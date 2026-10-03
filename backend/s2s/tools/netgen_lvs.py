"""netgen_lvs: Netgen LVS, layout (extracted SPICE) vs schematic (powered Verilog netlist).

Script follows OpenLane 2's LVS step: standard-cell SPICE models are read into the
schematic circuit before the Verilog netlist, then `lvs ... -blackbox -json`, using the
PDK's own Netgen setup file. Parses the final verdict, device/net counts and mismatches.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

SETUP = "/opt/pdk/sky130A/libs.tech/netgen/sky130A_setup.tcl"
HD_SPICE_DIR = "/opt/pdk/sky130A/libs.ref/sky130_fd_sc_hd/spice"
HD_SPICE = [f"{HD_SPICE_DIR}/{n}.spice" for n in (
    "sky130_ef_sc_hd__decap_12", "sky130_ef_sc_hd__fill_12", "sky130_ef_sc_hd__fill_4",
    "sky130_ef_sc_hd__fill_8", "sky130_fd_sc_hd")]

_TCL = r"""
set circuit1 [readnet spice {layout}]
set circuit2 [readnet verilog /dev/null]
{read_cells}
readnet verilog {netlist} $circuit2
lvs "$circuit1 {top}" "$circuit2 {top}" {setup} {report} -blackbox -json
puts "S2S_LVS_DONE"
"""

_FINAL = re.compile(r"^Final result:\s*(?P<v>.*?)\.?\s*$", re.M)
_COUNT = re.compile(r"^Number of (?P<what>devices|nets): (?P<a>\d+)(?P<amm>\s+\*\*Mismatch\*\*)?\s*\|"
                    r"Number of \w+: (?P<b>\d+)(?P<bmm>\s+\*\*Mismatch\*\*)?", re.M)


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker="S2S_LVS_DONE" in log)
    rpt = reports.get("report", "")
    finals = [m["v"].strip() for m in _FINAL.finditer(rpt)]
    verdict = finals[-1] if finals else None
    match = verdict is not None and verdict.startswith("Circuits match uniquely")

    counts = {}
    for m in _COUNT.finditer(rpt):
        counts[m["what"]] = {"layout": int(m["a"]), "schematic": int(m["b"])}  # last (top cell) wins
    mismatch_lines = [l.strip() for l in rpt.splitlines()
                      if "**Mismatch**" in l or l.startswith(("Netlists do not match", "Top level cell failed"))]

    js = reports.get("json", "")
    unmatched = {}
    if js.strip():
        data = json.loads(js)
        top = data[-1] if isinstance(data, list) and data else {}
        for key in ("devices", "nets", "pins", "properties"):
            if isinstance(top.get(key), list) and len(top[key]) == 2:
                a, b = top[key]
                if isinstance(a, int) and isinstance(b, int) and a != b:
                    unmatched[key] = {"layout": a, "schematic": b}
        if top.get("badnets"):
            unmatched["badnets"] = len(top["badnets"])
        if top.get("badelements"):
            unmatched["badelements"] = len(top["badelements"])

    if verdict is None:
        out.stage_failures.append("LVS report has no 'Final result' line")
        out.success_marker = False if out.success_marker else out.success_marker
    elif not match:
        out.errors.append(Issue("error", f"LVS: {verdict}", rule="lvs_mismatch"))
        for line in mismatch_lines[:20]:
            out.errors.append(Issue("error", line, rule="lvs_detail"))
    out.metrics = {"verdict": verdict, "lvs_status": "match" if match else ("mismatch" if verdict else None),
                   "counts": counts, "unmatched": unmatched, "mismatch_lines": len(mismatch_lines)}
    return out


SPEC = ToolSpec(
    name="netgen_lvs",
    version_key="netgen",
    parse=parse,
    failure_patterns=(r"do not match", r"\*\*Mismatch\*\*", r"failed pin matching", r"(?m)^Error"),
    safety_reports=("report",),
)


def run_netgen_lvs(
    layout_spice: Path, netlist: Path, top: str, workdir: Path,
    cell_spice: list[str] | None = None, timeout_s: float = 3600,
) -> ToolResult:
    report = workdir.resolve() / "reports" / f"lvs_{top}.rpt"
    report.parent.mkdir(parents=True, exist_ok=True)
    for stale in (report, report.with_suffix(".json")):
        if stale.exists():
            stale.unlink()
    read_cells = "\n".join(f"readnet spice {s} $circuit2" for s in (cell_spice or HD_SPICE))
    script = workdir.resolve() / ".s2s" / f"lvs_{top}.tcl"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(_TCL.format(layout=Path(layout_spice).resolve(), read_cells=read_cells,
                                  netlist=Path(netlist).resolve(), top=top, setup=SETUP, report=report))
    cmd = ["netgen", "-batch", "source", str(script)]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"lvs_{top}.log", SPEC.version_key, timeout_s)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec, {"report": report, "json": report.with_suffix(".json")})
