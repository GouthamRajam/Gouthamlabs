"""openlane_flow: OpenLane 2 flow (Classic by default; steps selectable with from/to/skip).

Parses per-step status from the run's flow.log, final metrics (WNS/TNS, DRC counts, LVS
status, antenna) from final/metrics.json (or the last step's state when the flow stopped
early), and ERROR records from the console log.

Stage rules (signoff): DRC (Magic, KLayout, routing) must be 0, LVS errors 0, worst
setup and hold slack must be >= 0. A metric that was never produced is a failure, not
a pass.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

PDK_ROOT = "/opt/pdk"

# Console records: "[08:11:51] ERROR    The following error was ...   __main__.py:187"
_RECORD = re.compile(r"^\[\d\d:\d\d:\d\d\] (?P<lvl>ERROR|CRITICAL|WARNING|INFO|VERBOSE|DEBUG)\s+(?P<msg>.*)$")
_SRC_REF = re.compile(r"\s+\S+\.py:\d+\s*$")
_RUNNING = re.compile(r"^Running '(?P<step>[^']+)' at '(?P<dir>[^']+)'")
_STEP_FAIL = re.compile(r"(violations found in the following corners|errors found|[Ff]ailed|mismatch)")

_KEYS = {
    "wns": "timing__setup__ws",
    "tns": "timing__setup__tns",
    "setup_violations": "timing__setup_vio__count",
    "hold_wns": "timing__hold__ws",
    "hold_violations": "timing__hold_vio__count",
    "magic_drc": "magic__drc_error__count",
    "klayout_drc": "klayout__drc_error__count",
    "route_drc": "route__drc_errors",
    "lvs_errors": "design__lvs_error__count",
    "antenna_violating_nets": "antenna__violating__nets",
    "instance_count": "design__instance__count",
    "die_area": "design__die__area",
}


def _records(log: str) -> list[tuple[str, str]]:
    """Join rich's wrapped console lines back into (level, message) records."""
    recs: list[list[str]] = []
    current: list[str] | None = None
    for raw in log.splitlines():
        if m := _RECORD.match(raw):
            current = [m["lvl"], _SRC_REF.sub("", m["msg"]).strip()]
            recs.append(current)
        elif current is not None and raw.startswith(" " * 11) and raw.strip():
            current[1] += " " + _SRC_REF.sub("", raw).strip()
        else:
            current = None
    return [(lvl, msg) for lvl, msg in recs]


def _steps(flow_log: str) -> list[dict]:
    steps: list[dict] = []
    for line in flow_log.splitlines():
        if m := _RUNNING.match(line):
            steps.append({"step": m["step"], "dir": m["dir"], "status": "ran", "notes": []})
        elif steps and line.strip():
            steps[-1]["notes"].append(line.strip())
    for s in steps:
        if s["step"].startswith("Checker.") and any(_STEP_FAIL.search(n) for n in s["notes"]):
            s["status"] = "failed"
        s["notes"] = s["notes"][:5]
    return steps


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    flow_log = reports.get("flow_log", "")
    out = ParsedLog(success_marker="Flow complete." in flow_log)
    for lvl, msg in _records(log):
        if lvl in ("ERROR", "CRITICAL"):
            out.errors.append(Issue("error", msg, rule="openlane"))
        elif lvl == "WARNING":
            out.warnings.append(Issue("warning", msg, rule="openlane"))

    steps = _steps(flow_log)
    for s in steps:
        if s["status"] == "failed":
            out.stage_failures.append(f"{s['step']}: {' '.join(s['notes'])[:300]}")

    raw: dict = {}
    if reports.get("metrics", "").strip():
        data = json.loads(reports["metrics"])
        raw = data.get("metrics", data)  # state_out.json nests them under "metrics"
    m = {k: raw.get(v) for k, v in _KEYS.items()}
    lvs = m["lvs_errors"]
    m["lvs_status"] = None if lvs is None else ("match" if lvs == 0 else "mismatch")
    m["metrics_source"] = reports.get("metrics_source")
    m["steps"] = [{"step": s["step"], "status": s["status"]} for s in steps]
    m["steps_run"] = len(steps)
    out.metrics = m

    if not raw:
        out.stage_failures.append("no metrics produced")
    else:
        for key in ("magic_drc", "klayout_drc", "route_drc"):
            if m[key] is None:
                out.stage_failures.append(f"{key} not reported")
            elif m[key] != 0:
                out.stage_failures.append(f"{key} = {m[key]} (must be 0)")
        if lvs is None:
            out.stage_failures.append("LVS not reported")
        elif lvs != 0:
            out.stage_failures.append(f"LVS errors = {lvs} (must be 0)")
        for key in ("wns", "hold_wns"):
            if m[key] is None:
                out.stage_failures.append(f"{key} not reported")
            elif m[key] < 0:
                out.stage_failures.append(f"{key} = {m[key]:.4f} ns (negative slack)")
    return out


SPEC = ToolSpec(
    name="openlane_flow",
    version_key="openlane",
    parse=parse,
    failure_patterns=(
        r"\] ERROR\b",
        r"\] CRITICAL\b",
        r"deferred errors",
        r"violations found in the following corners",
        r"OpenLane will now quit",
    ),
    safety_reports=("flow_log", "error_log"),
)


def run_openlane_flow(
    config: Path, workdir: Path, run_tag: str = "s2s", flow: str | None = None,
    from_step: str | None = None, to_step: str | None = None, skip: list[str] | None = None,
    pdk: str = "sky130A", scl: str = "sky130_fd_sc_hd", jobs: int = 4, timeout_s: float = 7200,
) -> ToolResult:
    config = Path(config).resolve()
    run_dir = config.parent / "runs" / run_tag
    cmd = ["openlane", "--manual-pdk", "--pdk-root", PDK_ROOT, "--pdk", pdk, "--scl", scl,
           "--run-tag", run_tag, "--overwrite", "--log-level", "VERBOSE", "-j", str(jobs)]
    if flow:
        cmd += ["--flow", flow]
    if from_step:
        cmd += ["--from", from_step]
    if to_step:
        cmd += ["--to", to_step]
    for s in skip or []:
        cmd += ["--skip", s]
    cmd.append(config.name)
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"openlane_{run_tag}.log", SPEC.version_key,
                         timeout_s, cwd=config.parent, env={"COLUMNS": "200"})
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)

    metrics = run_dir / "final" / "metrics.json"
    source = "final/metrics.json"
    if not metrics.exists():
        states = sorted(run_dir.glob("*/state_out.json"))
        if states:
            metrics = states[-1]
            source = f"{metrics.parent.name}/state_out.json (flow did not finish)"
    result = finish(SPEC, rec, {"flow_log": run_dir / "flow.log", "error_log": run_dir / "error.log",
                                "metrics": metrics})
    result.metrics["metrics_source"] = source if metrics.exists() else None
    result.metrics["run_dir"] = str(run_dir)
    result.metrics["gds"] = str(run_dir / "final" / "gds" / f"{_design_name(run_dir)}.gds")
    return result


def _design_name(run_dir: Path) -> str:
    try:
        return json.loads((run_dir / "resolved.json").read_text())["DESIGN_NAME"]
    except (OSError, KeyError, ValueError):
        return "design"
