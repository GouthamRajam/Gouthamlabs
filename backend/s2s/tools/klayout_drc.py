"""klayout_drc: KLayout SKY130 DRC deck on a GDS. Parses violation count by rule.

Uses the PDK's own deck (sky130A_mr.drc) with the same options OpenLane 2 uses for
signoff, and reads the result database (.lyrdb XML) KLayout writes.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

DECK = "/opt/pdk/sky130A/libs.tech/klayout/drc/sky130A_mr.drc"
DEFAULT_OPTIONS = {"feol": "true", "beol": "true", "floating_metal": "false", "offgrid": "true",
                   "seal": "true"}


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker="Writing report database" in log)
    xml = reports.get("lyrdb", "")
    by_rule: dict[str, int] = {}
    if not xml.strip():
        out.stage_failures.append("KLayout DRC report database missing or empty")
        out.metrics = {"drc_violations": None, "by_rule": {}}
        return out
    root = ET.fromstring(xml)
    descriptions = {c.findtext("name"): (c.findtext("description") or "")
                    for c in root.iter("category") if c.findtext("name")}
    for item in root.iter("item"):
        rule = (item.findtext("category") or "?").strip("'")
        by_rule[rule] = by_rule.get(rule, 0) + 1
    for rule, n in sorted(by_rule.items()):
        desc = descriptions.get(rule) or descriptions.get(f"'{rule}'") or ""
        out.errors.append(Issue("error", f"{n} x {rule}: {desc}".strip(": "), rule=rule))
    total = sum(by_rule.values())
    if total:
        out.stage_failures.append(f"{total} KLayout DRC violation(s)")
    out.metrics = {"drc_violations": total, "by_rule": by_rule}
    return out


SPEC = ToolSpec(
    name="klayout_drc",
    version_key="klayout",
    parse=parse,
    failure_patterns=(r"(?m)^ERROR", r"(?m)^\*\*\* ERROR", r"in Executable::execute"),
    safety_reports=(),  # the lyrdb is structured data, parsed for violations directly
)


def run_klayout_drc(
    gds: Path, top: str, workdir: Path, threads: int = 4, timeout_s: float = 3600,
    options: dict[str, str] | None = None,
) -> ToolResult:
    gds = Path(gds).resolve()
    report = workdir.resolve() / "reports" / f"klayout_drc_{top}.lyrdb"
    report.parent.mkdir(parents=True, exist_ok=True)
    if report.exists():
        report.unlink()  # never read a stale report
    opts = {**DEFAULT_OPTIONS, **(options or {}), "input": str(gds), "topcell": top,
            "report": str(report), "threads": str(threads)}
    cmd = ["klayout", "-b", "-zz", "-r", DECK]
    for key, value in opts.items():
        cmd += ["-rd", f"{key}={value}"]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"klayout_drc_{top}.log", SPEC.version_key,
                         timeout_s)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec, {"lyrdb": report})
