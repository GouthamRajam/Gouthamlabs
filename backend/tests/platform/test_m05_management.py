"""M0.5 generic director / manager runtime (A3.1, A3.2): assignment briefs and SLA, stall
handling, spot checks, director reviews and escalation to humans. Real Postgres/Redis and a real
orchestrator process; the work itself is the M0.3 dummy agent (no model calls)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json

from sqlalchemy import select

from tests.platform.conftest import new_design, wait_for


def _events(run_id, type_=None):
    from s2s.db.models import Event
    from s2s.db.session import session
    with session() as s:
        q = select(Event).where(Event.run_id == run_id)
        if type_:
            q = q.where(Event.type == type_)
        return [(e.agent_id, e.to_agent_id, e.summary, e.detail, e.task_id) for e in s.scalars(q.order_by(Event.ts))]


def _run_status(run_id):
    from s2s.db.models import Run
    from s2s.db.session import session
    with session() as s:
        return s.get(Run, run_id).status


def test_every_task_gets_an_assignment_brief_from_its_manager_within_sla(platform):
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    with session() as s:
        run_id = create_run(s, new_design(s), to_stage="rtl", dummy={"step_delay_s": 0.05}).id
    platform.start_orchestrator()
    wait_for(lambda: _run_status(run_id) == "completed", 120, every=0.2, what="run completion")
    briefs = [e for e in _events(run_id, "handoff") if "assigned" in e[2]]
    for b in briefs:
        print(b[2], {k: b[3][k] for k in ("waited_s", "assign_sla_s", "within_sla")})
    assert [(b[0], b[1]) for b in briefs] == [("Juno", "Iris"), ("Juno", "Kepler"), ("Reid", "Ada")]
    for b in briefs:
        assert b[3]["within_sla"] is True
        assert {"goal", "inputs", "exit_criteria", "expected_minutes", "budget", "progress_signal"} <= set(b[3])
    # 100% spot check of completed outputs is a manager event; the dummy writes no task.result,
    # so none is due here (covered below).


def _mk_task(s, run_id, stage, team, agent, status, **kw):
    from s2s.db.models import Task
    from s2s.ids import new_id
    t = Task(id=new_id("task"), run_id=run_id, agent_id=agent, stage=stage, status=status, title=f"{stage} work",
             team_id=team, inputs={}, budget={}, expected_step_seconds=1.0, **kw)
    s.add(t)
    return t


def test_assignment_sla_stall_handling_and_escalation_to_humans(platform):
    from s2s.agents import management as mgmt
    from s2s.db.models import Run, Task
    from s2s.db.session import session
    from s2s.events.bus import utcnow
    from s2s.ids import new_id
    now = utcnow()
    with session() as s:
        d = new_design(s)
        run = Run(id=new_id("run"), design_id=d.id, status="running", stages=["spec", "rtl"], agent_kind="dummy")
        s.add(run)
        s.flush()
        waiting = _mk_task(s, run.id, "spec", "spec_requirements", "Iris", "ready",
                           ready_at=now - dt.timedelta(minutes=5))
        dead = _mk_task(s, run.id, "architecture", "micro_architecture", "Kepler", "running",
                        stalled_at=now - dt.timedelta(seconds=1), checkpoint={"step": 2, "state": {}})
        hung = _mk_task(s, run.id, "rtl", "datapath_rtl", "Ada", "running", stalled_at=now - dt.timedelta(seconds=1))
        ids = (run.id, waiting.id, dead.id, hung.id)
    run_id, waiting_id, dead_id, hung_id = ids
    done = mgmt.tick(inflight={hung_id})
    print(done)
    assert done["assign_sla_flags"] == 1 and done["reassigned"] == 1 and done["stall_escalations"] == 1
    assert done["director_reviews"] >= 1
    with session() as s:
        assert s.get(Task, dead_id).status == "ready"  # reassigned, keeps its checkpoint
        assert s.get(Task, dead_id).checkpoint["step"] == 2
    esc = _events(run_id, "escalation")
    for e in esc:
        print(e[0], "->", e[1], ":", e[2])
    assert (esc[0][0], esc[0][1]) == ("Juno", "Atlas")  # Juno manages Spec directly: next level is Atlas
    assert any(e[0] == "Reid" and e[1] == "Hale" and "worker still running" in e[2] for e in esc)
    reassigned = [e for e in _events(run_id, "handoff") if "reassigned" in e[2]]
    assert reassigned and reassigned[0][0] == "Juno" and reassigned[0][1] == "Kepler"
    # a second pass does not repeat the same actions
    again = mgmt.tick(inflight={hung_id})
    assert again["assign_sla_flags"] == 0 and again["stall_escalations"] == 0
    # unresolved manager escalation -> the director forwards it to the human owner
    later = utcnow() + dt.timedelta(minutes=1)  # FAST_SLA: escalate_to_human_after 3 s
    third = mgmt.tick(inflight={hung_id}, now=later)
    print(third)
    to_human = [e for e in _events(run_id, "escalation") if e[1] == "human"]
    assert third["to_human"] == 1 and to_human[0][0] == "Juno"
    assert to_human[0][3]["human_owner"] == "Front-end cofounder (later VP Architecture)"
    reviews = _events(run_id, "manager.checkin")
    assert any(r[3].get("rule") == "director review" for r in reviews)


def test_spot_check_rehashes_completed_outputs(platform):
    from s2s.agents import management as mgmt
    from s2s.agents.runtime import artifact_dir
    from s2s.db.models import Run
    from s2s.db.session import session
    from s2s.ids import new_id
    with session() as s:
        d = new_design(s)
        run = Run(id=new_id("run"), design_id=d.id, status="running", stages=["spec"], agent_kind="s2s")
        s.add(run)
        s.flush()
        root = artifact_dir() / "runs" / run.id
        (root / "spec").mkdir(parents=True)
        (root / "reports").mkdir()
        (root / "spec/spec.yaml").write_text("design: x\n")
        res = {"outputs": [{"path": "spec/spec.yaml", "sha256": hashlib.sha256(b"design: x\n").hexdigest()}]}
        (root / "reports/task_result_spec.json").write_text(json.dumps(res))
        good = _mk_task(s, run.id, "spec", "spec_requirements", "Iris", "completed",
                        outputs={"task_result": "reports/task_result_spec.json"})
        run_id = run.id
    assert mgmt.tick()["spot_checks"] == 1
    (root / "spec/spec.yaml").write_text("design: tampered\n")
    with session() as s:
        _mk_task(s, run_id, "architecture", "micro_architecture", "Kepler", "completed",
                 outputs={"task_result": "reports/task_result_spec.json"})
    done = mgmt.tick()
    print(done)
    assert done["spot_check_failures"] == 1
    checks = [e for e in _events(run_id, "manager.checkin") if e[3].get("rule") == "spot check"]
    assert [c[3]["passed"] for c in checks] == [True, False]
    assert checks[1][3]["mismatches"] == ["spec/spec.yaml"]


def test_watchdog_is_not_blocked_by_a_working_step(platform):
    """A step that has inserted rows referencing its task (checks, artifacts) holds a key-share lock
    on the task row until it commits. The watchdog, the manager stall pass and in-step heartbeats must
    not wait for that (found in M0.6: a 50-minute formal step froze the orchestrator loop)."""
    import threading
    import time as _t
    from sqlalchemy import text
    from s2s.agents import management as mgmt
    from s2s.db.models import Check, Run
    from s2s.db.session import session
    from s2s.events.bus import utcnow
    from s2s.ids import new_id
    from s2s.orchestrator import watchdog
    with session() as s:
        d = new_design(s)
        run = Run(id=new_id("run"), design_id=d.id, status="running", stages=["spec"], agent_kind="dummy")
        s.add(run)
        s.flush()
        t = _mk_task(s, run.id, "spec", "spec_requirements", "Iris", "running",
                     last_progress_at=utcnow() - dt.timedelta(minutes=5))
        tid = t.id
    held, release = threading.Event(), threading.Event()

    def working_step():
        with session() as s:  # like a step: FK insert, transaction left open
            s.add(Check(id=new_id("chk"), task_id=tid, check_name="x", tool="t", command="", passed=True, metrics={}))
            s.flush()
            held.set()
            release.wait(30)
    th = threading.Thread(target=working_step)
    th.start()
    held.wait(10)
    t0 = _t.monotonic()
    with session() as s:
        s.execute(text("set local lock_timeout = '5s'"))
    done = watchdog.tick()
    mgmt.tick()
    took = _t.monotonic() - t0
    release.set()
    th.join()
    print(f"watchdog + manager pass took {took:.2f}s while a step held its task row; {done}")
    assert took < 3 and done["stalled"] == 1
