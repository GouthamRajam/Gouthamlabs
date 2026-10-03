"""eqy: Yosys equivalence checking. Parses proven / failed per partition."""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

_DONE = re.compile(r"DONE \((?P<status>[A-Z]+), rc=(?P<rc>\d+)\)")
_PROVED_ALL = "Successfully proved designs equivalent"
_PART_OK = re.compile(r"Successfully proved equivalence of partition (?P<p>\S+)")
_PART_BAD = re.compile(r"Failed to prove equivalence of partition (?P<p>\S+)")
_ERROR = re.compile(r"(?:^|\] )ERROR: (?P<msg>.*)$")


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog()
    done = None
    for m in _DONE.finditer(log):
        done = m
    status = done["status"] if done else None
    out.success_marker = done is not None
    proven = sorted({m["p"] for m in _PART_OK.finditer(log)})
    failed = sorted({m["p"] for m in _PART_BAD.finditer(log)})
    for p in failed:
        out.errors.append(Issue("error", f"partition {p} not proven equivalent", rule="not_equivalent"))
    for line in log.splitlines():
        if m := _ERROR.search(line.strip()):
            out.errors.append(Issue("error", m["msg"], rule="eqy_error"))
    if status == "PASS" and _PROVED_ALL not in log:
        out.stage_failures.append("eqy status PASS but no 'proved designs equivalent' statement")
    if status and status != "PASS" and not out.errors:
        out.errors.append(Issue("error", f"eqy finished with status {status}", rule=f"eqy_{status.lower()}"))
    out.metrics = {"status": status, "equivalent": status == "PASS" and _PROVED_ALL in log,
                   "partitions_proven": proven, "partitions_failed": failed}
    return out


SPEC = ToolSpec(
    name="eqy",
    version_key="eqy",
    parse=parse,
    failure_patterns=(r"ERROR", r"Failed to prove", r"DONE \((FAIL|ERROR|UNKNOWN|TIMEOUT)"),
)


def run_eqy(eqy_file: Path, workdir: Path, timeout_s: float = 1800) -> ToolResult:
    eqy_file = Path(eqy_file).resolve()
    cmd = ["eqy", "-f", eqy_file.name]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"eqy_{eqy_file.stem}.log", SPEC.version_key,
                         timeout_s, cwd=eqy_file.parent)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec)
