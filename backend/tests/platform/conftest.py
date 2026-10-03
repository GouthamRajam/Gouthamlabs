"""Fixtures for the M0.3 platform tests: a fresh Postgres database and Redis stream per test,
fast-SLA config overrides, and real orchestrator / API subprocesses.

Needs Postgres + Redis (`docker compose up -d`). Without them the tests are skipped, unless
S2S_REQUIRE_PLATFORM=1 (set in CI), which turns a missing service into a failure.
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine, text

BACKEND = Path(__file__).resolve().parents[2]
REPO = BACKEND.parent
ADMIN_URL = os.environ.get("S2S_TEST_ADMIN_URL", "postgresql+psycopg://s2s:s2s@localhost:5432/postgres")
DB_TEMPLATE = "postgresql+psycopg://s2s:s2s@localhost:5432/{name}"

# Fast SLAs for tests (minutes, as in management.yaml): a 3 s stall threshold instead of 15 min.
FAST_SLA = {
    "assign_ready_task_minutes": 2,
    "heartbeat_minutes": 0.05,
    "manager_checkin_minutes": 0.02,
    "stall_minutes": 0.05,
    "stall_multiplier_of_expected_step": 2,
    "default_expected_step_minutes": 0.05,
    "escalate_to_human_after_minutes": 0.05,
}


def _reachable(host: str, port: int) -> bool:
    try:
        socket.create_connection((host, port), timeout=1).close()
        return True
    except OSError:
        return False


@pytest.fixture(scope="session", autouse=True)
def services_available():
    if _reachable("localhost", 5432) and _reachable("localhost", 6379):
        return
    msg = "Postgres/Redis not reachable on localhost (run `docker compose up -d`)"
    if os.environ.get("S2S_REQUIRE_PLATFORM") == "1":
        pytest.fail(msg)
    pytest.skip(msg, allow_module_level=True)


def _reset_caches() -> None:
    from s2s import config, org
    from s2s.db import session
    from s2s.events import bus
    config.clear_caches()
    org.load_org.cache_clear()
    session.engine.cache_clear()
    bus.redis_client.cache_clear()


@pytest.fixture
def platform(tmp_path, monkeypatch):
    """A fresh migrated database + Redis stream + fast-SLA config, wired into the env."""
    name = f"s2s_t_{uuid.uuid4().hex[:10]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'create database "{name}"'))
    url = DB_TEMPLATE.format(name=name)

    mgmt = yaml.safe_load((REPO / "config" / "management.yaml").read_text())
    mgmt["sla"] = dict(FAST_SLA)
    mgmt_path = tmp_path / "management.yaml"
    mgmt_path.write_text(yaml.safe_dump(mgmt))
    env = {
        "S2S_DATABASE_URL": url,
        "S2S_EVENT_STREAM": f"s2s:test:{name}",
        "S2S_MANAGEMENT_CONFIG": str(mgmt_path),
        "S2S_ARTIFACT_DIR": str(tmp_path / "artifacts"),
        "S2S_DUMMY_MODEL_CALL_LOG": str(tmp_path / "model_calls.jsonl"),
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    _reset_caches()

    from alembic import command
    from alembic.config import Config
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")

    ctx = Platform(url, env, tmp_path, mgmt_path, monkeypatch)
    yield ctx
    ctx.stop_all()
    _reset_caches()
    from s2s.events.bus import redis_client
    try:
        redis_client().delete(env["S2S_EVENT_STREAM"])
    except Exception:
        pass
    with admin.connect() as c:
        c.execute(text(f'drop database if exists "{name}" with (force)'))
    admin.dispose()


class Platform:
    def __init__(self, url: str, env: dict, tmp: Path, mgmt_path: Path, monkeypatch):
        self.url, self.env, self.tmp, self.mgmt_path = url, env, tmp, mgmt_path
        self._mp = monkeypatch  # env changes are undone after the test
        self.procs: list[subprocess.Popen] = []

    def set_config(self, name: str, data: dict) -> None:
        """Override a config file (budgets/finance/management) for this test's processes."""
        path = self.tmp / f"{name}.yaml"
        path.write_text(yaml.safe_dump(data))
        key = {"budgets": "S2S_BUDGETS_CONFIG", "finance": "S2S_FINANCE_CONFIG",
               "management": "S2S_MANAGEMENT_CONFIG"}[name]
        self.env[key] = str(path)
        self._mp.setenv(key, str(path))
        _reset_caches()

    def _spawn(self, args: list[str], log: str) -> subprocess.Popen:
        out = open(self.tmp / log, "ab")
        p = subprocess.Popen([sys.executable, *args], cwd=BACKEND, env={**os.environ, **self.env},
                             stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        self.procs.append(p)
        return p

    def start_orchestrator(self, log: str = "orchestrator.log") -> subprocess.Popen:
        return self._spawn(["-m", "s2s.orchestrator", "--poll", "0.05"], log)

    def start_api(self) -> tuple[subprocess.Popen, int]:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        p = self._spawn(["-m", "uvicorn", "s2s.api.app:app", "--port", str(port), "--log-level",
                         "warning"], "api.log")
        import httpx
        for _ in range(100):
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health", timeout=0.5).status_code == 200:
                    return p, port
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        raise RuntimeError(f"API did not start; see {self.tmp / 'api.log'}")

    @staticmethod
    def kill(p: subprocess.Popen) -> None:
        """SIGKILL: no cleanup, no chance to finish the current step."""
        os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=10)

    def log(self, name: str) -> str:
        path = self.tmp / name
        return path.read_text(errors="replace") if path.exists() else ""

    def stop_all(self) -> None:
        for p in self.procs:
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                    p.wait(timeout=10)
                except Exception:
                    os.killpg(p.pid, signal.SIGKILL)


# --- helpers ------------------------------------------------------------------------------------
def new_design(s, name: str = "counter8"):
    from s2s.db.models import Design, Project
    from s2s.ids import new_id
    p = Project(id=new_id("prj"), name="test")
    s.add(p)
    s.flush()
    d = Design(id=new_id("des"), project_id=p.id, name=name, request_text=f"{name} for tests")
    s.add(d)
    s.flush()
    return d


def wait_for(cond, timeout: float, every: float = 0.05, what: str = "condition"):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        v = cond()
        if v:
            return v
        time.sleep(every)
    raise AssertionError(f"timed out after {timeout}s waiting for {what}")
