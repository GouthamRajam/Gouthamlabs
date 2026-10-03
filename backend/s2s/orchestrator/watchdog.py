"""Heartbeat watchdog and manager check-ins (MASTER_SPEC Part 6.6.2), from config/management.yaml.

  - A running task is stalled when it has made no progress (no heartbeat) for
    min(stall_minutes, stall_multiplier_of_expected_step x expected step time). It is
    flagged once: tasks.stalled_at + a `task.stalled` event to its manager.
  - A stall that lasts escalate_to_human_after_minutes more raises an `escalation`.
  - Every running task gets a `manager.checkin` from its manager every
    manager_checkin_minutes.
A heartbeat (any committed step) clears the stall flag.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select

from s2s.config import sla_seconds, management
from s2s.db.models import Task
from s2s.db.session import session as db_session
from s2s.events.bus import emit, utcnow
from s2s.org import load_org


def stall_threshold_s(task: Task) -> float:
    mult = float(management()["sla"]["stall_multiplier_of_expected_step"])
    return min(sla_seconds("stall_minutes"), mult * float(task.expected_step_seconds))


def _manager(task: Task) -> str | None:
    chain = load_org().manager_chain(task.team_id) if task.team_id else []
    return chain[0] if chain else None


def tick(now: dt.datetime | None = None) -> dict[str, int]:
    """One watchdog pass. Returns counts of what it did (for logs/tests)."""
    now = now or utcnow()
    done = {"stalled": 0, "escalated": 0, "checkins": 0}
    checkin_s = sla_seconds("manager_checkin_minutes")
    escalate_s = sla_seconds("escalate_to_human_after_minutes")
    with db_session() as s:
        ids = s.scalars(select(Task.id).where(Task.status == "running")).all()
    for tid in ids:
        with db_session() as s:
            t = s.get(Task, tid, with_for_update=True)
            if t is None or t.status != "running":
                continue
            mgr = _manager(t)
            base = dict(run_id=t.run_id, task_id=t.id, stage=t.stage, design_id=t.inputs.get("design_id"))
            last = t.last_progress_at or t.assigned_at or t.started_at
            silent = (now - last).total_seconds() if last else 0.0
            threshold = stall_threshold_s(t)
            if t.stalled_at is None and silent > threshold:
                t.stalled_at = now
                done["stalled"] += 1
                emit(s, "task.stalled", f"{t.agent_id}: no progress for {silent:.1f}s "
                     f"(threshold {threshold:.1f}s); flagged to {mgr}", agent_id=t.agent_id,
                     team=t.team_id, to_agent_id=mgr, status="blocked", **base,
                     detail={"silent_s": round(silent, 3), "threshold_s": threshold,
                             "last_progress_at": last.isoformat() if last else None,
                             "evidence_signal": t.evidence_signal, "manager": mgr})
            elif t.stalled_at is not None and t.escalated_at is None \
                    and (now - t.stalled_at).total_seconds() > escalate_s:
                t.escalated_at = now
                done["escalated"] += 1
                emit(s, "escalation", f"{t.agent_id}: stalled for over {escalate_s:.0f}s; "
                     "needs a human", agent_id=mgr or t.agent_id, team=t.team_id, to_agent_id="human",
                     **base, detail={"rule": "stall unresolved", "stalled_at": t.stalled_at.isoformat()})
            if mgr and (t.last_checkin_at is None or (now - t.last_checkin_at).total_seconds() >= checkin_s):
                t.last_checkin_at = now
                done["checkins"] += 1
                emit(s, "manager.checkin", f"{mgr} checked {t.agent_id}: {t.percent:.0%} "
                     f"({t.evidence_signal or 'no evidence yet'})", agent_id=mgr, to_agent_id=t.agent_id,
                     **base, detail={"percent": t.percent, "evidence_signal": t.evidence_signal,
                                     "stalled": t.stalled_at is not None})
    return done
