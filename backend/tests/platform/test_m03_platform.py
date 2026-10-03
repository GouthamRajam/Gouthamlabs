"""M0.3 platform behavior beyond the five acceptance tests."""
from __future__ import annotations

import asyncio
import json

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select

from tests.platform.conftest import REPO, new_design, wait_for
from tests.platform.test_m03_acceptance import _events, _run_status


def test_dummy_run_emits_every_event_type(platform):
    """One dummy run exercises all 21 Part 11.2 event types through real code paths:
    small budgets (from config) trigger budget.warning/alert, a hung step triggers
    task.stalled/escalation, 3 regression failures trigger the 3-failures escalation."""
    from s2s.db.session import session
    from s2s.events.bus import EVENT_TYPES
    from s2s.orchestrator.engine import create_run
    budgets = yaml.safe_load((REPO / "config" / "budgets.yaml").read_text())
    budgets["per_agent"]["Rex"] = {"max_tool_runs": 6}  # verification uses 5 -> warning at 83%
    budgets["per_run"]["max_cost_usd"] = 0.01           # dummy run costs ~$0.0137 -> 80% and 100% alerts
    platform.set_config("budgets", budgets)
    with session() as s:
        run_id = create_run(s, new_design(s), dummy={
            "step_delay_s": 0.05, "hang": {"stage": "spec", "at_step": 2, "seconds": 7}}).id
    platform.start_orchestrator()
    wait_for(lambda: _run_status(run_id) == "completed", 90, every=0.2, what="run completion")
    seen = {e.type for e in _events(run_id)}
    print(f"\nevent types seen: {len(seen & EVENT_TYPES)}/{len(EVENT_TYPES)}")
    assert seen == EVENT_TYPES, f"missing: {sorted(EVENT_TYPES - seen)}"
    statuses = {e.status for e in _events(run_id, type="agent.status")}
    assert {"thinking", "working", "reviewing", "idle"} <= statuses
    rules = {e.detail.get("rule") for e in _events(run_id, type="escalation")}
    assert {"same failure 3 times", "stall unresolved"} <= rules
    assert {int(e.detail["pct"]) for e in _events(run_id, type="budget.alert")} == {80, 100}


def test_task_hard_budget_stop_pauses_and_escalates(platform):
    from s2s.db.models import Run, Task
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    budgets = yaml.safe_load((REPO / "config" / "budgets.yaml").read_text())
    budgets["per_agent"]["Rex"] = {"max_tool_runs": 3}  # verification needs 5 tool runs
    platform.set_config("budgets", budgets)
    with session() as s:
        run_id = create_run(s, new_design(s), from_stage="verification", to_stage="verification",
                            dummy={"step_delay_s": 0.02}).id
    platform.start_orchestrator()

    def paused():
        with session() as s:
            return s.scalar(select(Task).where(Task.run_id == run_id)).status == "paused"
    wait_for(paused, 30, what="task paused at its hard budget")
    [esc] = _events(run_id, type="escalation")
    assert esc.detail == {"budget": "tool_runs", "used": 3, "limit": 3, "rule": "hard stop"}
    assert esc.to_agent_id == "Rhea"  # Rex's department manager
    with session() as s:
        assert s.scalar(select(Run).where(Run.id == run_id)).status == "running"  # not silently done


def test_human_gate_mode_waits_for_a_decision(platform):
    from s2s.api.app import app
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    mgmt = yaml.safe_load(platform.mgmt_path.read_text())
    mgmt["gates"]["mode"] = "human"
    platform.set_config("management", mgmt)
    with session() as s:
        run_id = create_run(s, new_design(s), to_stage="rtl", dummy={"step_delay_s": 0.02}).id
    platform.start_orchestrator()
    c = TestClient(app)
    gate = wait_for(lambda: (c.get("/gates", params={"status": "pending"}).json() or [None])[0], 30,
                    what="G1 pending")
    assert gate["gate"] == "G1" and gate["run_id"] == run_id
    with session() as s:  # rtl must not start before the human decides
        assert s.scalar(select(Task).where(Task.run_id == run_id, Task.stage == "rtl")).status == "pending"
    r = c.post(f"/gates/{gate['id']}/decision", json={"decision": "approve", "reviewer": "VP Front-End",
                                                      "comments": "spec looks complete"})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert c.post(f"/gates/{gate['id']}/decision", json={"decision": "approve", "reviewer": "x"}).status_code == 409
    wait_for(lambda: _run_status(run_id) == "completed", 30, every=0.2, what="run completion after approval")
    [decided] = _events(run_id, type="gate.decided")
    assert decided.detail["mode"] == "human" and decided.detail["reviewer"] == "VP Front-End"


def test_org_loaded_from_management_yaml(platform):
    from s2s.api.app import app
    from s2s.db.models import OrgUnit
    from s2s.db.session import session
    from s2s.org import sync_org
    with session() as s:
        n = sync_org(s)
    with session() as s:
        units = s.scalars(select(OrgUnit)).all()
    assert n == len(units) == 70
    divisions = [u for u in units if u.kind == "division"]
    teams = [u for u in units if u.kind == "team"]
    assert len(divisions) == 9 and len([u for u in units if u.kind == "department"]) == 3
    per_div = {}
    for t in teams:
        d = t
        while d.parent_id:
            d = next(u for u in units if u.id == d.parent_id)
        per_div[d.id] = per_div.get(d.id, 0) + t.instances
    # MASTER_SPEC Part 6.4 instance counts per division, plus 7 directors/managers = 146
    assert per_div == {"div1": 10, "div2": 49, "div3": 15, "div4": 16, "div5": 11, "div6": 18,
                       "div7": 4, "div8": 6, "div9": 10}
    managers = {"Juno", "Hale", "Reid", "Nadia", "Rhea", "Mason", "Sloane"}
    assert managers <= {u.manager_agent_id for u in units if u.kind in ("division", "department")}
    assert sum(per_div.values()) + len(managers) == 146
    assert {t.manager_agent_id for t in teams if t.phase > 0} == {"Flux", "Bea", "Juniper", "Quinn"}
    c = TestClient(app)
    org = c.get("/org").json()
    assert [d["id"] for d in org["divisions"]] == [f"div{i}" for i in range(1, 10)]
    div2 = org["divisions"][1]
    assert [d["manager_agent_id"] for d in div2["children"]] == ["Reid", "Nadia", "Rhea"]
    agents = {a["id"]: a for a in c.get("/agents").json()}
    assert agents["Rex"]["role"] == "team_lead" and agents["Rhea"]["role"] == "manager"
    assert agents["Hale"]["role"] == "director" and agents["Vera"]["division_id"] == "div2"


def test_only_one_orchestrator_may_run(platform):
    from s2s.orchestrator.engine import AlreadyRunning, Orchestrator
    first = Orchestrator()
    first.start()
    try:
        with pytest.raises(AlreadyRunning):
            Orchestrator().start()
    finally:
        first._lock_conn.close()


def test_migration_roundtrip_matches_models(platform):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from s2s.db.models import Base
    cfg = Config(str(REPO / "backend" / "alembic.ini"))
    cfg.attributes["database_url"] = platform.url
    eng = create_engine(platform.url)
    tables = set(inspect(eng).get_table_names()) - {"alembic_version"}
    assert tables == set(Base.metadata.tables) and len(tables) == 23  # 22 from M0.3 + check_params (Part 27.6)
    command.downgrade(cfg, "base")
    assert set(inspect(eng).get_table_names()) <= {"alembic_version"}
    command.upgrade(cfg, "head")
    command.check(cfg)  # raises if the models and the migrations disagree
    eng.dispose()


def test_ws_filters(platform):
    import websockets
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    _, port = platform.start_api()
    with session() as s:
        run_a = create_run(s, new_design(s, "a"), to_stage="architecture", dummy={"step_delay_s": 0.02}).id
        run_b = create_run(s, new_design(s, "b"), to_stage="architecture", dummy={"step_delay_s": 0.02}).id
    platform.start_orchestrator()
    wait_for(lambda: _run_status(run_a) == _run_status(run_b) == "completed", 60, every=0.2, what="runs")

    async def fetch(query: str) -> list[dict]:
        out = []
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws/events?since=0-0&{query}") as ws:
            await ws.recv()  # stream.subscribed
            try:
                while True:
                    out.append(json.loads(await asyncio.wait_for(ws.recv(), timeout=1.5)))
            except asyncio.TimeoutError:
                return out

    by_run = asyncio.run(fetch(f"run_id={run_a}"))
    assert by_run and {e["run_id"] for e in by_run} == {run_a}
    assert len(by_run) == len(_events(run_a))
    by_agent = asyncio.run(fetch("agent_id=Kepler"))
    assert by_agent and {e["agent_id"] for e in by_agent} == {"Kepler"}
    div5 = asyncio.run(fetch("division=div5"))  # Atlas (program office) gates/stages
    assert div5 and {e["agent_id"] for e in div5} == {"Atlas"}


def test_api_endpoints_after_a_run(platform):
    from s2s.api.app import app
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    with session() as s:
        run_id = create_run(s, new_design(s), dummy={"step_delay_s": 0.02}).id
    platform.start_orchestrator()
    wait_for(lambda: _run_status(run_id) == "completed", 60, every=0.2, what="run completion")
    c = TestClient(app)
    run = c.get(f"/runs/{run_id}").json()
    assert run["status"] == "completed" and len(run["gates"]) == 4
    assert all(g["status"] == "approved" for g in run["gates"])
    art = next(e for e in _events(run_id, type="artifact.created"))
    sha = art.detail["artifacts"][0].split(":", 1)[1]
    blob = c.get(f"/artifacts/{sha}")
    assert blob.status_code == 200 and blob.content.startswith(b"# [dummy]")
    assert c.get(f"/runs/{run_id}/evidence/rtl").status_code == 404  # packets come in later milestones
    fin = c.get("/finance/summary").json()
    assert fin["records"] > 0 and fin["by_source"]["llm"] > 0 and fin["by_source"]["compute"] > 0
    assert fin["by_run"][run_id] == pytest.approx(fin["total_usd"])
    [b] = fin["budgets"]
    assert b["scope_id"] == run_id and b["spent_usd"] == pytest.approx(fin["total_usd"])
    dash = c.get("/management/dashboard").json()
    assert dash["task_counts"] == {"completed": 11}
    assert dash["assignments"]["count"] == 11 and dash["assignments"]["sla_hit_rate"] == 1.0
    briefs = c.get("/research/briefs").json()
    assert briefs and briefs[0]["author_agent"] == "Lyra"
    rex = c.get("/agents/Rex").json()
    assert rex["recent_events"] and rex["current_task"] is None
    page = c.get("/events", params={"run_id": run_id, "limit": 5}).json()
    older = c.get("/events", params={"run_id": run_id, "limit": 5, "before": page[-1]["id"]}).json()
    assert len(page) == 5 and older and older[0]["id"] < page[-1]["id"]
    assert c.get("/runs/nope").status_code == 404
    assert c.post("/designs/nope/runs", json={}).status_code == 404
