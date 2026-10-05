"""Operator change request fix_testplan_assertion_refs: Vera may change ONLY illegal_states `assertion` fields, each
to a property that exists in formal_top.sv (spi_master 2026-10-05: plan said a_done_implies_busy, proven property is
ap_done_implies_busy)."""
from types import SimpleNamespace

import yaml

from s2s.agents import m06

PLAN = {"illegal_states": [{"name": "done_without_busy", "expr": "done and not busy", "req": "REQ-012",
                            "assertion": "a_done_implies_busy", "reason": "r"}], "other": [1, 2]}
FORMAL = "ap_done_implies_busy: assert(!(done) || busy);\ncp_done_implies_busy: cover(done);\n"


def _run(tmp_path, monkeypatch, new_plan):
    (tmp_path / "tb").mkdir(exist_ok=True); (tmp_path / "formal").mkdir(exist_ok=True)
    (tmp_path / "tb/testplan.yaml").write_text(yaml.safe_dump(PLAN))
    (tmp_path / "formal/formal_top.sv").write_text(FORMAL)
    ctx = SimpleNamespace(workdir=tmp_path, state={})
    seen = {}

    def fake_author(c, who, *, validate, **kw):
        (tmp_path / "tb/testplan.yaml").write_text(yaml.safe_dump(new_plan))
        seen["problems"] = validate(c)
    monkeypatch.setattr(m06, "_author_loop", fake_author)
    monkeypatch.setattr(m06, "guarded", lambda c, who, change, why: change())
    monkeypatch.setattr(m06, "_assign", lambda *a, **k: None)
    monkeypatch.setattr(m06, "validate_testplan", lambda c: [])
    m06.fix_testplan_refs(ctx, ["assertion ap_a_done_implies_busy is missing"], "operator decision")
    return seen["problems"]


def test_correct_reference_passes(tmp_path, monkeypatch):
    good = yaml.safe_load(yaml.safe_dump(PLAN)); good["illegal_states"][0]["assertion"] = "done_implies_busy"
    assert _run(tmp_path, monkeypatch, good) == []


def test_reference_to_missing_property_is_refused(tmp_path, monkeypatch):
    bad = yaml.safe_load(yaml.safe_dump(PLAN)); bad["illegal_states"][0]["assertion"] = "made_up"
    assert any("no assertion ap_made_up" in p for p in _run(tmp_path, monkeypatch, bad))


def test_any_other_change_is_refused(tmp_path, monkeypatch):
    sneaky = yaml.safe_load(yaml.safe_dump(PLAN))
    sneaky["illegal_states"][0]["assertion"] = "done_implies_busy"
    sneaky["illegal_states"][0]["expr"] = "False"  # weakening the illegal state itself
    assert any("only the `assertion` fields" in p for p in _run(tmp_path, monkeypatch, sneaky))
