"""magic_drc: Magic DRC on a GDS (SKY130 full DRC style). Parses violation count by rule.

The Tcl script mirrors OpenLane's Magic DRC step (gds read; drc euclidean on;
drc style drc(full); drc check; drc listall why) and prints one machine-readable line
per rule plus a total. PDK rules come from the PDK's magicrc/tech file inside the image.
"""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

MAGICRC = "/opt/pdk/sky130A/libs.tech/magic/sky130A.magicrc"

_TCL = r"""
gds noduplicates true
gds read {gds}
load {top}
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
set total 0
foreach {{why boxes}} [drc listall why] {{
    set n [llength $boxes]
    set total [expr {{$total + $n}}]
    puts stdout "S2S_DRC_RULE\t$n\t$why"
}}
puts stdout "S2S_DRC_COUNT $total"
puts stdout "S2S_DRC_DONE"
flush stdout
quit -noprompt
"""

_RULE = re.compile(r"^S2S_DRC_RULE\t(?P<n>\d+)\t(?P<why>.*)$", re.M)
_COUNT = re.compile(r"^S2S_DRC_COUNT (?P<n>\d+)$", re.M)


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker="S2S_DRC_DONE" in log)
    by_rule: dict[str, int] = {}
    for m in _RULE.finditer(log):
        by_rule[m["why"]] = by_rule.get(m["why"], 0) + int(m["n"])
        out.errors.append(Issue("error", f"{m['n']} x {m['why']}", rule=m["why"]))
    count = _COUNT.search(log)
    total = int(count["n"]) if count else None
    if count is None:
        out.success_marker = False
    elif total != sum(by_rule.values()):
        out.stage_failures.append(f"DRC total {total} != sum of per-rule counts {sum(by_rule.values())}")
    if total:
        out.stage_failures.append(f"{total} Magic DRC violation(s)")
    out.metrics = {"drc_violations": total, "by_rule": by_rule}
    return out


SPEC = ToolSpec(
    name="magic_drc",
    version_key="magic",
    parse=parse,
    failure_patterns=(r"(?i)^error\b", r"(?m)^Error", r"[Cc]ouldn't", r"S2S_DRC_RULE"),
)


def run_magic_drc(gds: Path, top: str, workdir: Path, timeout_s: float = 3600) -> ToolResult:
    gds = Path(gds).resolve()
    script = workdir.resolve() / ".s2s" / f"magic_drc_{top}.tcl"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(_TCL.format(gds=gds, top=top))
    cmd = ["magic", "-dnull", "-noconsole", "-rcfile", MAGICRC, str(script)]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"magic_drc_{top}.log", SPEC.version_key,
                         timeout_s)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec)
