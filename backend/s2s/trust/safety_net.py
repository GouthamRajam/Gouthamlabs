"""Parser double-check / failure-string safety net (MASTER_SPEC Part 8.2, mechanism 2).

A check passes ONLY if all of these hold:
  1. the tool exited with code 0 and did not time out,
  2. the parser counted 0 errors and found no stage-rule failures,
  3. no known failure string appears anywhere in the tool's log,
  4. the tool's success marker is present (when the tool prints one).

Rule 3 is the defense against parser bugs: if a log contains an error string that the
parser did not count, the check FAILS. There is no allow-list or waiver mechanism here
by design (project rules); a pattern that misfires on a genuinely clean log must be
made more precise, never suppressed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from s2s.tools.result import FAIL, PASS, TIMEOUT, ParsedLog

# Failure strings that mean "something went wrong" for any tool.
COMMON_FAILURE_PATTERNS: tuple[str, ...] = (
    r"Segmentation fault",
    r"core dumped",
    r"Traceback \(most recent call last\)",
    r"command not found",
    r"No such file or directory",
    r"std::bad_alloc",
    r"[Oo]ut of memory",
    r"(?m)^Killed\b",
    r"\bFATAL\b",
    r"[Ii]nternal [Ee]rror",
)

MAX_HITS_REPORTED = 20


@dataclass
class Decision:
    passed: bool
    status: str
    reasons: list[str]
    hits: list[str]


def scan(log_text: str, patterns: tuple[str, ...] | list[str]) -> list[str]:
    """Return every log line that matches any failure pattern (deduplicated, in order)."""
    compiled = [re.compile(p) for p in (*COMMON_FAILURE_PATTERNS, *patterns)]
    hits: list[str] = []
    for line in log_text.splitlines():
        if any(rx.search(line) for rx in compiled) and line.strip() not in hits:
            hits.append(line.strip())
    return hits


def decide(
    exit_code: int | None,
    timed_out: bool,
    parsed: ParsedLog,
    log_text: str,
    failure_patterns: tuple[str, ...] | list[str] = (),
) -> Decision:
    reasons: list[str] = []
    if timed_out:
        reasons.append("tool timed out")
    if exit_code is None:
        reasons.append("tool did not produce an exit code")
    elif exit_code != 0:
        reasons.append(f"tool exit code {exit_code} (must be 0)")
    if parsed.error_count:
        reasons.append(f"parser counted {parsed.error_count} error(s)")
    reasons.extend(f"stage rule: {f}" for f in parsed.stage_failures)
    if parsed.success_marker is False:
        reasons.append("tool's success marker not found in its output (incomplete or crashed run)")

    hits = scan(log_text, failure_patterns)
    if hits:
        if parsed.error_count == 0:
            reasons.append(
                f"safety net: {len(hits)} log line(s) contain known failure strings that the "
                f"parser did not count, e.g. {hits[0]!r}"
            )
        else:
            reasons.append(f"safety net: {len(hits)} log line(s) contain known failure strings")

    if timed_out:
        status = TIMEOUT
    else:
        status = FAIL if reasons else PASS
    return Decision(passed=not reasons, status=status, reasons=reasons, hits=hits[:MAX_HITS_REPORTED])
