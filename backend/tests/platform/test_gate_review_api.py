"""M0.8 human gate review API (offline): GET /designs/{id}/gates lists the design's gates with the
gated stage's check evidence, and POST /gates/{id}/decision records a human decision exactly once."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.platform.conftest import new_design


def _client():
    from s2s.api.app import app
    return TestClient(app)


def test_design_gates_list_evidence_and_decide_once(platform):
    from s2s.db.models import Check, Gate, Run, Task
    from s2s.db.session import session
    from s2s.ids import new_id
    with session() as s:
        d = new_design(s, "counter8")
        run = Run(id=new_id("run"), design_id=d.id, status="running", stages=["spec", "architecture"],
                  current_stage="architecture")
        s.add(run)
        s.flush()
        task = Task(id=new_id("task"), run_id=run.id, agent_id="Kepler", stage="architecture", status="completed")
        s.add(task)
        s.flush()
        s.add_all([Check(id=new_id("chk"), task_id=task.id, check_name="arch_schema", tool="jsonschema", passed=True),
                   Check(id=new_id("chk"), task_id=task.id, check_name="req_trace", tool="s2s.trace", passed=False)])
        g = Gate(id=new_id("gate"), run_id=run.id, gate="G1", status="pending", after_stage="architecture")
        s.add(g)
        design_id, gate_id, run_id = d.id, g.id, run.id

    c = _client()
    rows = c.get(f"/designs/{design_id}/gates").json()
    assert len(rows) == 1
    row = rows[0]
    assert (row["id"], row["gate"], row["status"], row["after_stage"], row["run_id"]) == \
        (gate_id, "G1", "pending", "architecture", run_id)
    assert row["reviewer"] is None and row["decision"] is None and row["decided_at"] is None
    ev = row["evidence"]
    assert (ev["checks_passed"], ev["checks_failed"], ev["failed_checks"]) == (1, 1, ["req_trace"])

    ov = c.get(f"/designs/{design_id}/overview").json()
    arch = next(st for st in ov["stages"] if st["name"] == "architecture")
    assert arch["gate"]["id"] == gate_id and arch["gate"]["status"] == "pending"

    assert c.get("/designs/des_missing/gates").status_code == 404

    r = c.post(f"/gates/{gate_id}/decision", json={"decision": "approve_with_conditions", "reviewer": "VP Front-End",
                                                   "comments": "fix req_trace before G2"})
    assert r.status_code == 200, r.text
    row = c.get(f"/designs/{design_id}/gates").json()[0]
    assert (row["status"], row["decision"], row["reviewer"], row["comments"]) == \
        ("approved", "approve_with_conditions", "VP Front-End", "fix req_trace before G2")
    assert row["decided_at"]

    again = c.post(f"/gates/{gate_id}/decision", json={"decision": "reject", "reviewer": "someone else"})
    assert again.status_code == 409
    assert c.get(f"/designs/{design_id}/gates").json()[0]["status"] == "approved"
