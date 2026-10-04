"""Runs EDA commands inside the s2s-eda image and records what was run (Part 7.5 rules 3-4).

Two modes (env S2S_EDA_MODE):
  docker (default)  `docker run --rm --network none` the s2s-eda image, mounting the task's
                    working directory at the same absolute path, so paths are identical
                    inside and outside the container.
  local             already running inside s2s-eda: run the command directly.

Every input file must live inside the working directory (it is the only thing mounted).

Concurrency: every run first takes slots from one machine-wide pool (S2S_TOOL_SLOTS, default the CPU
count; OpenLane takes 2 because it runs steps on several threads). Slots are flock'ed files in
S2S_LOCK_DIR, so they are shared by every process and thread of every design run. A job waits for its
slots BEFORE its timeout starts: queueing never makes a tool run time out.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import shlex
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
IMAGE = os.environ.get("S2S_EDA_IMAGE", "s2s-eda")
DEFAULT_TIMEOUT_S = 1800


class EdaUnavailable(RuntimeError):
    """The s2s-eda environment cannot be used (no docker, no image, ...)."""


@dataclass
class RunRecord:
    command: list[str]
    exit_code: int | None
    timed_out: bool
    duration_s: float
    log_path: Path
    tool_version: str | None
    env_hash: str
    mode: str


HEAVY_WEIGHT = {"openlane": 2}  # slots per run; every other tool takes 1


def tool_slots() -> int:
    return max(1, int(os.environ.get("S2S_TOOL_SLOTS", str(os.cpu_count() or 4))))


def lock_dir() -> Path:
    return Path(os.environ.get("S2S_LOCK_DIR", REPO_ROOT / "var" / "locks"))


@contextlib.contextmanager
def tool_slots_held(version_key: str):
    """Hold `HEAVY_WEIGHT[version_key]` (default 1) of the machine-wide slots for one tool run.
    Slots are taken under one acquisition lock, so two multi-slot jobs never each hold a part and wait
    for each other. flock (not fcntl record locks) so threads of one process also exclude each other."""
    total = tool_slots()
    need = min(HEAVY_WEIGHT.get(version_key, 1), total)
    d = lock_dir()
    d.mkdir(parents=True, exist_ok=True)
    held: list = []
    try:
        with open(d / "acquire.lock", "a") as acq:
            fcntl.flock(acq, fcntl.LOCK_EX)
            try:
                while len(held) < need:
                    for i in range(total):
                        if len(held) == need:
                            break
                        f = open(d / f"slot_{i}.lock", "a")
                        try:
                            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            held.append(f)
                        except BlockingIOError:
                            f.close()
                    if len(held) < need:
                        time.sleep(0.5)
            finally:
                fcntl.flock(acq, fcntl.LOCK_UN)
        yield len(held)
    finally:
        for f in held:
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()


def mode() -> str:
    return os.environ.get("S2S_EDA_MODE", "docker")


def versions_lock_path() -> Path:
    if "S2S_VERSIONS_LOCK" in os.environ:
        return Path(os.environ["S2S_VERSIONS_LOCK"])
    in_image = Path("/opt/s2s/eda/versions.lock")
    if mode() == "local" and in_image.exists():
        return in_image
    return REPO_ROOT / "eda" / "versions.lock"


@lru_cache(maxsize=1)
def _lock() -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in versions_lock_path().read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            pins[key] = value
    return pins


def pinned_version(key: str) -> str | None:
    return _lock().get(key)


@lru_cache(maxsize=1)
def image_id() -> str:
    if mode() == "local":
        return os.environ.get("S2S_EDA_IMAGE_ID", "local")
    if shutil.which("docker") is None:
        raise EdaUnavailable("docker is not installed")
    proc = subprocess.run(
        ["docker", "image", "inspect", "-f", "{{.Id}}", IMAGE], capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise EdaUnavailable(f"image {IMAGE!r} not available: {proc.stderr.strip()}")
    return proc.stdout.strip()


def env_hash() -> str:
    """Identifies the exact tool environment: image id + the versions.lock it was built from."""
    h = hashlib.sha256()
    h.update(image_id().encode())
    h.update(versions_lock_path().read_bytes())
    return "sha256:" + h.hexdigest()


def run(
    command: list[str],
    workdir: Path,
    log_path: Path,
    version_key: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> RunRecord:
    """Run `command` in s2s-eda; stdout+stderr go to `log_path`. Never raises on tool failure."""
    workdir = workdir.resolve()
    cwd = (cwd or workdir).resolve()
    if workdir != cwd and workdir not in cwd.parents:
        raise ValueError(f"cwd {cwd} must be inside workdir {workdir}")
    log_path = log_path.resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = env or {}

    container = f"s2s-{uuid.uuid4().hex[:12]}"
    if mode() == "local":
        full = command
        proc_env = {**os.environ, **env}
    else:
        image_id()  # raises EdaUnavailable early with a clear message
        full = ["docker", "run", "--rm", "--name", container, "--network", "none",
                "-v", f"{workdir}:{workdir}", "-w", str(cwd)]
        for key, value in env.items():
            full += ["-e", f"{key}={value}"]
        full += [IMAGE, *command]
        proc_env = None

    with tool_slots_held(version_key):  # waits for a free slot; the timeout starts after this
        start = time.monotonic()
        timed_out = False
        with open(log_path, "wb") as log:
            proc = subprocess.Popen(full, stdout=log, stderr=subprocess.STDOUT, cwd=cwd, env=proc_env,
                                    start_new_session=True)
            try:
                exit_code: int | None = proc.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                if mode() == "local":
                    os.killpg(proc.pid, 9)
                else:
                    subprocess.run(["docker", "kill", container], capture_output=True)
                proc.wait()
                exit_code = None
        with open(log_path, "a") as log:
            if timed_out:
                log.write(f"\n[s2s] TIMEOUT after {timeout_s}s; process killed\n")

    return RunRecord(
        command=command,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_s=round(time.monotonic() - start, 3),
        log_path=log_path,
        tool_version=pinned_version(version_key),
        env_hash=env_hash(),
        mode=mode(),
    )


def command_str(command: list[str]) -> str:
    return " ".join(shlex.quote(c) for c in command)
