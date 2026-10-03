"""verilator_lint: `verilator --lint-only -Wall`. Parses warnings/errors with file:line."""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

# %Warning-WIDTHTRUNC: width_mismatch.v:9:16: Operator ASSIGNW expects 8 bits ...
# %Error: syntax_error.v:7:1: syntax error, unexpected endmodule ...
# %Error: Exiting due to 2 warning(s)
_MSG = re.compile(
    r"^%(?P<sev>Error|Warning)(?:-(?P<rule>[A-Z0-9_]+))?:\s+"
    r"(?:(?P<file>[^\s:]+):(?P<line>\d+):(?:\d+:)?\s+)?(?P<msg>.*)$"
)


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker=None)  # verilator prints nothing on a clean lint
    for raw in log.splitlines():
        m = _MSG.match(raw.strip())
        if not m:
            continue
        issue = Issue(
            severity="error" if m["sev"] == "Error" else "warning",
            message=m["msg"].strip(),
            file=m["file"],
            line=int(m["line"]) if m["line"] else None,
            rule=m["rule"],
        )
        (out.errors if issue.severity == "error" else out.warnings).append(issue)
    if out.warnings:
        # -Wall: every lint warning is a defect in Phase 0 RTL (coding standard).
        out.stage_failures.append(f"{len(out.warnings)} lint warning(s) under -Wall")
    out.metrics = {"errors": out.error_count, "warnings": out.warning_count}
    return out


SPEC = ToolSpec(
    name="verilator_lint",
    version_key="verilator",
    parse=parse,
    failure_patterns=(r"(?m)^%Error",),
)


def run_verilator_lint(
    files: list[Path], top: str, workdir: Path, timeout_s: float = 300,
    extra_args: list[str] | None = None,
) -> ToolResult:
    cmd = ["verilator", "--lint-only", "-Wall", "--top-module", top,
           *(extra_args or []), *[str(Path(f).resolve()) for f in files]]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / "verilator_lint.log", SPEC.version_key,
                         timeout_s)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec)
