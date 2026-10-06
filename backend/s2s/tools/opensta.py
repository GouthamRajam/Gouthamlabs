"""opensta: OpenSTA timing for one corner. Parses WNS/TNS, worst paths and violations.

One call = one corner (liberty set + optional SPEF). Stage rules: setup and hold worst
slack must be >= 0, and no max slew / max capacitance / max fanout violators.
"""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

SKY130_HD_LIB = "/opt/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__{corner}.lib"

_TCL = r"""
{read_libs}
read_verilog {netlist}
link_design {top}
read_sdc {sdc}
{post_route}
{read_spef}
puts "S2S_STA_CORNER {corner}"
report_checks -path_delay max -group_count {paths} -digits 4
report_checks -path_delay min -group_count {paths} -digits 4
puts "S2S_SETUP_WORST [sta::format_time [sta::worst_slack_cmd max] 4]"
puts "S2S_HOLD_WORST [sta::format_time [sta::worst_slack_cmd min] 4]"
puts "S2S_SETUP_TNS [sta::format_time [sta::total_negative_slack_cmd max] 4]"
puts "S2S_HOLD_TNS [sta::format_time [sta::total_negative_slack_cmd min] 4]"
puts "S2S_CHECK_TYPES_BEGIN"
report_check_types -max_slew -max_capacitance -max_fanout -violators
puts "S2S_CHECK_TYPES_END"
puts "S2S_STA_DONE"
"""

_NUM = r"(?P<v>-?\d+(?:\.\d+)?(?:e[-+]?\d+)?|INF|-INF)"
_SETUP = re.compile(r"^S2S_SETUP_WORST " + _NUM + r"\s*$", re.M)
_HOLD = re.compile(r"^S2S_HOLD_WORST " + _NUM + r"\s*$", re.M)
_SETUP_TNS = re.compile(r"^S2S_SETUP_TNS " + _NUM + r"\s*$", re.M)
_HOLD_TNS = re.compile(r"^S2S_HOLD_TNS " + _NUM + r"\s*$", re.M)
_CORNER = re.compile(r"^S2S_STA_CORNER (?P<c>\S+)", re.M)
_PATH = re.compile(
    r"^Startpoint: (?P<start>\S+).*?^Endpoint: (?P<end>\S+).*?^Path Type: (?P<type>\w+).*?"
    r"^\s*(?P<slack>-?\d+\.\d+)\s+slack \((?P<state>MET|VIOLATED)\)", re.M | re.S)
_ERROR = re.compile(r"^Error:?\s*(?P<msg>.*)$", re.M)
_WARNING = re.compile(r"^Warning:?\s*(?P<msg>.*)$", re.M)
_VIOLATOR_SECTION = re.compile(r"^(?P<kind>max slew|max capacitance|max fanout)\b", re.I | re.M)
_VIOLATOR_PIN = re.compile(r"^(?P<pin>\S+)\s+(?P<limit>-?[\d.]+)\s+(?P<value>-?[\d.]+)(?:\s+-?[\d.]+)?\s+\(VIOLATED\)", re.M)


def violator_pins(block: str) -> list[dict]:
    """report_check_types -violators rows: [{kind, pin, limit, value}] (OpenSTA prints Pin Limit Value Slack)."""
    rows, kind = [], None
    for line in block.splitlines():
        k = _VIOLATOR_SECTION.match(line.strip())
        if k:
            kind = k["kind"].lower()
            continue
        m = _VIOLATOR_PIN.match(line.strip())
        if m and kind:
            rows.append({"kind": kind, "pin": m["pin"], "limit": float(m["limit"]), "value": float(m["value"])})
    return rows


def _num(m: re.Match | None) -> float | None:
    if not m:
        return None
    v = m["v"]
    return float("inf") if v == "INF" else float("-inf") if v == "-INF" else float(v)


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker="S2S_STA_DONE" in log)
    for m in _ERROR.finditer(log):
        out.errors.append(Issue("error", m["msg"].strip(), rule="sta_error"))
    for m in _WARNING.finditer(log):
        out.warnings.append(Issue("warning", m["msg"].strip()))

    paths = [{"startpoint": m["start"], "endpoint": m["end"], "type": m["type"],
              "slack": float(m["slack"]), "state": m["state"]} for m in _PATH.finditer(log)]
    for p in paths:
        if p["state"] == "VIOLATED":
            kind = "setup" if p["type"] == "max" else "hold"
            out.errors.append(Issue("error", f"{kind} violation {p['startpoint']} -> {p['endpoint']}: "
                                    f"slack {p['slack']} ns", rule=f"{kind}_violation"))
    setup = _num(_SETUP.search(log))
    hold = _num(_HOLD.search(log))
    block = log.split("S2S_CHECK_TYPES_BEGIN", 1)[-1].split("S2S_CHECK_TYPES_END", 1)[0] \
        if "S2S_CHECK_TYPES_BEGIN" in log else ""
    violator_kinds = sorted({m["kind"].lower() for m in _VIOLATOR_SECTION.finditer(block)})

    if setup is None or hold is None:
        out.stage_failures.append("worst slack not reported")
    if setup is not None and setup < 0:
        out.stage_failures.append(f"setup worst slack {setup:.4f} ns (negative)")
    if hold is not None and hold < 0:
        out.stage_failures.append(f"hold worst slack {hold:.4f} ns (negative)")
    if violator_kinds:
        out.stage_failures.append(f"design rule violators: {', '.join(violator_kinds)}")

    corner = _CORNER.search(log)
    out.metrics = {
        "corner": corner["c"] if corner else None,
        "wns": min(setup, 0.0) if setup is not None else None,
        "setup_worst_slack": setup,
        "tns": _num(_SETUP_TNS.search(log)),
        "hold_worst_slack": hold,
        "hold_tns": _num(_HOLD_TNS.search(log)),
        "violated_paths_reported": sum(1 for p in paths if p["state"] == "VIOLATED"),
        "worst_paths": paths,
        "drv_violators": violator_kinds,
        "drv_violator_pins": violator_pins(block),
    }
    return out


SPEC = ToolSpec(
    name="opensta",
    version_key="opensta",
    parse=parse,
    failure_patterns=(r"(?m)^Error", r"VIOLATED", r"cannot open"),
)


def run_opensta(
    netlist: Path, sdc: Path, top: str, workdir: Path, corner: str = "tt_025C_1v80",
    liberty: list[Path] | None = None, spef: Path | None = None, paths: int = 5,
    timeout_s: float = 1800, post_route: bool = False, tag: str | None = None,
) -> ToolResult:
    """post_route: the clock tree exists, so clock latencies are propagated through it."""
    libs = [str(Path(p).resolve()) for p in liberty] if liberty else [SKY130_HD_LIB.format(corner=corner)]
    name = f"sta_{top}_{tag or corner}"
    script = workdir.resolve() / ".s2s" / f"{name}.tcl"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(_TCL.format(
        read_libs="\n".join(f"read_liberty {lib}" for lib in libs),
        netlist=Path(netlist).resolve(), top=top, sdc=Path(sdc).resolve(),
        read_spef=f"read_spef {Path(spef).resolve()}" if spef else "", corner=tag or corner, paths=paths,
        post_route="set_propagated_clock [all_clocks]" if post_route else ""))
    cmd = ["sta", "-no_init", "-exit", str(script)]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"{name}.log", SPEC.version_key,
                         timeout_s)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec)
