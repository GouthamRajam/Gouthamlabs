"""Phase 1 harness #2: an operator resume is a database operation that the orchestrator executes (it survives a
restart of every process), not a side process. Refused for anything but a paused task, and without a reason."""
from __future__ import annotations

import pytest
import yaml
from sqlalchemy import select

from tests.platform.conftest import REPO, new_design, wait_for
from tests.platform.test_m03_acceptance import _events


def test_resume_is_queued_in_the_database_and_run_by_the_orchestrator(platform):
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.ops.jobs import ResumeRefused, queue_resume
    from s2s.orchestrator.engine import create_run
    budgets = yaml.safe_load((REPO / "config" / "budgets.yaml").read_text())
    budgets["per_agent"]["Rex"] = {"max_tool_runs": 3}  # the dummy verification needs 5: pauses at the hard stop
    platform.set_config("budgets", budgets)
    with session() as s:
        run_id = create_run(s, new_design(s), from_stage="verification", to_stage="verification",
                            dummy={"step_delay_s": 0.02}).id
    orc = platform.start_orchestrator()

    def task():
        with session() as s:
            return s.scalar(select(Task).where(Task.run_id == run_id))
    wait_for(lambda: task().status == "paused", 30, what="task paused at its hard budget")
    with pytest.raises(ResumeRefused, match="reason"):
        queue_resume(task().id, " ")
    with session() as s:  # the decision a human makes before resuming: a larger budget
        t = s.scalar(select(Task).where(Task.run_id == run_id))
        t.budget = {**t.budget, "max_tool_runs": 20}
    orc.terminate(); orc.wait(10)  # the orchestrator is down when the resume is queued
    r = queue_resume(task().id, "budget raised after review")
    assert r["status"] == "ready"
    with pytest.raises(ResumeRefused, match="only a paused task"):
        queue_resume(task().id, "again")
    platform.start_orchestrator(log="orchestrator2.log")  # a fresh orchestrator picks it up from the database
    wait_for(lambda: task().status == "completed", 60, what="resumed task completed")
    [esc] = [e for e in _events(run_id, type="escalation") if (e.detail or {}).get("rule") == "operator resume"]
    assert esc.detail["queued_via"] == "database" and esc.detail["reason"] == "budget raised after review"
