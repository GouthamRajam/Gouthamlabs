"""sby_formal: SymbiYosys. Parses PASS/FAIL per property and the counterexample VCD.

Per-property results come from sby's JUnit file (<task>/<task>.xml); the overall
verdict comes from sby's "DONE (STATUS, rc=N)" line.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

_DONE = re.compile(r"DONE \((?P<status>[A-Z]+), rc=(?P<rc>\d+)\)")
_CEX = re.compile(r"summary: counterexample trace(?: \[(?P<kind>\w+)\])?: (?P<path>\S+)")
_FAILED = re.compile(r"failed assertion (?P<name>\S+) at (?P<file>[^:\s]+):(?P<line>\d+)\.\d+-\S+ in step (?P<step>\d+)")
_ENGINE_ERROR = re.compile(r"\] ERROR: (?P<msg>.*)$")


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker=False)
    done = None
    for m in _DONE.finditer(log):
        done = m
    status = done["status"] if done else None
    out.success_marker = done is not None

    properties: list[dict] = []
    xml = reports.get("junit", "")
    if xml.strip():
        for case in ET.fromstring(xml).iter("testcase"):
            if case.get("type") is None:  # "build execution" pseudo-case
                continue
            failure = case.find("failure")
            properties.append({
                "name": case.get("id") or case.get("name"),
                "type": case.get("type"),
                "location": case.get("location"),
                "result": "FAIL" if failure is not None else ("PASS" if status == "PASS" else status),
                "trace": case.get("tracefile"),
            })

    # The summary lists each trace, then the assertions it violates. A basecase/BMC trace is
    # a real counterexample from reset; an [induction] trace is only a k-induction artifact
    # (state may be unreachable), so it is reported separately and not counted as a bug
    # unless no real counterexample exists.
    traces: dict[str, list[str]] = {"cex": [], "induction": []}
    failed: dict[str, list[Issue]] = {"cex": [], "induction": []}
    kind = "cex"
    for line in log.splitlines():
        if m := _CEX.search(line):
            kind = "induction" if m["kind"] == "induction" else "cex"
            traces[kind].append(m["path"])
        elif m := _FAILED.search(line):
            if not any(i.rule == m["name"] for i in failed[kind]):
                failed[kind].append(Issue("error", f"assertion failed in step {m['step']}"
                                          + (" (induction)" if kind == "induction" else ""),
                                          m["file"], int(m["line"]), rule=m["name"]))
    out.errors.extend(failed["cex"] or failed["induction"])
    for line in log.splitlines():
        if m := _ENGINE_ERROR.search(line):
            out.errors.append(Issue("error", m["msg"], rule="sby_error"))
    if status and status != "PASS" and not out.errors:
        out.errors.append(Issue("error", f"sby finished with status {status}", rule=f"sby_{status.lower()}"))
    if status == "PASS" and not properties and reports.get("junit") is not None:
        out.stage_failures.append("sby reported PASS but listed no properties (nothing was checked)")

    out.metrics = {
        "status": status,
        "properties": properties,
        "proven": sum(1 for p in properties if p["result"] == "PASS"),
        "failed": sum(1 for p in properties if p["result"] == "FAIL"),
        "counterexample_vcd": traces["cex"],
        "induction_trace_vcd": traces["induction"],
    }
    return out


SPEC = ToolSpec(
    name="sby_formal",
    version_key="sby",
    parse=parse,
    failure_patterns=(r"\] ERROR", r"DONE \((FAIL|ERROR|UNKNOWN|TIMEOUT)", r"not found in path"),
    safety_reports=(),  # the JUnit file embeds the raw log again
)


def run_sby_formal(sby_file: Path, workdir: Path, timeout_s: float = 1800) -> ToolResult:
    sby_file = Path(sby_file).resolve()
    task = sby_file.stem
    cmd = ["sby", "-f", sby_file.name]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"sby_{task}.log", SPEC.version_key,
                         timeout_s, cwd=sby_file.parent)
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec, {"junit": sby_file.parent / task / f"{task}.xml"})
