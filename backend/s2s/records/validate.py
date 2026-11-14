"""Trajectory validator: checks each exported run for schema completeness and training-grade quality.

    python -m s2s.records.validate <file.jsonl> [<file2.jsonl> ...]
    python -m s2s.records.validate --dir docs/trajectories/

Exits 0 if all files pass, 1 if any have gaps. Prints a per-file grade and a summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_HEADER_KEYS = {"kind", "trajectory_schema", "id", "run_id", "design", "status", "autonomy",
                        "operator_influence", "counts", "labels"}
REQUIRED_OUTCOME_KEYS = {"kind", "verdict", "run_status", "checks_total", "checks_failing_last", "gates"}
REQUIRED_RECORD_KEYS = {"kind", "seq", "ts", "id"}
VALID_KINDS = {"run", "task", "plan", "tool_call", "tool_result", "model_call", "check", "finding",
               "handoff", "escalation", "gate", "stage", "task_event", "stall", "budget", "artifact",
               "analysis", "decision", "outcome"}
REQUIRED_MODEL_CALL_KEYS = {"schema", "alignment", "prompt", "answer"}


class Finding:
    __slots__ = ("level", "message")

    def __init__(self, level: str, message: str):
        self.level = level
        self.message = message

    def __repr__(self) -> str:
        return f"[{self.level}] {self.message}"


def validate(path: Path) -> tuple[str, list[Finding]]:
    """Validate one trajectory file. Returns (grade, findings).
    Grade: 'training-grade', 'usable', or 'incomplete'.
    """
    findings: list[Finding] = []
    try:
        lines = path.read_text().splitlines()
    except OSError as e:
        return "error", [Finding("error", str(e))]

    if not lines:
        return "error", [Finding("error", "empty file")]

    recs = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError as e:
            findings.append(Finding("error", f"line {i + 1}: invalid JSON: {e}"))

    if not recs:
        return "error", findings + [Finding("error", "no valid records")]

    header = recs[0]
    if header.get("kind") != "run":
        findings.append(Finding("error", "first record is not kind=run"))

    missing_h = REQUIRED_HEADER_KEYS - set(header.keys())
    if missing_h:
        findings.append(Finding("error", f"header missing keys: {sorted(missing_h)}"))

    if header.get("trajectory_schema") != 1:
        findings.append(Finding("warn", f"unknown schema version: {header.get('trajectory_schema')}"))

    outcome = recs[-1] if recs[-1].get("kind") == "outcome" else None
    if outcome is None:
        findings.append(Finding("error", "last record is not kind=outcome"))
    else:
        missing_o = REQUIRED_OUTCOME_KEYS - set(outcome.keys())
        if missing_o:
            findings.append(Finding("error", f"outcome missing keys: {sorted(missing_o)}"))

    seqs = [r.get("seq") for r in recs]
    if seqs != list(range(len(recs))):
        findings.append(Finding("error", "seq is not a contiguous 0..N sequence"))

    for i, r in enumerate(recs):
        missing_r = REQUIRED_RECORD_KEYS - set(r.keys())
        if missing_r:
            findings.append(Finding("error", f"record {i} (kind={r.get('kind')}): missing {sorted(missing_r)}"))
            continue
        if r["kind"] not in VALID_KINDS:
            findings.append(Finding("warn", f"record {i}: unknown kind {r['kind']!r}"))
        if "labels" not in r:
            findings.append(Finding("warn", f"record {i} (kind={r['kind']}): no labels field"))

    model_calls = [r for r in recs if r.get("kind") == "model_call"]
    mc_total = len(model_calls)
    mc_no_prompt = 0
    mc_no_answer = 0
    mc_unrecorded = 0
    for mc in model_calls:
        detail = mc.get("model_call") or {}
        missing_mc = REQUIRED_MODEL_CALL_KEYS - set(detail.keys())
        if missing_mc:
            findings.append(Finding("warn", f"model_call {mc['id']}: missing {sorted(missing_mc)}"))
        if not detail.get("prompt"):
            mc_no_prompt += 1
        if not detail.get("answer"):
            mc_no_answer += 1
        ab = detail.get("answered_by")
        if ab in (None, "unrecorded"):
            mc_unrecorded += 1

    if mc_no_prompt:
        findings.append(Finding("warn", f"{mc_no_prompt}/{mc_total} model calls have no prompt"))
    if mc_no_answer:
        findings.append(Finding("warn", f"{mc_no_answer}/{mc_total} model calls have no answer"))
    if mc_unrecorded:
        findings.append(Finding("gap", f"{mc_unrecorded}/{mc_total} model calls have unrecorded provenance"))

    tasks = [r for r in recs if r.get("kind") == "task"]
    task_ids = {t["id"] for t in tasks}
    for r in recs:
        if r.get("kind") in ("tool_call", "tool_result", "plan", "model_call", "check"):
            if r.get("task_id") and r["task_id"] not in task_ids:
                findings.append(Finding("warn", f"record {r['seq']}: task_id {r['task_id']} has no task record"))

    ts_values = [r.get("ts") for r in recs if r.get("ts")]
    for i in range(1, len(ts_values)):
        if ts_values[i] < ts_values[i - 1]:
            findings.append(Finding("warn", f"timestamp out of order at position ~{i}"))
            break

    checks = [r for r in recs if r.get("kind") == "check"]
    for c in checks:
        if not c.get("check"):
            findings.append(Finding("warn", f"check record {c['id']} has no check detail"))

    autonomy = header.get("autonomy")
    influence = header.get("operator_influence", [])
    if autonomy == "operator_influenced" and not influence:
        findings.append(Finding("warn", "autonomy=operator_influenced but no influence reasons listed"))
    if autonomy == "autonomous" and influence:
        findings.append(Finding("error", "autonomy=autonomous but influence reasons present"))

    errors = sum(1 for f in findings if f.level == "error")
    gaps = sum(1 for f in findings if f.level == "gap")
    warns = sum(1 for f in findings if f.level == "warn")

    if errors > 0:
        grade = "incomplete"
    elif gaps > 0 or warns > 2:
        grade = "usable"
    else:
        grade = "training-grade"

    return grade, findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.records.validate",
                                 description="Validate trajectory exports for schema completeness")
    ap.add_argument("files", nargs="*", type=Path, help="trajectory .jsonl files")
    ap.add_argument("--dir", type=Path, help="directory of .jsonl files")
    a = ap.parse_args(argv)

    paths = list(a.files or [])
    if a.dir:
        paths += sorted(a.dir.glob("*.jsonl"))
    if not paths:
        print("no files to validate", file=sys.stderr)
        return 1

    grades = {"training-grade": 0, "usable": 0, "incomplete": 0, "error": 0}
    any_fail = False

    for p in paths:
        grade, findings = validate(p)
        grades[grade] = grades.get(grade, 0) + 1
        marker = {"training-grade": "+", "usable": "~", "incomplete": "-", "error": "!"}[grade]
        print(f"  [{marker}] {grade:15s}  {p.name}")
        for f in findings:
            if f.level in ("error", "gap"):
                print(f"        {f}")
        if grade in ("incomplete", "error"):
            any_fail = True

    print(f"\n  {len(paths)} files: {grades.get('training-grade', 0)} training-grade, "
          f"{grades.get('usable', 0)} usable, {grades.get('incomplete', 0)} incomplete, "
          f"{grades.get('error', 0)} error")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
