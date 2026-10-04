"""M0.6 real run: verification (Zones 2B + 2C) of a design whose M0.5 run produced spec, arch and RTL.

    cd backend && python scripts/run_m06.py <m05_run_id>

The new run belongs to the SAME design as the M0.5 run, so the per-design spend cap and the
reported cost per design cover both milestones. Real model (Settings -> Model access), real tools
(s2s-eda). Prints a summary of the agents' events (all of them go to a log file), the checks, the
verification report and the metered spend. Never prints the API key.
"""
from __future__ import annotations

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

from s2s.agents.runtime import artifact_dir  # noqa: E402
from s2s.config import spend_caps  # noqa: E402
from s2s.db.models import Check, Design, Event, Run, Task, UsageRecord  # noqa: E402
from s2s.db.session import session  # noqa: E402
from s2s.finance.meter import spend_so_far  # noqa: E402
from s2s.models import access  # noqa: E402
from s2s.orchestrator.engine import create_run  # noqa: E402


def fmt(e: Event) -> str:
    to = f" -> {e.to_agent_id}" if e.to_agent_id else ""
    return f"{e.ts:%H:%M:%S}  {e.type:<15} {(e.agent_id or '-'):<9}{to:<12} {e.summary}"


def main() -> int:
    src = sys.argv[1]
    timeout_min = float(os.environ.get("S2S_M06_TIMEOUT_MIN", "120"))
    view = access.public_view()
    print(f"model access: provider={view['provider']} model={view['model']} key_saved={view['key_set']}")
    caps = spend_caps()
    with session() as s:
        srun = s.get(Run, src)
        design = s.get(Design, srun.design_id)
        spent = spend_so_far(s, src)
        run_id = create_run(s, design, from_stage="test_build", to_stage="verification", agent_kind="s2s",
                            inputs={"source_run": src}).id
    print(f"spend caps: per design ${caps['per_design_usd']:.2f}, daily ${caps['daily_usd']:.2f}; before this run: "
          f"today ${spent['today_usd']:.4f}, design {design.name} ${spent['design_usd']:.4f}")
    print(f"design {design.name}: verification run {run_id} (from M0.5 run {src}: test_build -> verification)\n")
    logs = REPO / "var" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    evlog = open(logs / f"events_{run_id}.txt", "w")
    orc = subprocess.Popen([sys.executable, "-m", "s2s.orchestrator", "--poll", "0.2"], cwd=BACKEND,
                           env=os.environ.copy(), stdout=open(logs / f"orchestrator_{run_id}.log", "ab"),
                           stderr=subprocess.STDOUT, start_new_session=True)
    quiet = {"task.heartbeat", "manager.checkin", "agent.status", "artifact.created"}
    seen, t0 = 0, time.monotonic()
    try:
        while True:
            with session() as s:
                evs = s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()
                for e in evs[seen:]:
                    evlog.write(fmt(e) + "\n")
                    if e.type not in quiet:
                        print(fmt(e)[:220], flush=True)
                evlog.flush()
                seen = len(evs)
                run = s.get(Run, run_id)
                stopped = [t for t in s.scalars(select(Task).where(Task.run_id == run_id)) if t.status in ("paused", "failed")]
            if run.status in ("completed", "failed") or stopped or time.monotonic() - t0 > timeout_min * 60:
                break
            time.sleep(2.0)
        time.sleep(2)
        with session() as s:
            for e in s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()[seen:]:
                evlog.write(fmt(e) + "\n")
                print(fmt(e)[:220])
    finally:
        os.killpg(orc.pid, signal.SIGTERM)
        orc.wait(timeout=60)
        evlog.close()
    return report(run_id, design.id, time.monotonic() - t0)


def report(run_id: str, design_id: str, wall: float) -> int:
    with session() as s:
        run = s.get(Run, run_id)
        tasks = s.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.seq)).all()
        print(f"\n=== run {run_id}: {run.status} in {wall / 60:.1f} min ===")
        for t in tasks:
            print(f"  {t.stage:<13} {t.agent_id:<6} {t.status}")
        print("\n=== checks (Trust Layer records, in order) ===")
        for t in tasks:
            for c in s.scalars(select(Check).where(Check.task_id == t.id).order_by(Check.id)):
                det = (c.metrics or {}).get("detail")
                print(f"  {t.stage:<13} {c.check_name:<26} {'PASS' if c.passed else 'FAIL'}  {c.tool}"
                      + (f"  {det[:2]}" if det and not c.passed else ""))
        rows = s.execute(select(UsageRecord.agent_id, UsageRecord.source, func.count(), func.sum(UsageRecord.cost_usd))
                         .where(UsageRecord.run_id == run_id).group_by(UsageRecord.agent_id, UsageRecord.source)
                         .order_by(func.sum(UsageRecord.cost_usd).desc())).all()
        print("\n=== metered spend, this run ===")
        total = Decimal(0)
        for agent, src, n, cost in rows:
            print(f"  {agent:<9} {src:<8} {n:>3} record(s)  ${Decimal(cost):.6f}")
            total += Decimal(cost)
        design_runs = [r for r in s.scalars(select(Run).where(Run.design_id == design_id))]
        dtotal = s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                          .where(UsageRecord.run_id.in_([r.id for r in design_runs])))
        print(f"  TOTAL this run: ${total:.6f}")
        print(f"  TOTAL for the design (all its runs: {', '.join(r.id for r in design_runs)}): ${Decimal(dtotal):.6f}")
        print(f"  spent today (all work): ${spend_so_far(s)['today_usd']:.4f}")
    rep = artifact_dir() / "runs" / run_id / "reports/verification_report.json"
    if rep.exists():
        r = json.loads(rep.read_text())
        print("\n=== verification report ===")
        print(json.dumps({k: r.get(k) for k in ("coverage", "formal", "mutation")}, indent=1, default=str))
        print(f"real RTL bugs found: {len(r.get('real_rtl_bugs', []))}")
        for b in r.get("bugs", []):
            print(f"  [{b['classification']}] {b['requirement']}: {b['root_cause']} -> {b.get('routed_to')}")
    return 0 if run.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
