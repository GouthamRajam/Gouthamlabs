"""Glue between the runner, a tool's parser and the Trust Layer's pass/fail decision.

Each tool module defines a ToolSpec (name, versions.lock key, parser, extra failure
strings) and calls `finish()` after running. Unit tests call `evaluate()` on golden logs,
which is exactly the decision path `finish()` uses for real runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from s2s.tools.result import ERROR, ParsedLog, ToolResult
from s2s.tools.runner import RunRecord
from s2s.trust.safety_net import decide

Parser = Callable[[str, dict[str, str]], ParsedLog]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    version_key: str  # key in eda/versions.lock
    parse: Parser  # (log_text, {report_name: report_text}) -> ParsedLog
    failure_patterns: tuple[str, ...] = ()
    # Reports the safety net scans together with the raw log (None = all of them). Reports
    # that merely embed the raw log again (e.g. sby's JUnit file) are left out.
    safety_reports: tuple[str, ...] | None = None


def read_text(path: Path | str | None) -> str:
    if path is None:
        return ""
    p = Path(path)
    return p.read_text(errors="replace") if p.is_file() else ""


def evaluate(
    spec: ToolSpec,
    exit_code: int | None,
    log_text: str,
    reports: dict[str, str] | None = None,
    timed_out: bool = False,
) -> ToolResult:
    """Parse and decide: the single pass/fail path for real runs and golden-log tests."""
    reports = reports or {}
    parsed = spec.parse(log_text, reports)
    names = reports.keys() if spec.safety_reports is None else spec.safety_reports
    safety_text = "\n".join([log_text, *(reports.get(n, "") for n in names)])
    d = decide(exit_code, timed_out, parsed, safety_text, spec.failure_patterns)
    return ToolResult(
        tool=spec.name,
        passed=d.passed,
        status=d.status,
        exit_code=exit_code,
        timed_out=timed_out,
        error_count=parsed.error_count,
        warning_count=parsed.warning_count,
        errors=parsed.errors,
        warnings=parsed.warnings,
        stage_failures=parsed.stage_failures,
        metrics=parsed.metrics,
        reasons=d.reasons,
        safety_net_hits=d.hits,
        log_path=None,
        report_paths={},
        command=[],
        tool_version=None,
        env_hash=None,
        duration_s=None,
    )


def finish(spec: ToolSpec, record: RunRecord, report_paths: dict[str, Path] | None = None) -> ToolResult:
    """Build the final ToolResult for a real run.

    `report_paths`: extra files the parser reads, keyed by the names the parser expects.
    A missing file is read as empty text (and the parser decides what that means).
    """
    report_paths = report_paths or {}
    log_text = read_text(record.log_path)
    reports = {k: read_text(p) for k, p in report_paths.items()}
    result = evaluate(spec, record.exit_code, log_text, reports, record.timed_out)
    result.log_path = str(record.log_path)
    result.report_paths = {k: str(p) for k, p in report_paths.items() if Path(p).exists()}
    result.command = record.command
    result.tool_version = record.tool_version
    result.env_hash = record.env_hash
    result.duration_s = record.duration_s
    return result


def unavailable(spec: ToolSpec, reason: str, command: list[str] | None = None) -> ToolResult:
    """Result when the tool could not be run at all. Never a pass."""
    return ToolResult(
        tool=spec.name, passed=False, status=ERROR, exit_code=None, timed_out=False,
        error_count=0, warning_count=0, errors=[], warnings=[], stage_failures=[], metrics={},
        reasons=[f"tool could not be run: {reason}"], safety_net_hits=[], log_path=None,
        report_paths={}, command=command or [], tool_version=None, env_hash=None, duration_s=None,
    )
