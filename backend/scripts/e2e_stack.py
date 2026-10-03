"""Backend stack for the Live Office end-to-end tests (web/tests, Playwright).

Creates a fresh database (Postgres from `docker compose up`), migrates it, writes test
configs (fast SLAs: 3 s stall threshold; small budgets so budget warnings/alerts happen
within one dummy run), and runs a real API + orchestrator against it. Stays in the
foreground; on SIGTERM/SIGINT it stops both and drops the database.

    python backend/scripts/e2e_stack.py --port 8100 --env-file web/test-results/e2e-env.json
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

import yaml
from sqlalchemy import create_engine, text

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
ADMIN_URL = os.environ.get("S2S_TEST_ADMIN_URL", "postgresql+psycopg://s2s:s2s@localhost:5432/postgres")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--env-file", default=str(REPO / "web" / "test-results" / "e2e-env.json"))
    args = ap.parse_args()

    name = f"s2s_e2e_{uuid.uuid4().hex[:8]}"
    work = Path(f"/tmp/{name}")
    work.mkdir(parents=True)
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'create database "{name}"'))
    url = ADMIN_URL.rsplit("/", 1)[0] + f"/{name}"

    mgmt = yaml.safe_load((REPO / "config" / "management.yaml").read_text())
    mgmt["sla"] = {"assign_ready_task_minutes": 2, "heartbeat_minutes": 0.05, "manager_checkin_minutes": 0.02,
                   "stall_minutes": 0.05, "stall_multiplier_of_expected_step": 2,
                   "default_expected_step_minutes": 0.05, "escalate_to_human_after_minutes": 0.05}
    budgets = yaml.safe_load((REPO / "config" / "budgets.yaml").read_text())
    budgets["per_agent"]["Rex"] = {"max_tool_runs": 6}  # verification uses 5: warning at 83%
    budgets["per_run"]["max_cost_usd"] = 0.01           # a dummy run (~$0.014) crosses 80% and 100%
    (work / "management.yaml").write_text(yaml.safe_dump(mgmt))
    (work / "budgets.yaml").write_text(yaml.safe_dump(budgets))
    env = {
        **os.environ, "S2S_DATABASE_URL": url, "S2S_EVENT_STREAM": f"s2s:{name}",
        "S2S_MANAGEMENT_CONFIG": str(work / "management.yaml"), "S2S_BUDGETS_CONFIG": str(work / "budgets.yaml"),
        "S2S_ARTIFACT_DIR": str(work / "artifacts"), "PYTHONPATH": str(BACKEND),
        "S2S_CORS_ORIGINS": "http://localhost:3100,http://127.0.0.1:3100",  # the test web server
    }
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True,
                   capture_output=True)
    procs = [
        subprocess.Popen([sys.executable, "-m", "uvicorn", "s2s.api.app:app", "--host", "127.0.0.1", "--port",
                          str(args.port), "--log-level", "warning", "--timeout-keep-alive", "75"], cwd=BACKEND, env=env),
        subprocess.Popen([sys.executable, "-m", "s2s.orchestrator", "--poll", "0.05"], cwd=BACKEND, env=env,
                         stdout=open(work / "orchestrator.log", "w"), stderr=subprocess.STDOUT),
    ]
    env_file = Path(args.env_file)
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(json.dumps({k: env[k] for k in (
        "S2S_DATABASE_URL", "S2S_EVENT_STREAM", "S2S_MANAGEMENT_CONFIG", "S2S_BUDGETS_CONFIG", "S2S_ARTIFACT_DIR")}
        | {"api": f"http://127.0.0.1:{args.port}", "work": str(work)}, indent=2))

    stopping = False

    def stop(*_: object) -> None:
        nonlocal stopping
        if stopping:
            return
        stopping = True
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        with admin.connect() as c:
            c.execute(text(f'drop database if exists "{name}" with (force)'))
        print(f"e2e stack: stopped, dropped {name}", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{args.port}/health", timeout=1)
            break
        except OSError:
            time.sleep(0.2)
    print(f"e2e stack: db {name}, api :{args.port}, env {env_file}", flush=True)
    while True:
        for p in procs:
            if p.poll() is not None:
                print(f"e2e stack: child {p.args[2]} exited {p.returncode}", flush=True)
                stop()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
