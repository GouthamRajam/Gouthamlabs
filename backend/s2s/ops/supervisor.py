"""Service supervisor (Phase 1 harness #2 and #9).

Keeps the long-lived S2S services of config/services.yaml alive: infrastructure first (dockerd, then the compose
services Postgres and Redis), then the processes (orchestrator, api, ...). A container restart used to lose every
process and the operator rebuilt them by hand; `python -m s2s.ops.supervisor up` now brings everything back and
keeps it up.

Processes are identified ONLY by PID files (var/run/<name>.pid holding pid, process-group id and the kernel start
time of the process). A process is "ours" only if /proc/<pid> exists AND its start time matches the file, so a
reused PID is never mistaken for a service. Stopping signals that process group and nothing else, never a process
found by matching command lines (2026-10-07: a command-line pattern kill matched the operator's own shell).

Every action is appended to var/log/supervisor.jsonl (one JSON object per line) so restarts are part of the run
record. Child environments never carry the model API key (strip_env).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

REPO = Path(__file__).resolve().parents[3]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def proc_start_time(pid: int) -> int | None:
    """Kernel start time (clock ticks since boot, /proc/<pid>/stat field 22) or None if the PID does not exist."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    return int(stat.rsplit(")", 1)[1].split()[19])  # fields after "comm)": state is field 3 -> index 0


@dataclass
class Service:
    name: str
    argv: list[str]
    cwd: Path
    enabled: bool = True
    needs_infra: bool = False


@dataclass
class Infra:
    """Infrastructure probes and starters; replaceable in tests."""
    docker_up: Callable[[], bool]
    start_docker: Callable[[], None]
    compose_healthy: Callable[[str], bool]
    compose_up: Callable[[list[str]], None]


def _sh_ok(cmd: list[str], timeout: float = 20) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def real_infra(repo: Path, log_dir: Path) -> Infra:
    def start_docker() -> None:
        for stale in (Path("/var/run/docker.pid"), Path("/var/run/docker/containerd/containerd.pid")):
            stale.unlink(missing_ok=True)  # left behind by a container restart; dockerd refuses to start
        with open(log_dir / "dockerd.log", "ab") as out:
            subprocess.Popen(["dockerd"], stdout=out, stderr=subprocess.STDOUT, start_new_session=True)

    def compose_healthy(svc: str) -> bool:
        probe = {"postgres": ["pg_isready", "-U", "s2s"], "redis": ["redis-cli", "ping"]}.get(svc)
        if probe is None:
            return _sh_ok(["docker", "compose", "--project-directory", str(repo), "ps", "--status", "running", "-q", svc])
        return _sh_ok(["docker", "compose", "--project-directory", str(repo), "exec", "-T", svc, *probe])

    return Infra(
        docker_up=lambda: _sh_ok(["docker", "info"]),
        start_docker=start_docker,
        compose_healthy=compose_healthy,
        compose_up=lambda svcs: subprocess.run(["docker", "compose", "--project-directory", str(repo), "up", "-d",
                                                *svcs], capture_output=True, timeout=300),
    )


@dataclass
class Supervisor:
    repo: Path
    services: list[Service]
    env: dict[str, str]
    strip_env: list[str]
    require_dirs: list[Path]
    infra_cfg: dict
    infra: Infra
    run_dir: Path
    log_dir: Path
    infra_wait_s: float = 120  # how long one pass waits for dockerd / compose services to become healthy
    backoff: dict[str, float] = field(default_factory=dict)
    next_try: dict[str, float] = field(default_factory=dict)

    # --- record -------------------------------------------------------------------------------
    def record(self, action: str, service: str, **kw) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with open(self.log_dir / "supervisor.jsonl", "a") as f:
            f.write(json.dumps({"ts": _now(), "action": action, "service": service, **kw}) + "\n")

    # --- PID files ----------------------------------------------------------------------------
    def pidfile(self, name: str) -> Path:
        return self.run_dir / f"{name}.pid"

    def read_pid(self, name: str) -> dict | None:
        try:
            return json.loads(self.pidfile(name).read_text())
        except (OSError, ValueError):
            return None

    def alive(self, name: str) -> dict | None:
        """The service's PID record if that exact process (pid + start time) is still running."""
        rec = self.read_pid(name)
        if not rec:
            return None
        st = proc_start_time(rec["pid"])
        if st is None or st != rec["start_time"]:
            return None
        try:  # a zombie (exited, not yet reaped by its parent) is not alive
            if Path(f"/proc/{rec['pid']}/stat").read_text().rsplit(")", 1)[1].split()[0] == "Z":
                return None
        except OSError:
            return None
        return rec

    # --- environment --------------------------------------------------------------------------
    def child_env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in self.strip_env}
        env.update(self.env)
        for k in self.strip_env:  # never passed, even if the config tried to
            env.pop(k, None)
        return env

    def check_launch_env(self) -> list[str]:
        return [f"required directory missing: {d}" for d in self.require_dirs if not d.is_dir()]

    # --- processes ----------------------------------------------------------------------------
    def service(self, name: str) -> Service:
        for s in self.services:
            if s.name == name:
                return s
        raise KeyError(f"unknown service {name!r} (config/services.yaml)")

    def start(self, name: str, reason: str = "start") -> dict:
        if rec := self.alive(name):
            return {"service": name, "status": "running", "pid": rec["pid"]}
        problems = self.check_launch_env()
        if problems:
            self.record("refused", name, problems=problems)
            raise RuntimeError(f"{name}: launch environment invalid: {problems}")
        svc = self.service(name)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with open(self.log_dir / f"{name}.log", "ab") as out:
            p = subprocess.Popen(svc.argv, cwd=svc.cwd, env=self.child_env(), stdout=out, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, start_new_session=True)
        rec = {"pid": p.pid, "pgid": p.pid, "start_time": proc_start_time(p.pid), "argv": svc.argv,
               "started_at": _now()}
        self.pidfile(name).write_text(json.dumps(rec) + "\n")
        self.record("started", name, pid=p.pid, reason=reason)
        return {"service": name, "status": "started", "pid": p.pid}

    def stop(self, name: str, timeout_s: float = 20) -> dict:
        """Stop by PID file only: SIGTERM the recorded process group, SIGKILL it after `timeout_s`."""
        rec = self.alive(name)
        if rec is None:
            self.pidfile(name).unlink(missing_ok=True)
            return {"service": name, "status": "not running"}
        os.killpg(rec["pgid"], signal.SIGTERM)
        end = time.monotonic() + timeout_s
        while time.monotonic() < end and self.alive(name):
            self._reap()
            time.sleep(0.1)
        if self.alive(name):
            os.killpg(rec["pgid"], signal.SIGKILL)
            sig = "SIGKILL"
        else:
            sig = "SIGTERM"
        self._reap()  # if we are its parent, collect it (a zombie is already "not alive" but still in /proc)
        self.pidfile(name).unlink(missing_ok=True)
        self.record("stopped", name, pid=rec["pid"], signal=sig)
        return {"service": name, "status": "stopped", "pid": rec["pid"], "signal": sig}

    @staticmethod
    def _reap() -> None:
        try:  # children started by this process: collect exit status so they do not stay zombies
            while os.waitpid(-1, os.WNOHANG)[0]:
                pass
        except ChildProcessError:
            pass

    # --- infrastructure -----------------------------------------------------------------------
    def ensure_infra(self, wait_s: float | None = None) -> list[str]:
        """Bring up dockerd and the compose services; returns what is still unhealthy."""
        wait_s = self.infra_wait_s if wait_s is None else wait_s
        bad: list[str] = []
        if self.infra_cfg.get("docker"):
            if not self.infra.docker_up():
                self.record("starting", "dockerd", reason="docker info failed")
                self.infra.start_docker()
                end = time.monotonic() + wait_s
                while time.monotonic() < end and not self.infra.docker_up():
                    time.sleep(1)
                if not self.infra.docker_up():
                    self.record("unhealthy", "dockerd")
                    return ["dockerd"]
                self.record("healthy", "dockerd")
        svcs = list(self.infra_cfg.get("compose") or [])
        down = [s for s in svcs if not self.infra.compose_healthy(s)]
        if down:
            self.record("starting", "compose", services=down)
            self.infra.compose_up(down)
            end = time.monotonic() + wait_s
            while time.monotonic() < end and any(not self.infra.compose_healthy(s) for s in down):
                time.sleep(1)
            bad = [s for s in down if not self.infra.compose_healthy(s)]
            for s in down:
                self.record("unhealthy" if s in bad else "healthy", s)
        return bad

    def ensure_all(self) -> dict:
        """One supervision pass: infrastructure, then every enabled service (restart with backoff)."""
        out = {"infra_unhealthy": self.ensure_infra(), "services": {}}
        now = time.monotonic()
        for svc in self.services:
            if not svc.enabled:
                continue
            if self.alive(svc.name):
                out["services"][svc.name] = "running"
                continue
            if svc.needs_infra and out["infra_unhealthy"]:
                out["services"][svc.name] = f"waiting for {out['infra_unhealthy']}"
                continue
            if now < self.next_try.get(svc.name, 0):
                out["services"][svc.name] = "backoff"
                continue
            was = self.read_pid(svc.name)
            r = self.start(svc.name, reason="restart (process gone)" if was else "start")
            delay = self.backoff[svc.name] = min(2 * self.backoff.get(svc.name, 2.5), 300) if was else 5
            self.next_try[svc.name] = now + delay
            out["services"][svc.name] = r["status"]
        return out

    def status(self) -> dict:
        return {s.name: ({"pid": r["pid"], "since": r["started_at"]} if (r := self.alive(s.name)) else
                         ("disabled" if not s.enabled else "not running")) for s in self.services}


def load(config: Path | None = None, run_dir: Path | None = None, infra: Infra | None = None) -> Supervisor:
    cfg = yaml.safe_load((config or REPO / "config" / "services.yaml").read_text())
    subs = {"{repo}": str(REPO), "{python}": sys.executable, "{bin}": str(Path(sys.executable).parent)}

    def sub(s: str) -> str:
        for k, v in subs.items():
            s = s.replace(k, v)
        return s

    services = [Service(name=s["name"], argv=[sub(a) for a in s["argv"]], cwd=Path(sub(s.get("cwd", "{repo}"))),
                        enabled=s.get("enabled", True), needs_infra=s.get("needs_infra", False))
                for s in cfg.get("services", [])]
    run_dir = run_dir or REPO / "var" / "run"
    log_dir = run_dir.parent / "log"
    return Supervisor(repo=REPO, services=services, env={k: sub(str(v)) for k, v in (cfg.get("env") or {}).items()},
                      strip_env=list(cfg.get("strip_env") or []),
                      require_dirs=[Path(sub(d)) for d in cfg.get("require_dirs") or []],
                      infra_cfg=cfg.get("infra") or {}, infra=infra or real_infra(REPO, log_dir),
                      run_dir=run_dir, log_dir=log_dir)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.ops.supervisor", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("up", help="bring infra + services up, then keep them up in a detached supervisor loop")
    sub.add_parser("down", help="stop the supervisor loop, then every service (by PID file)")
    sub.add_parser("status")
    run = sub.add_parser("run", help="supervision loop in the foreground")
    run.add_argument("--interval", type=float, default=10)
    for c in ("start", "stop"):
        p = sub.add_parser(c)
        p.add_argument("names", nargs="+")
    a = ap.parse_args(argv)
    sv = load()
    if a.cmd == "status":
        print(json.dumps({"supervisor": "running" if _loop_alive(sv) else "not running", **sv.status()}, indent=1))
    elif a.cmd == "start":
        for n in a.names:
            print(json.dumps(sv.start(n)))
    elif a.cmd == "stop":
        for n in a.names:
            print(json.dumps(sv.stop(n)))
    elif a.cmd == "run":
        _write_loop_pid(sv)
        sv.record("loop started", "supervisor", pid=os.getpid())
        while True:
            sv.ensure_all()
            sv._reap()
            time.sleep(a.interval)
    elif a.cmd == "up":
        print(json.dumps(sv.ensure_all(), indent=1))
        if not _loop_alive(sv):
            sv.log_dir.mkdir(parents=True, exist_ok=True)
            with open(sv.log_dir / "supervisor.log", "ab") as out:
                subprocess.Popen([sys.executable, "-m", "s2s.ops.supervisor", "run"], cwd=REPO / "backend",
                                 env={**sv.child_env(), "PYTHONPATH": str(REPO / "backend")}, stdout=out,
                                 stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            print("supervisor loop started")
    elif a.cmd == "down":
        rec = _loop_alive(sv)
        if rec:
            os.killpg(rec["pgid"], signal.SIGTERM)
            sv.pidfile("supervisor").unlink(missing_ok=True)
            sv.record("stopped", "supervisor", pid=rec["pid"])
        for s in reversed(sv.services):
            print(json.dumps(sv.stop(s.name)))
    return 0


def _write_loop_pid(sv: Supervisor) -> None:
    sv.run_dir.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    sv.pidfile("supervisor").write_text(json.dumps({"pid": pid, "pgid": os.getpgid(pid),
                                                    "start_time": proc_start_time(pid), "started_at": _now()}) + "\n")


def _loop_alive(sv: Supervisor) -> dict | None:
    return sv.alive("supervisor")


if __name__ == "__main__":
    sys.exit(main())
