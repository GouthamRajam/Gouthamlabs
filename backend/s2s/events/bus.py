"""Event bus (MASTER_SPEC Part 11).

Every agent action emits an event, validated against the Part 11.1 schema, persisted to the
`events` table (the source of truth) and published to the Redis stream `s2s:events` (the
live feed). Two kinds:

  - State events (default) describe database rows written in the caller's transaction
    (a heartbeat + checkpoint, an artifact, a check, a gate decision, ...). They are written
    in that transaction and published only after it commits, so a viewer never sees an event
    for work that was rolled back. Their `ts` is the commit time: the moment the fact
    became true.
  - Live events (`immediate=True`: an agent's status, plan, tool started/finished) are facts
    the moment they happen. They are committed in their own transaction and published at
    once, so the Live Office shows "tool running" while the tool runs, not after its step.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from functools import lru_cache
from typing import Any

import redis
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session

from s2s.config import settings
from s2s.db.models import Event
from s2s.ids import new_id

log = logging.getLogger(__name__)

# Part 11.2 (check.passed/check.failed and gate.requested/gate.decided are separate types).
EVENT_TYPES = frozenset({
    "agent.status", "task.started", "plan", "tool_call", "tool_result", "artifact.created",
    "check.passed", "check.failed", "handoff", "finding", "gate.requested", "gate.decided",
    "task.completed", "budget.warning", "escalation", "stage.changed", "task.heartbeat",
    "task.stalled", "manager.checkin", "budget.alert", "research.brief",
})
AGENT_STATUSES = frozenset({"idle", "thinking", "working", "waiting", "blocked", "reviewing"})

_PENDING = "s2s_pending_events"


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@lru_cache(maxsize=None)
def redis_client(url: str | None = None) -> redis.Redis:
    return redis.Redis.from_url(url or settings().redis_url, decode_responses=True)


def emit(
    session: Session,
    type: str,
    summary: str,
    *,
    run_id: str | None = None,
    design_id: str | None = None,
    team: str | None = None,
    agent_id: str | None = None,
    stage: str | None = None,
    task_id: str | None = None,
    status: str | None = None,
    detail: dict[str, Any] | None = None,
    to_agent_id: str | None = None,
    progress: float | None = None,
    immediate: bool = False,
) -> dict[str, Any]:
    """Validate and record one event. Returns the event JSON.

    State event (default): in the caller's transaction, published after its commit.
    `immediate=True`: committed and published now, independent of the caller's transaction.
    """
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type {type!r}")
    if type == "agent.status" and status not in AGENT_STATUSES:
        raise ValueError(f"agent.status needs status in {sorted(AGENT_STATUSES)}, got {status!r}")
    if not summary:
        raise ValueError("event summary is required")
    if progress is not None and not 0.0 <= progress <= 1.0:
        raise ValueError(f"progress must be within 0..1, got {progress}")
    ts = utcnow()
    ev = {
        "id": new_id("evt"), "ts": iso(ts), "run_id": run_id, "design_id": design_id,
        "team": team, "agent_id": agent_id, "agent_name": agent_id, "stage": stage,
        "task_id": task_id, "type": type, "status": status, "summary": summary,
        "detail": detail or {}, "to_agent_id": to_agent_id, "progress": progress,
    }
    row = Event(**{**ev, "ts": ts})
    if immediate:
        from s2s.db.session import session as own_session
        with own_session() as s:
            s.add(row)  # published by the after_commit hook of this short transaction
            s.info.setdefault(_PENDING, []).append((row, ev, True))
        return ev
    session.add(row)
    session.info.setdefault(_PENDING, []).append((row, ev, False))
    return ev


def publish(events: list[dict[str, Any]]) -> None:
    """XADD events to the Redis stream (used after commit; also usable directly)."""
    if not events:
        return
    s = settings()
    pipe = redis_client(s.redis_url).pipeline(transaction=False)
    for ev in events:
        pipe.xadd(s.event_stream, {"event": json.dumps(ev)}, maxlen=s.event_stream_maxlen,
                  approximate=True)
    pipe.execute()


@sa_event.listens_for(Session, "before_commit")
def _stamp_commit_time(session: Session) -> None:
    """State events become true when their transaction commits: stamp that time."""
    now = utcnow()
    for row, ev, immediate in session.info.get(_PENDING, []):
        if not immediate:
            row.ts = now
            ev["ts"] = iso(now)


@sa_event.listens_for(Session, "after_commit")
def _publish_after_commit(session: Session) -> None:
    pending = [ev for _, ev, _ in session.info.pop(_PENDING, [])]
    try:
        publish(pending)
    except redis.RedisError:  # the event is safely in the DB; the live feed missed it
        log.exception("failed to publish %d event(s) to the stream", len(pending))


@sa_event.listens_for(Session, "after_rollback")
def _drop_after_rollback(session: Session) -> None:
    session.info.pop(_PENDING, None)
