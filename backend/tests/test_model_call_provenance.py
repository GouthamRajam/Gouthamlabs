"""Phase 1 trajectory items 3/4: a model call's record says what actually answered it, which attempt it was, what
feedback the earlier attempt got, the exact system prompt, and whether an operator note influenced it. A note reaches
the answerer only inside the request, so the record explains the answer."""
import json
import threading
import time
from types import SimpleNamespace as NS

import pytest

from s2s.agents import llm
from s2s.models.gateway import BridgeProvider, ModelGateway, ScriptedProvider
from s2s.ops.bridge import assign

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}


def _answer(root, answers, note=None, model="claude-opus-5-5"):
    """Plays the operator + answering subagent for successive bridge requests."""
    def run():
        done = set()
        while len(done) < len(answers):
            for rq in sorted((root / "requests").glob("br_*.json")):
                rid = rq.stem
                if rid in done or rid.endswith(".assign"):
                    continue
                n = note if not done else None
                assign(rid, model, note=n, root=root)
                req = json.loads(rq.read_text())
                assert not n or req["operator_note"][0]["text"] == n  # the answerer sees it in the request
                (root / "responses" / f"{rid}.json").write_text(answers[len(done)])
                done.add(rid)
            time.sleep(0.05)
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return th


def test_bridge_records_answering_model_attempts_and_operator_note(tmp_path):
    bp = BridgeProvider(root=str(tmp_path), timeout_s=10)
    th = _answer(tmp_path, ['{"x": "no"}', '{"x": 3}'], note="18 of 20 tool runs used: escalate")
    r = bp.complete("sys", [{"role": "user", "content": "go"}], 100, SCHEMA)
    th.join(5)
    p = r.provenance
    assert p["answered_by"] == {"model": "claude-opus-5-5", "via": "claude-code subagent"}
    assert [a["rejected_because"] is None for a in p["attempts"]] == [False, True]
    assert p["attempts"][1]["feedback_given"].startswith("Your previous answer was rejected")
    assert p["operator_influenced"] and p["operator_notes"][0]["note"][0]["text"].startswith("18 of 20")


def test_unassigned_bridge_answer_is_unrecorded_not_guessed(tmp_path):
    bp = BridgeProvider(root=str(tmp_path), timeout_s=10)

    def answer():
        while True:
            rqs = list((tmp_path / "requests").glob("br_*.json"))
            if rqs:
                (tmp_path / "responses" / f"{rqs[0].stem}.json").write_text('{"x": 1}')
                return
            time.sleep(0.05)
    threading.Thread(target=answer, daemon=True).start()
    p = bp.complete("sys", [{"role": "user", "content": "go"}], 100, SCHEMA).provenance
    assert p["answered_by"] == "unrecorded" and not p["operator_influenced"]


def test_assign_refuses_after_the_answer(tmp_path):
    (tmp_path / "requests").mkdir(); (tmp_path / "responses").mkdir()
    (tmp_path / "requests/br_1.json").write_text("{}"); (tmp_path / "responses/br_1.json").write_text("{}")
    with pytest.raises(RuntimeError, match="already answered"):
        assign("br_1", "m", root=tmp_path)


def test_transcript_record_is_training_grade(tmp_path, monkeypatch):
    from s2s.finance import meter
    monkeypatch.setattr(meter, "check_spend_caps", lambda task: None)
    monkeypatch.setattr(meter, "record_llm", lambda *a, **k: NS(cost_usd=0))
    sp = ScriptedProvider()
    sp.replies.extend([{"plan": "p", "status": "success"}, {"plan": "p2", "status": "success"}])
    events = []
    ctx = NS(task=NS(id="task_1", run_id="run_1", stage="synthesis", inputs={}, agent_id="Sienna"), step_index=3,
             state={}, workdir=tmp_path, gateway=ModelGateway(sp),
             ref=meter.TaskRef("task_1", "run_1", "Sienna", "synthesis", None, {}),
             emit=lambda *a, **k: events.append((a, k)))
    schema = {"type": "object"}
    llm.ask(ctx, "Sienna", goal="Write the SDC", inputs={}, exit_criteria=["x"], schema=schema)
    llm.ask(ctx, "Sienna", goal="Write the SDC", inputs={}, exit_criteria=["x"], schema=schema,
            previous_attempts="the SDC guard refused: set_false_path")
    recs = [json.loads(l) for l in (tmp_path / "logs/model_calls.jsonl").read_text().splitlines()]
    assert [r["attempt"] for r in recs] == [1, 2] and recs[1]["prior_feedback"].startswith("the SDC guard")
    r = recs[0]
    assert r["schema"] == 2 and r["run_id"] == "run_1" and r["step_index"] == 3 and r["ts"]
    assert r["model"] == "dummy-model" and r["answered_by"] == "dummy-model" and r["operator_influenced"] is False
    assert (tmp_path / "logs/system_prompts" / f"{r['system_sha256']}.txt").read_text() == sp.calls[0]["system"]
