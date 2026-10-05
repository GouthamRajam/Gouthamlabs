"""task.result records outputs as they are at completion; an output rewritten by an interrupted step attempt after
its last recorded hash is reported as an open issue (sync_fifo place_route spot-check, 2026-10-05)."""
import hashlib
import json
from types import SimpleNamespace

from s2s.agents import m05


def test_rewritten_output_is_reported_not_hidden(tmp_path, monkeypatch):
    monkeypatch.setattr(m05, "_record", lambda *a, **k: None)
    (tmp_path / "reports").mkdir()
    a, b = tmp_path / "reports/a.json", tmp_path / "reports/b.json"
    a.write_text("old"); b.write_text("same")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    state = {"outputs": {"reports/a.json": sha(a), "reports/b.json": sha(b)},
             "answers": {"Orion": {"summary": "s", "self_assessment": {"confidence": "high", "reason": "r"}}}}
    a.write_text("new")  # rewritten after the hash was recorded
    ctx = SimpleNamespace(state=state, workdir=tmp_path, evidence=None,
                          task=SimpleNamespace(id="t", agent_id="Orion", outputs={}),
                          artifact=lambda *x, **k: None)
    m05._task_result(ctx, "place_route")
    res = json.loads((tmp_path / "reports/task_result_place_route.json").read_text())
    by = {o["path"]: o["sha256"] for o in res["outputs"]}
    assert by["reports/a.json"] == sha(a) and by["reports/b.json"] == sha(b)  # spot check will now match
    assert any("reports/a.json was rewritten" in i for i in res["open_issues"])
    assert not any("b.json" in i for i in res["open_issues"])
