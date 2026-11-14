"""Database-resumable operator jobs (Phase 1 harness #2).

Operator work on a paused task (resume it after a fix or a decision) used to be a separate Python process that
called run_task directly. A container restart killed those processes and nothing could bring them back. Here a
resume is a database change: the task goes back to `ready` at its checkpoint and the orchestrator runs it. If the
orchestrator dies, its start-up recovery re-queues the task, so the job survives restarts. Every resume is an
`escalation` event with the operator's reason (part of the run's decision record).

    python -m s2s.ops.jobs resume <task_id> --reason "<why>" [--step <name>[#k]]

Resume by step NAME, never by a completed-step count (Phase 1 harness #4). The checkpoint's `step` counts completed
steps, so on 2026-10-07 a resume "at step 8" after the mutation step had blocked the task started AFTER it and the task
completed without a mutation result. Now: a task blocked by a step is resumed AT that step by default (the runtime
records it in state.blocked_step), the stale `blocked` flag is cleared, and a resume may never move forward past a
step that has not finished.
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


def step_names(task: Task, agent_kind: str) -> list[str]:
    import s2s.agents.m06  # noqa: F401  (register the M0.6/M0.7 stage step lists)
    import s2s.agents.m07  # noqa: F401
    from s2s.orchestrator.engine import AGENTS
    return [f.__name__ for f in AGENTS[agent_kind]().steps(task)]


def resolve_step(names: list[str], step: str) -> int:
    """Index of `step` ("name", or "name#k" for the k-th of several steps with that name)."""
    name, _, k = step.partition("#")
    hits = [i for i, n in enumerate(names) if n == name]
    if not hits:
        raise ResumeRefused(f"no step named {name!r}; steps: {names}")
    if not k:
        if len(hits) > 1:
            raise ResumeRefused(f"{len(hits)} steps are named {name!r} (indices {hits}); say which: {name}#1..#{len(hits)}")
        return hits[0]
    if not k.isdigit() or not 1 <= int(k) <= len(hits):
        raise ResumeRefused(f"{step!r}: there are {len(hits)} steps named {name!r}")
    return hits[int(k) - 1]


def queue_resume(task_id: str, reason: str, actor: str = "operator", step: str | None = None) -> dict:
    """Put a paused task back in the orchestrator's queue. Refuses anything not paused, and any resume point that would
    skip a step that has not finished (see the module docstring)."""
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
        ckpt = dict(t.checkpoint or {})
        done = int(ckpt.get("step", 0))  # steps completed
        state = dict(ckpt.get("state") or {})
        names = step_names(t, run.agent_kind)
        blocked, blocked_step = state.get("blocked"), state.get("blocked_step")
        if step is not None:
            target = resolve_step(names, step)
            if target > done:
                raise ResumeRefused(f"step {names[target]!r} (index {target}) is after unfinished steps "
                                    f"{names[done:target]}: a resume never skips a step")
            if blocked and blocked_step and target > blocked_step["index"]:
                raise ResumeRefused(f"{names[target]!r} is after the step that blocked the task "
                                    f"({blocked_step['name']!r}, index {blocked_step['index']}): it would be skipped")
        elif blocked:
            if not blocked_step:
                raise ResumeRefused("the task is blocked but the blocking step is not recorded (older checkpoint): "
                                    f"name the step to re-run with --step; steps: {names}")
            target = blocked_step["index"]
        else:
            target = done
        state.pop("blocked", None)
        state.pop("blocked_step", None)
        t.checkpoint = {**ckpt, "step": target, "state": state}
        t.status, t.ready_at, t.lease_owner, t.stalled_at, t.escalated_at = "ready", utcnow(), None, None, None
        name = names[target] if target < len(names) else "(end)"
        emit(s, "escalation", f"Operator: resume queued for {t.agent_id}'s '{t.stage}' task at step '{name}' "
             f"(index {target}): {reason}"[:300], run_id=t.run_id, design_id=run.design_id, agent_id="Atlas",
             stage=t.stage, task_id=t.id,
             detail={"rule": "operator resume", "actor": actor, "reason": reason, "resume_step": target,
                     "resume_step_name": name, "steps_completed_before": done, "cleared_block": blocked,
                     "blocked_step": blocked_step, "queued_via": "database"})
        return {"task": t.id, "status": "ready", "resume_step": target, "resume_step_name": name}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.ops.jobs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resume", help="queue a paused task for the orchestrator at its checkpoint")
    r.add_argument("task_id")
    r.add_argument("--reason", required=True)
    r.add_argument("--step", help="step name to re-run (name#k if several share the name); default: the step that "
                                  "blocked the task, else the checkpoint")
    a = ap.parse_args(argv)
    try:
        print(json.dumps(queue_resume(a.task_id, a.reason, step=a.step)))
    except ResumeRefused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
