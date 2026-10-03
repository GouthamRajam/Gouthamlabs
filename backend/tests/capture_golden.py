"""Capture golden logs by running every adapter for real (needs docker + the s2s-eda image).

    cd backend && python -m tests.capture_golden            # all cases
    cd backend && python -m tests.capture_golden opensta    # cases whose id contains "opensta"

For each case it saves, under tests/golden/<tool>/<case>/:
  log.txt              the tool's raw combined stdout/stderr
  reports/<name>       every report file the parser read (name = parser's report key)
  meta.json            command, exit code, tool version, env hash, timestamp and the
                       live result (status, reasons, metrics)

A golden is only written if the real result matches the case's expectation (a "pass"
case really passed, a "fail_*" case really failed). Otherwise it stops with an error:
goldens record what the tools actually did, never what we hoped.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
from pathlib import Path

from tests.cases import CASES, GOLDEN

WORK_ROOT = Path("/tmp/s2s-golden-work")


def capture(case) -> dict:
    work = WORK_ROOT / case.tool / case.name
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    result = case.run(work)
    if result.passed != case.expect_pass:
        raise SystemExit(
            f"{case.id}: expected {'PASS' if case.expect_pass else 'FAIL'} but the real run gave "
            f"{result.status}: {result.reasons} (log: {result.log_path}). Golden NOT written.")

    out = GOLDEN / case.tool / case.name
    shutil.rmtree(out, ignore_errors=True)
    (out / "reports").mkdir(parents=True)
    shutil.copy2(result.log_path, out / "log.txt")
    for name, path in result.report_paths.items():
        shutil.copy2(path, out / "reports" / name)
    meta = {
        "tool": case.tool,
        "case": case.name,
        "expect": "pass" if case.expect_pass else "fail",
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "workdir": str(work),
        "command": result.command,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "tool_version": result.tool_version,
        "env_hash": result.env_hash,
        "duration_s": result.duration_s,
        "reports": sorted(result.report_paths),
        "live_result": {
            "status": result.status,
            "passed": result.passed,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "reasons": result.reasons,
            "metrics": result.metrics,
        },
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    return meta


def main(argv: list[str]) -> int:
    selected = [c for c in CASES if not argv or any(a in c.id for a in argv)]
    for case in selected:
        meta = capture(case)
        print(f"{case.id:40s} {meta['live_result']['status']:5s} exit={meta['exit_code']} "
              f"{meta['duration_s']}s  reasons={meta['live_result']['reasons']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
