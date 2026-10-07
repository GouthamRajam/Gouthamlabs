"""Database-resumable operator jobs (Phase 1 harness #2).

Operator work on a paused task (resume it after a fix or a decision) used to be a separate Python process that
called run_task directly. A container restart killed those processes and nothing could bring them back. Here a
resume is a database change: the task goes back to `ready` at its checkpoint and the orchestrator runs it. If the
orchestrator dies, its start-up recovery re-queues the task, so the job survives restarts. Every resume is an
`escalation` event with the operator's reason (part of the run's decision record).

    python -m s2s.ops.jobs resume <task_id> --reason "<why>"
"""
from __future__ import annotations

import argparse
import json
import sys

from sqlalchemy import select

from s2s.db.models import Run, Task
from s2s.db.session import session as db_session
from s2s.events.bus import emit, utcnow

RESUMABLE = ("paused",)


class ResumeRefused(RuntimeError):
    pass


def queue_resume(task_id: str, reason: str, actor: str = "operator") -> dict:
    """Put a paused task back in the orchestrator's queue at its checkpoint. Refuses anything not paused."""
    if not reason.strip():
        raise ResumeRefused("a resume needs a reason (it is part of the decision record)")
    with db_session() as s:
        t = s.scalars(select(Task).where(Task.id == task_id).with_for_update()).one_or_none()
        if t is None:
            raise ResumeRefused(f"no task {task_id}")
        if t.status not in RESUMABLE:
            raise ResumeRefused(f"task {task_id} is {t.status}; only a paused task can be resumed")
        run = s.get(Run, t.run_id)
        if run.status not in ("pending", "running"):
            raise ResumeRefused(f"run {run.id} is {run.status}; the orchestrator does not advance it")
        step = int((t.checkpoint or {}).get("step", 0))
        t.status, t.ready_at, t.lease_owner, t.stalled_at, t.escalated_at = "ready", utcnow(), None, None, None
        emit(s, "escalation", f"Operator: resume queued for {t.agent_id}'s '{t.stage}' task at checkpoint step {step}: "
             f"{reason}"[:300], run_id=t.run_id, design_id=run.design_id, agent_id="Atlas", stage=t.stage,
             task_id=t.id, detail={"rule": "operator resume", "actor": actor, "reason": reason,
                                   "resume_step": step, "queued_via": "database"})
        return {"task": t.id, "status": "ready", "resume_step": step}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.ops.jobs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resume", help="queue a paused task for the orchestrator at its checkpoint")
    r.add_argument("task_id")
    r.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    try:
        print(json.dumps(queue_resume(a.task_id, a.reason)))
    except ResumeRefused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
