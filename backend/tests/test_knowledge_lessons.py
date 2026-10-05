"""S2S's engineering memory (D5): every lesson is complete, names a regression test that exists, and is found by
the agents' keyword search for the problems it describes."""
from pathlib import Path

from s2s.knowledge import kb

TESTS = Path(__file__).resolve().parents[1]  # backend/
FIELDS = ("id", "kind", "title", "symptom", "lesson", "tags", "source", "date", "confidence", "owner")


def _ours():
    return [e for e in kb.seed_entries() if e["kind"] in ("s2s_lesson", "forbidden_method")]


def test_entries_complete_and_unique():
    ids = [e["id"] for e in kb.seed_entries()]
    assert len(ids) == len(set(ids))
    for e in _ours():
        assert all(e.get(f) for f in FIELDS), e["id"]


def test_every_lesson_has_root_cause_evidence_and_an_existing_regression_test():
    for e in _ours():
        if e["kind"] != "s2s_lesson":
            continue
        assert e.get("root_cause") and e.get("evidence"), e["id"]
        path = e["regression_test"].split("::")[0]
        assert (TESTS / path).exists(), f"{e['id']}: {path} does not exist"


def test_agents_find_the_lesson_for_their_problem():
    assert "s2s-cts-001" in [e["id"] for e in kb.search("place route max_fanout_violations = 3 clkbuf")]
    assert "s2s-fv-001" in [e["id"] for e in kb.search("debug formal induction failed")]
    assert "s2s-mut-001" in [e["id"] for e in kb.search("mutation missing_reset survived")]
    assert "s2s-forbid-001" in [e["id"] for e in kb.search("waiver policy mutation formal")]
