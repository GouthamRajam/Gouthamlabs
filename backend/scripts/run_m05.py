"""M0.5 real run: one design from its plain-English request through spec, architecture and RTL
with the real model (Settings -> Model access) and the real EDA tools (s2s-eda).

    cd backend && python scripts/run_m05.py counter8

Runs a real orchestrator process against the main database, so the run is live in the Live Office
(http://localhost:3000) and the API. Prints every event the agents emitted, every check, and the
metered spend. Stops when the run completes or fails, or a task pauses (spend cap, needs a human).
Never prints the API key: only whether one is saved.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
os.environ.setdefault("S2S_SECRETS_DIR", str(REPO / "var" / "secrets"))
os.environ.setdefault("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))
sys.path.insert(0, str(BACKEND))

from sqlalchemy import func, select  # noqa: E402

from s2s.config import spend_caps  # noqa: E402
from s2s.db.models import Check, Design, Event, Project, Run, Task, UsageRecord  # noqa: E402
from s2s.db.session import session  # noqa: E402
from s2s.finance.meter import spend_so_far  # noqa: E402
from s2s.ids import new_id  # noqa: E402
from s2s.models import access  # noqa: E402
from s2s.models.gateway import ModelGateway  # noqa: E402
from s2s.orchestrator.engine import create_run  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("design", choices=["counter8", "uart", "sync_fifo", "alu8", "spi_master"])
    p.add_argument("--timeout-min", type=float, default=45)
    args = p.parse_args()

    view = access.public_view()
    gw = type(ModelGateway.from_settings().provider).__name__
    print(f"model calls: {gw} (config/finance.yaml model_provider); Settings: provider={view['provider']} "
          f"model={view['model']} key_saved={view['key_set']}")
    if not view["key_set"]:
        print("no API key saved in Settings -> Model access")
        return 2
    caps = spend_caps()
    with session() as s:
        today = spend_so_far(s)["today_usd"]
    print(f"spend caps: per design ${caps['per_design_usd']:.2f}, daily ${caps['daily_usd']:.2f}; "
          f"spent today before this run: ${today:.4f}")

    request = (REPO / "designs" / args.design / "request.md").read_text()
    with session() as s:
        prj = Project(id=new_id("prj"), name="M0.5")
        s.add(prj)
        s.flush()
        d = Design(id=new_id("des"), project_id=prj.id, name=args.design, request_text=request)
        s.add(d)
        s.flush()
        run_id = create_run(s, d, to_stage="rtl", agent_kind="s2s").id
    print(f"design {args.design}: run {run_id} (spec -> architecture -> rtl)\n")

    logs = REPO / "var" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = open(logs / f"orchestrator_{run_id}.log", "ab")
    orc = subprocess.Popen([sys.executable, "-m", "s2s.orchestrator", "--poll", "0.2"], cwd=BACKEND,
                           env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    seen, t0 = 0, time.monotonic()
    try:
        while True:
            with session() as s:
                evs = s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()
                for e in evs[seen:]:
                    print(_fmt(e), flush=True)
                seen = len(evs)
                run = s.get(Run, run_id)
                tasks = s.scalars(select(Task).where(Task.run_id == run_id)).all()
                stopped = [t for t in tasks if t.status in ("paused", "failed")]
            if run.status in ("completed", "failed") or stopped:
                break
            if time.monotonic() - t0 > args.timeout_min * 60:
                print("TIMEOUT waiting for the run")
                break
            time.sleep(1.0)
        time.sleep(1.5)  # last events of the final transaction
        with session() as s:
            for e in s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()[seen:]:
                print(_fmt(e))
    finally:
        os.killpg(orc.pid, signal.SIGTERM)
        orc.wait(timeout=30)
    return report(run_id, time.monotonic() - t0)


def _fmt(e: Event) -> str:
    to = f" -> {e.to_agent_id}" if e.to_agent_id else ""
    return f"{e.ts:%H:%M:%S.%f}"[:-3] + f"  {e.type:<15} {(e.agent_id or '-'):<9}{to:<12} {e.summary}"


def report(run_id: str, wall_s: float) -> int:
    with session() as s:
        run = s.get(Run, run_id)
        tasks = s.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.seq)).all()
        print(f"\n=== run {run_id}: {run.status} in {wall_s / 60:.1f} min ===")
        for t in tasks:
            print(f"  {t.stage:<13} {t.agent_id:<7} {t.status}")
        print("\n=== checks (Trust Layer records) ===")
        for t in tasks:
            for c in s.scalars(select(Check).where(Check.task_id == t.id).order_by(Check.id)):
                m = {k: v for k, v in (c.metrics or {}).items() if k != "detail"}
                print(f"  {t.stage:<13} {c.check_name:<24} {'PASS' if c.passed else 'FAIL'}  {c.tool}  {m}")
                if not c.passed and (c.metrics or {}).get("detail"):
                    for line in c.metrics["detail"][:5]:
                        print(f"      - {line}")
        rows = s.execute(select(UsageRecord.agent_id, UsageRecord.source, func.count(),
                                func.sum(UsageRecord.quantity), func.sum(UsageRecord.cost_usd))
                         .where(UsageRecord.run_id == run_id).group_by(UsageRecord.agent_id, UsageRecord.source)
                         .order_by(func.sum(UsageRecord.cost_usd).desc())).all()
        print("\n=== metered spend (usage_records) ===")
        total = Decimal(0)
        for agent, source, n, qty, cost in rows:
            unit = "tokens" if source == "llm" else "cpu-s"
            print(f"  {agent:<9} {source:<8} {n:>3} record(s) {float(qty):>10.1f} {unit:<7} ${Decimal(cost):.6f}")
            total += Decimal(cost)
        n_events = s.scalar(select(func.count()).select_from(Event).where(Event.run_id == run_id))
        print(f"  TOTAL for this run: ${total:.6f}   ({n_events} events)")
        print(f"  spent today (all work): ${spend_so_far(s)['today_usd']:.4f}")
    return 0 if run.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
