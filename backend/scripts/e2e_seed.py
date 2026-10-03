"""Seed data for the Live Office end-to-end tests. Uses the env written by e2e_stack.py.

    python backend/scripts/e2e_seed.py run [--to STAGE] [--hang] [--step-delay S]
        start a real dummy run (the e2e orchestrator executes it); prints {"run_id": ...}
    python backend/scripts/e2e_seed.py stall
        a running task whose last progress was 20 minutes ago; the real watchdog then flags it
        task.stalled (as it would for a hung agent); prints {"task_id": ..., "run_id": ...}
    python backend/scripts/e2e_seed.py usage
        a completed run with three usage_records of known cost; prints the seeded run total and
        the database total (what the finance tab must show, to the cent)
    python backend/scripts/e2e_seed.py status RUN_ID
        prints the run status
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load_env(path: str) -> None:
    for k, v in json.loads(Path(path).read_text()).items():
        if k.startswith("S2S_"):
            os.environ[k] = v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "stall", "usage", "status", "active"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--to")
    ap.add_argument("--hang", action="store_true")
    ap.add_argument("--step-delay", type=float, default=0.15)
    ap.add_argument("--env-file", default=str(BACKEND.parent / "web" / "test-results" / "e2e-env.json"))
    a = ap.parse_args()
    load_env(a.env_file)

    from sqlalchemy import func, select
    from s2s.db.models import Design, Project, Run, Task, UsageRecord
    from s2s.db.session import session
    from s2s.ids import new_id
    from s2s.orchestrator.engine import create_run

    def design(s, name="uart"):
        p = Project(id=new_id("prj"), name="e2e")
        s.add(p)
        s.flush()
        d = Design(id=new_id("des"), project_id=p.id, name=name, request_text=f"{name} (e2e test)")
        s.add(d)
        s.flush()
        return d

    out: dict
    with session() as s:
        if a.what == "run":
            dummy = {"step_delay_s": a.step_delay}
            if a.hang:
                dummy["hang"] = {"stage": "spec", "at_step": 2, "seconds": 7}
            run = create_run(s, design(s), to_stage=a.to, dummy=dummy)
            out = {"run_id": run.id}
        elif a.what == "stall":
            run = create_run(s, design(s, "stall_seed"), from_stage="verification", to_stage="verification")
            t = s.scalar(select(Task).where(Task.run_id == run.id))
            ago = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=20)
            t.status, t.lease_owner, t.attempts = "running", "e2e-seed", 1
            t.started_at = t.assigned_at = t.last_progress_at = ago
            t.evidence_signal, t.percent = "regression attempt 2: 41/42 pass", 0.4
            run.status, run.current_stage = "running", "verification"
            out = {"task_id": t.id, "run_id": run.id}
        elif a.what == "usage":
            d = design(s, "finance_seed")
            run = Run(id=new_id("run"), design_id=d.id, status="completed", stages=[], agent_kind="dummy")
            s.add(run)
            s.flush()
            costs = [Decimal("12.34"), Decimal("5.67"), Decimal("0.99")]
            for i, c in enumerate(costs):
                s.add(UsageRecord(id=new_id("use"), task_id=None, agent_id="Meter", source=["llm", "compute", "storage"][i],
                                  quantity=1, unit="seed", unit_cost=c, cost_usd=c, run_id=run.id,
                                  model="dummy-model" if i == 0 else None, detail={"seed": True}))
            s.flush()
            total = s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0)))
            out = {"run_id": run.id, "seeded_usd": str(sum(costs)), "db_total_usd": str(total),
                   "records": s.scalar(select(func.count()).select_from(UsageRecord))}
        elif a.what == "status":
            out = {"status": s.get(Run, a.arg).status}
        else:
            out = {"active": s.scalar(select(func.count()).select_from(Run).where(
                Run.status.in_(("pending", "running")), Run.id.not_in(
                    select(Task.run_id).where(Task.lease_owner == "e2e-seed"))))}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
