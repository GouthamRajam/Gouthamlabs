"""Phase 1 trajectory item 2: structured decision log with a schema and id links; legacy prose kept as unstructured."""
import datetime as dt
import json

import pytest

from s2s.records import decisions as d

MD = """# Decisions
- 2026-10-05 (M0.7) — Raised budget for run_01M43MDNVKWCHEQ0GGHPJFT602 task_01M43MDNWHYXH7R7VYFNE6PW46.
- 2026-10-06 — No scope here.
not an entry
- 2026-10-07 (P&R) [D-20261007-001] — a structured entry rendered into the markdown (skipped).
"""


def test_legacy_entries_are_unstructured_with_extracted_ids():
    recs = d.legacy_from_markdown(MD)
    assert [r["id"] for r in recs] == ["L-0001", "L-0002"]
    assert recs[0]["links"] == {"runs": ["run_01M43MDNVKWCHEQ0GGHPJFT602"], "tasks": ["task_01M43MDNWHYXH7R7VYFNE6PW46"]}
    assert all(r["legacy"] and not r["structured"] and not d.validate(r, d.LEGACY_SCHEMA) for r in recs)


def test_add_validates_numbers_and_renders(tmp_path):
    log, md = tmp_path / "decisions.jsonl", tmp_path / "DECISIONS.md"
    md.write_text("")
    now = dt.datetime(2026, 10, 8, 9, 0, tzinfo=dt.timezone.utc)
    a = d.add(actor="CEO", kind="budget", scope="P&R", title="t", decision="raise 16 -> 20", outcome="fail",
              links={"runs": ["run_x"], "checks": []}, log=log, md=md, now=now)
    b = d.add(actor="analyzer", kind="outcome", scope="P&R", title="t2", decision="stop", log=log, md=md, now=now)
    assert (a["id"], b["id"]) == ("D-20261008-001", "D-20261008-002") and a["links"] == {"runs": ["run_x"]}
    assert "[D-20261008-001]" in md.read_text() and d.legacy_from_markdown(md.read_text()) == []
    with pytest.raises(ValueError, match="schema"):
        d.add(actor="CEO", kind="vibes", scope="", title="t", decision="x", log=log, md=None, now=now)


def test_committed_decision_files_match_their_schemas():
    for r in d.load(d.LOG):
        assert not d.validate(r), r["id"]
    legacy = d.load(d.LEGACY)
    assert legacy and all(not d.validate(r, d.LEGACY_SCHEMA) for r in legacy)
    ids = {r["id"] for r in legacy}
    for r in d.load(d.LOG):  # a structured restatement points at real legacy entries
        assert set(r["supersedes"]) <= ids | {x["id"] for x in d.load(d.LOG)}
