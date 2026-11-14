"""Phase 1 harness #3: the runtime's tool heartbeat writes a Heartbeat row, refreshes last_progress_at and clears the
stall flag in its own transaction (callable from tool threads), throttled to one beat per interval per task."""
from __future__ import annotations

import time

from sqlalchemy import func, select

from tests.platform.conftest import new_design


def test_tool_pulse_clears_a_stall_and_is_throttled(platform):
    from s2s.agents.runtime import tool_pulse
    from s2s.db.models import Heartbeat, Task
    from s2s.db.session import session
    from s2s.events.bus import utcnow
    from s2s.orchestrator.engine import create_run
    with session() as s:
        run_id = create_run(s, new_design(s), from_stage="verification", to_stage="verification",
                            dummy={"step_delay_s": 0.02}).id
    with session() as s:
        t = s.scalar(select(Task).where(Task.run_id == run_id))
        t.stalled_at = utcnow()
        tid = t.id
    with session() as s:
        pulse, every = tool_pulse(s.get(Task, tid), 2, 5)
    assert 0 < every <= 3  # fast SLA: heartbeat 3 s, and at most a third of the stall threshold
    pulse("sby running 120s (sby_rtl_equiv.log)")
    pulse("sby running 121s (sby_rtl_equiv.log)")  # within the interval: dropped
    with session() as s:
        t = s.get(Task, tid)
        assert t.stalled_at is None and t.evidence_signal.startswith("sby running 120s")
        assert s.scalar(select(func.count()).select_from(Heartbeat).where(Heartbeat.task_id == tid)) == 1
    time.sleep(every)
    pulse("sby running 125s")
    with session() as s:
        assert s.scalar(select(func.count()).select_from(Heartbeat).where(Heartbeat.task_id == tid)) == 2
