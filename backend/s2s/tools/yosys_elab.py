"""yosys_elab: read, elaborate and check RTL with Yosys. Parses errors, latches, loops.

Script: read_verilog -sv <files>; hierarchy -check -top <top>; proc; check -assert
Stage rules: any inferred latch or logic loop fails (coding standard: no latches).
"""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

# "syntax_error.v:7: ERROR: syntax error, unexpected TOK_ENDMODULE"  /  "ERROR: Found 1 problems ..."
_ERROR = re.compile(r"^(?:(?P<file>[^\s:]+):(?P<line>\d+): )?ERROR: (?P<msg>.*)$")
_WARNING = re.compile(r"^Warning: (?P<msg>.*)$")
# "Latch inferred for signal `\latch.\q' from process `\latch.$proc$latch.v:7$1': ..."
_LATCH = re.compile(r"^Latch inferred for signal `(?P<sig>[^']+)' from process `[^$]*\$proc\$(?P<file>[^:]+):(?P<line>\d+)")
_LOOP = re.compile(r"^Warning: found logic loop in module (?P<mod>\S+?):?$")
_PROBLEMS = re.compile(r"^Found and reported (?P<n>\d+) problems\.")


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker=False)
    latches: list[Issue] = []
    loops: list[str] = []
    check_problems = None
    for raw in log.splitlines():
        line = raw.strip()
        if m := _ERROR.match(line):
            out.errors.append(Issue("error", m["msg"], m["file"], int(m["line"]) if m["line"] else None))
        elif m := _LOOP.match(line):
            loops.append(m["mod"])
            out.warnings.append(Issue("warning", m.group(0)[len("Warning: "):], rule="logic_loop"))
        elif m := _WARNING.match(line):
            out.warnings.append(Issue("warning", m["msg"]))
        if m := _LATCH.match(line):
            latches.append(Issue("warning", f"latch inferred for {m['sig']}", m["file"], int(m["line"]),
                                 rule="latch"))
        if m := _PROBLEMS.match(line):
            check_problems = int(m["n"])
        if line.startswith("End of script."):
            out.success_marker = True
    out.warnings.extend(latches)
    if latches:
        out.stage_failures.append(f"{len(latches)} latch(es) inferred: "
                                  + ", ".join(i.message.split()[-1] for i in latches))
    if loops:
        out.stage_failures.append(f"logic loop(s) in module(s): {', '.join(loops)}")
    out.metrics = {"latches": len(latches), "logic_loops": len(loops),
                   "check_problems": check_problems}
    return out


SPEC = ToolSpec(
    name="yosys_elab",
    version_key="yosys",
    parse=parse,
    failure_patterns=(r"ERROR:",),
)


def run_yosys_elab(files: list[Path], top: str, workdir: Path, timeout_s: float = 600) -> ToolResult:
    srcs = " ".join(str(Path(f).resolve()) for f in files)
    script = f"read_verilog -sv {srcs}; hierarchy -check -top {top}; proc; check -assert"
    cmd = ["yosys", "-p", script]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / "yosys_elab.log", SPEC.version_key, timeout_s)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec)
