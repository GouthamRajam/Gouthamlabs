"""Tests for the trajectory validator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from s2s.records.validate import validate


def _write(tmp_path: Path, recs: list[dict]) -> Path:
    p = tmp_path / "test.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in recs))
    return p


def _header(**kw):
    base = {"kind": "run", "trajectory_schema": 1, "seq": 0, "ts": "2026-10-04T00:00:00+00:00",
            "id": "run_TEST", "run_id": "run_TEST", "design": "test", "status": "completed",
            "autonomy": "autonomous", "operator_influence": [], "labels": [],
            "counts": {"events": 1, "heartbeats_omitted": 0, "model_calls": 0, "checks": 0, "tasks": 0}}
    base.update(kw)
    return base


def _outcome(**kw):
    base = {"kind": "outcome", "seq": 1, "ts": "2026-10-04T01:00:00+00:00", "id": "outcome:run_TEST",
            "run_id": "run_TEST", "verdict": "pass", "run_status": "completed",
            "checks_total": 0, "checks_failing_last": [], "gates": [], "labels": []}
    base.update(kw)
    return base


def test_minimal_valid(tmp_path):
    grade, findings = validate(_write(tmp_path, [_header(), _outcome()]))
    assert grade == "training-grade"
    assert not any(f.level == "error" for f in findings)


def test_empty_file(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    grade, _ = validate(p)
    assert grade == "error"


def test_missing_outcome(tmp_path):
    grade, findings = validate(_write(tmp_path, [_header()]))
    assert grade == "incomplete"
    assert any("not kind=outcome" in f.message for f in findings)


def test_bad_seq(tmp_path):
    h = _header()
    o = _outcome(seq=5)
    grade, findings = validate(_write(tmp_path, [h, o]))
    assert any("seq" in f.message for f in findings)


def test_unrecorded_provenance_downgrades(tmp_path):
    mc = {"kind": "model_call", "seq": 1, "ts": "2026-10-04T00:30:00+00:00", "id": "mc:1",
          "run_id": "run_TEST", "labels": [],
          "model_call": {"schema": 1, "alignment": "by_order", "prompt": "hello", "answer": "world",
                         "answered_by": "unrecorded"}}
    o = _outcome(seq=2)
    grade, findings = validate(_write(tmp_path, [_header(), mc, o]))
    assert grade == "usable"
    assert any("unrecorded provenance" in f.message for f in findings)


def test_autonomy_mismatch(tmp_path):
    h = _header(autonomy="autonomous", operator_influence=["reason"])
    grade, findings = validate(_write(tmp_path, [h, _outcome()]))
    assert grade == "incomplete"
    assert any("autonomous but influence" in f.message for f in findings)
