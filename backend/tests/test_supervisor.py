"""Phase 1 harness #2/#9: the service supervisor keeps services alive across process loss, identifies processes only
by PID file (pid + kernel start time), stops them by PID only, never passes the model API key, and records every
action as structured JSON lines."""
import json
import os
import sys
import time
from pathlib import Path

import pytest
import yaml

from s2s.ops import supervisor as sv_mod
from s2s.ops.supervisor import Infra, load, proc_start_time


def _cfg(tmp: Path, env_dump: Path, require: Path) -> Path:
    code = f"import os,json,time; open({str(env_dump)!r},'w').write(json.dumps(dict(os.environ))); time.sleep(120)"
    cfg = {"infra": {"docker": True, "compose": ["postgres"]},
           "env": {"S2S_ARTIFACT_DIR": str(tmp), "S2S_ANTHROPIC_KEY": "from-config"},
           "strip_env": ["S2S_ANTHROPIC_KEY", "S2S_MODEL_PROVIDER"], "require_dirs": [str(require)],
           "services": [{"name": "svc", "argv": [sys.executable, "-c", code], "cwd": str(tmp), "needs_infra": True}]}
    p = tmp / "services.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p


class FakeInfra:
    def __init__(self, docker=True, pg=True):
        self.docker, self.pg, self.calls = docker, pg, []

    def make(self):
        return Infra(docker_up=lambda: self.docker, start_docker=lambda: self.calls.append("start_docker"),
                     compose_healthy=lambda s: self.pg, compose_up=lambda svcs: self.calls.append(("up", svcs)))


@pytest.fixture
def sup(tmp_path, monkeypatch):
    monkeypatch.setenv("S2S_ANTHROPIC_KEY", "secret-in-parent")
    fake = FakeInfra()
    s = load(_cfg(tmp_path, tmp_path / "env.json", tmp_path), run_dir=tmp_path / "run", infra=fake.make())
    s.fake, s.infra_wait_s = fake, 1
    yield s
    for svc in s.services:
        s.stop(svc.name, timeout_s=5)


def _wait(pred, t=10):
    end = time.monotonic() + t
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False


def test_start_is_idempotent_and_records_pid_and_start_time(sup):
    r = sup.start("svc")
    rec = json.loads(sup.pidfile("svc").read_text())
    assert r["status"] == "started" and rec["pid"] == r["pid"] and rec["start_time"] == proc_start_time(r["pid"])
    assert sup.start("svc") == {"service": "svc", "status": "running", "pid": r["pid"]}


def test_child_never_gets_the_model_api_key(sup, tmp_path):
    sup.start("svc")
    assert _wait(lambda: (tmp_path / "env.json").exists())
    env = json.loads((tmp_path / "env.json").read_text())
    assert "S2S_ANTHROPIC_KEY" not in env  # neither the parent's value nor the config's
    assert env["S2S_ARTIFACT_DIR"] == str(tmp_path)


def test_stop_by_pid_file(sup):
    pid = sup.start("svc")["pid"]
    r = sup.stop("svc")
    assert r["status"] == "stopped" and r["signal"] == "SIGTERM"
    assert proc_start_time(pid) is None and not sup.pidfile("svc").exists()


def test_a_reused_pid_is_never_treated_as_the_service(sup):
    """PID file pointing at another live process (this test) with a different start time: not ours, not signalled."""
    sup.run_dir.mkdir(parents=True, exist_ok=True)
    sup.pidfile("svc").write_text(json.dumps({"pid": os.getpid(), "pgid": os.getpgid(os.getpid()),
                                              "start_time": proc_start_time(os.getpid()) + 1}))
    assert sup.alive("svc") is None
    assert sup.stop("svc") == {"service": "svc", "status": "not running"}  # and we are still alive


def test_a_dead_service_is_restarted_and_the_restart_is_recorded(sup):
    pid = sup.start("svc")["pid"]
    os.kill(pid, 9)
    assert _wait(lambda: (sup._reap() or True) and sup.alive("svc") is None)
    out = sup.ensure_all()
    assert out["services"]["svc"] == "started" and sup.alive("svc")["pid"] != pid
    log = [json.loads(l) for l in (sup.log_dir / "supervisor.jsonl").read_text().splitlines()]
    assert [l["action"] for l in log if l["service"] == "svc"] == ["started", "started"]
    assert log[-1]["reason"] == "restart (process gone)"


def test_services_wait_for_infrastructure(sup):
    sup.fake.pg = False
    out = sup.ensure_all()
    assert out["infra_unhealthy"] == ["postgres"] and out["services"]["svc"].startswith("waiting")
    assert ("up", ["postgres"]) in sup.fake.calls and sup.alive("svc") is None


def test_docker_is_started_when_down(tmp_path):
    fake = FakeInfra(docker=False)
    calls = fake.calls

    def start():
        calls.append("start_docker")
        fake.docker = True
    s = load(_cfg(tmp_path, tmp_path / "e.json", tmp_path), run_dir=tmp_path / "run",
             infra=Infra(docker_up=lambda: fake.docker, start_docker=start, compose_healthy=lambda _: True,
                         compose_up=lambda _: None))
    assert s.ensure_infra(wait_s=2) == [] and calls == ["start_docker"]


def test_launch_refused_without_required_dirs(tmp_path):
    s = load(_cfg(tmp_path, tmp_path / "e.json", tmp_path / "missing"), run_dir=tmp_path / "run",
             infra=FakeInfra().make())
    with pytest.raises(RuntimeError, match="required directory missing"):
        s.start("svc")
    assert s.alive("svc") is None


def test_repo_config_strips_the_key_and_lists_core_services():
    s = load(infra=FakeInfra().make())
    assert {"S2S_ANTHROPIC_KEY", "S2S_MODEL_PROVIDER"} <= set(s.strip_env)
    assert {"orchestrator", "api"} <= {x.name for x in s.services if x.enabled}
