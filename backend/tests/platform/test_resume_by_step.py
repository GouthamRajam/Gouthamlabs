"""Phase 1 harness #4: the runtime records WHICH step blocked a task; a resume re-runs that step by default and never
moves forward past an unfinished step (2026-10-07: a resume after the mutation step had blocked skipped it)."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from tests.platform.conftest import new_design

RAN: list[str] = []


def _agent_cls(block: dict):
    from s2s.agents.runtime import Agent, NeedsHuman

    def plan(ctx):
        RAN.append("plan")

    def mutation(ctx):  # like Myra: a harness error sets the block, the next step pauses the task
        RAN.append("mutation")
        if block["on"]:
            ctx.state["blocked"] = "mutation harness error"
        else:
            ctx.state["mutation"] = {"detected": 20, "total": 20}

    def stop_if_blocked(ctx):
        RAN.append("stop_if_blocked")
        if ctx.state.get("blocked"):
            raise NeedsHuman(ctx.state["blocked"])

    def report(ctx):
        RAN.append("report")
        assert "mutation" in ctx.state, "report reached without a mutation result"

    class Blocking(Agent):
        def steps(self, task):
            return [plan, mutation, stop_if_blocked, report]
    return Blocking


@pytest.fixture
def blocked_task(platform, monkeypatch):
    from s2s.agents.runtime import run_task
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.orchestrator import engine
    block = {"on": True}
    cls = _agent_cls(block)
    monkeypatch.setitem(engine.AGENTS, "dummy", cls)  # queue_resume reads the step names from the run's agent kind
    with session() as s:
        run_id = engine.create_run(s, new_design(s), from_stage="verification", to_stage="verification",
                                   dummy={"step_delay_s": 0.0}).id
    with session() as s:
        tid = s.scalar(select(Task).where(Task.run_id == run_id)).id
    RAN.clear()
    out = run_task(tid, cls())
    assert out.status == "paused" and RAN == ["plan", "mutation", "stop_if_blocked"]
    return tid, block, cls


def test_runtime_records_the_blocking_step(blocked_task):
    from s2s.db.models import Task
    from s2s.db.session import session
    tid, _, _ = blocked_task
    with session() as s:
        ck = s.get(Task, tid).checkpoint
    assert ck["step"] == 2  # two steps completed: the count points AFTER the blocking step
    assert ck["state"]["blocked_step"] == {"index": 1, "name": "mutation"}


def test_default_resume_reruns_the_blocking_step(blocked_task):
    from s2s.agents.runtime import run_task
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.ops.jobs import queue_resume
    tid, block, cls = blocked_task
    r = queue_resume(tid, "mutation harness fixed")
    assert r["resume_step"] == 1 and r["resume_step_name"] == "mutation"
    with session() as s:
        t = s.get(Task, tid)
        assert t.status == "ready" and "blocked" not in t.checkpoint["state"]
        t.status = "running"  # what the orchestrator does when it assigns the task
    block["on"] = False
    RAN.clear()
    assert run_task(tid, cls()).status == "completed"
    assert RAN == ["mutation", "stop_if_blocked", "report"]  # the blocking step ran again; nothing skipped


def test_a_resume_never_skips_forward(blocked_task):
    from s2s.ops.jobs import ResumeRefused, queue_resume
    tid, _, _ = blocked_task
    with pytest.raises(ResumeRefused, match="after the step that blocked the task"):
        queue_resume(tid, "skip it", step="stop_if_blocked")
    with pytest.raises(ResumeRefused, match="unfinished steps"):
        queue_resume(tid, "skip it", step="report")


def test_old_checkpoint_without_the_blocking_step_needs_a_named_step(blocked_task):
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.ops.jobs import ResumeRefused, queue_resume
    tid, _, _ = blocked_task
    with session() as s:  # a checkpoint written before the runtime recorded blocked_step
        t = s.get(Task, tid)
        st = dict(t.checkpoint["state"]); st.pop("blocked_step")
        t.checkpoint = {**t.checkpoint, "state": st}
    with pytest.raises(ResumeRefused, match="blocking step is not recorded"):
        queue_resume(tid, "resume")
    assert queue_resume(tid, "re-run mutation", step="mutation")["resume_step"] == 1
