"""Phase 1 trajectory items 1, 4, 5: labels are append-only and idempotent; false stall alarms are labelled only when a
tool was running; operator events label their task and run; the exporter orders the run, joins checks and model
calls, attaches labels and separates autonomous from operator-influenced runs."""
from __future__ import annotations

import datetime as dt
import json

from sqlalchemy import select

from tests.platform.conftest import new_design


def _ev(s, run_id, task_id, type, summary, ts, detail=None, agent="Rex"):
    from s2s.db.models import Event
    from s2s.ids import new_id
    e = Event(id=new_id("evt"), ts=ts, run_id=run_id, task_id=task_id, type=type, summary=summary, agent_id=agent,
              detail=detail or {})
    s.add(e)
    return e


def _run(s):
    from s2s.db.models import Task
    from s2s.orchestrator.engine import create_run
    run_id = create_run(s, new_design(s), from_stage="verification", to_stage="verification",
                        dummy={"step_delay_s": 0.0}).id
    s.flush()
    return run_id, s.scalar(select(Task).where(Task.run_id == run_id)).id


def test_backfill_labels_and_export(platform, tmp_path):
    from s2s.db.models import Check
    from s2s.db.session import session
    from s2s.records import annotate, trajectory
    t0 = dt.datetime(2026, 10, 7, 6, 0, tzinfo=dt.timezone.utc)
    m = dt.timedelta(minutes=1)
    with session() as s:
        run_id, tid = _run(s)
        _ev(s, run_id, tid, "plan", "Rex: plan", t0)
        _ev(s, run_id, tid, "tool_call", "Myra: mutation run", t0 + m, {"tool": "mutation"})
        stall_open = _ev(s, run_id, tid, "task.stalled", "no progress", t0 + 20 * m)
        _ev(s, run_id, tid, "tool_result", "20/20", t0 + 30 * m, {"tool": "mutation"})
        stall_idle = _ev(s, run_id, tid, "task.stalled", "no progress", t0 + 60 * m)
        _ev(s, run_id, tid, "tool_call", "Rex: model call", t0 + 61 * m, {"tool": "model"})
        _ev(s, run_id, tid, "tool_result", "answered", t0 + 62 * m, {"tool": "model"})
        s.add(Check(id="chk_01M4TEST0000000000000000AA", task_id=tid, check_name="mutation_detection", tool="mutation",
                    command="", passed=True, metrics={"rate": 1.0}))
        _ev(s, run_id, tid, "check.passed", "mutation_detection: passed", t0 + 63 * m,
            {"check_id": "chk_01M4TEST0000000000000000AA"})
    art = tmp_path / "art"
    (art / "runs" / run_id / "logs").mkdir(parents=True)
    (art / "runs" / run_id / "logs/model_calls.jsonl").write_text(
        json.dumps({"task_id": tid, "agent": "Rex", "prompt": "p", "answer": "{}"}) + "\n")

    recs = trajectory.export(run_id, art)
    assert recs[0]["kind"] == "run" and recs[0]["autonomy"] == "autonomous" and recs[-1]["kind"] == "outcome"
    kinds = [r["kind"] for r in recs]
    assert kinds.index("task") < kinds.index("plan") < kinds.index("model_call") < kinds.index("check")
    mc = next(r for r in recs if r["kind"] == "model_call")
    assert mc["model_call"]["alignment"] == "by_order" and mc["model_call"]["answer"] == "{}"
    chk = next(r for r in recs if r["kind"] == "check")
    assert chk["id"] == "chk_01M4TEST0000000000000000AA" and chk["check"]["metrics"] == {"rate": 1.0}

    with session() as s:
        out1 = annotate.backfill_false_stalls(s)
        assert out1 == {"stalls_false_alarm": 1, "stalls_not_labelled": 1}
        assert annotate.backfill_false_stalls(s)["stalls_false_alarm"] == 0  # idempotent
        _ev(s, run_id, tid, "escalation", "Operator decision (CEO): budget raised 16 -> 20", t0 + 70 * m,
            {"rule": "operator decision"}, agent="Atlas")
    with session() as s:
        annotate.backfill_operator_events(s)
    recs = trajectory.export(run_id, art)
    stalls = {r["id"]: r for r in recs if r["kind"] == "stall"}
    assert [l["label"] for l in stalls[stall_open.id]["labels"]] == ["false_alarm"]
    assert stalls[stall_idle.id]["labels"] == []  # no open tool call: not assumed false
    assert recs[0]["autonomy"] == "operator_influenced" and recs[0]["operator_influence"]
    esc = next(r for r in recs if r["kind"] == "escalation")
    assert "manual_intervention" in [l["label"] for l in esc["labels"]]
