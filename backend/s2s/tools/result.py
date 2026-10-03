"""Structured results shared by every EDA tool adapter (MASTER_SPEC Part 7.5)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

PASS = "PASS"
FAIL = "FAIL"
TIMEOUT = "TIMEOUT"
ERROR = "ERROR"  # the tool could not be run at all (e.g. container/image missing)


@dataclass
class Issue:
    """One finding reported by a tool: an error, warning or stage-rule violation."""

    severity: str  # "error" | "warning"
    message: str
    file: str | None = None
    line: int | None = None
    rule: str | None = None  # tool's own code, e.g. WIDTHTRUNC or a DRC rule name


@dataclass
class ParsedLog:
    """What a parser extracted from a tool's log and report files.

    `errors` are the tool's own errors. `stage_failures` are stage-specific rules that
    fail the check even when the tool itself exits 0 (e.g. a latch was inferred, LVS did
    not match, setup slack is negative). `success_marker` is positive evidence that the
    tool ran to completion; None means the tool prints no such marker.
    """

    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    stage_failures: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    success_marker: bool | None = None

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


@dataclass
class ToolResult:
    """Outcome of one adapter call. `passed` is decided only by s2s.trust.safety_net."""

    tool: str
    passed: bool
    status: str  # PASS | FAIL | TIMEOUT | ERROR
    exit_code: int | None
    timed_out: bool
    error_count: int
    warning_count: int
    errors: list[Issue]
    warnings: list[Issue]
    stage_failures: list[str]
    metrics: dict[str, Any]
    reasons: list[str]  # why it failed; empty when passed
    safety_net_hits: list[str]  # log lines matching known failure strings
    log_path: str | None  # raw combined stdout/stderr of the tool
    report_paths: dict[str, str]  # extra report files the parser read
    command: list[str]
    tool_version: str | None
    env_hash: str | None
    duration_s: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
