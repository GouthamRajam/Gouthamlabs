"""cocotb_sim: cocotb runner with Verilator (Icarus secondary). Parses test pass/fail,
seed and (Verilator only) line coverage.

Pass/fail comes from cocotb's own JUnit results.xml and its "TESTS=.. PASS=.. FAIL=.."
summary; zero tests run is a failure.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.result import Issue, ParsedLog, ToolResult

COCOTB_PYTHON = "/opt/cocotb/bin/python3"

_SUMMARY = re.compile(r"\*\*\s+TESTS=(?P<t>\d+)\s+PASS=(?P<p>\d+)\s+FAIL=(?P<f>\d+)\s+SKIP=(?P<s>\d+)")
_SEED = re.compile(r"Seeding Python random module with (?:supplied seed )?(?P<seed>\d+)")
_TEST_LINE = re.compile(r"\*\*\s+(?P<name>\S+)\s+(?P<res>PASS|FAIL|SKIP)\b")
_COVERAGE = re.compile(r"^S2S_COVERAGE lines_hit=(?P<hit>\d+) lines_found=(?P<found>\d+)$", re.M)
_DONE = "S2S_COCOTB_DONE"


_EXC = re.compile(r"^\s*(?P<exc>\w*(?:Error|Exception)): (?P<msg>.*)$")


def _failure_detail(log: str, test_name: str) -> str | None:
    """The exception line cocotb logs after '<test> failed' (e.g. 'AssertionError: count=5')."""
    short = test_name.rsplit(".", 1)[-1]
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if line.rstrip().endswith(f"{short} failed"):
            for nxt in lines[i + 1:i + 40]:
                if "**" in nxt:
                    break
                if m := _EXC.match(nxt):
                    return f"{m['exc']}: {m['msg'].strip()}"
    return None


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker=_DONE in log)
    summary = None
    for m in _SUMMARY.finditer(log):
        summary = m  # last summary wins
    seed = _SEED.search(log)
    tests: dict[str, str] = {m["name"]: m["res"] for m in _TEST_LINE.finditer(log)
                             if not m["name"].startswith("TESTS=")}

    xml = reports.get("results_xml", "")
    xml_tests = xml_failures = 0
    if xml.strip():
        root = ET.fromstring(xml)
        for case in root.iter("testcase"):
            xml_tests += 1
            name = f"{case.get('classname', '')}.{case.get('name', '')}".strip(".")
            bad = case.find("failure")
            if bad is None:
                bad = case.find("error")
            if bad is not None:
                xml_failures += 1
                detail = _failure_detail(log, name) or bad.get("message") or bad.tag
                out.errors.append(Issue("error", f"test {name} failed: {detail}",
                                        case.get("file"), _int(case.get("lineno")), rule="test_failure"))
    elif summary and int(summary["f"]):
        # No results.xml (e.g. golden without it): fall back to the log's per-test lines.
        for name, res in tests.items():
            if res == "FAIL":
                detail = _failure_detail(log, name)
                out.errors.append(Issue("error", f"test {name} failed" + (f": {detail}" if detail else ""),
                                        rule="test_failure"))

    n_tests = int(summary["t"]) if summary else xml_tests
    n_fail = int(summary["f"]) if summary else xml_failures
    if n_tests == 0:
        out.stage_failures.append("no cocotb tests ran")
    if summary and xml.strip() and (xml_tests != n_tests or xml_failures != n_fail):
        out.stage_failures.append(
            f"results.xml ({xml_tests} tests, {xml_failures} failed) disagrees with log summary "
            f"({n_tests} tests, {n_fail} failed)")
    if summary is None:
        out.success_marker = False

    cov = _COVERAGE.search(log)
    out.metrics = {
        "tests": n_tests,
        "passed": int(summary["p"]) if summary else xml_tests - xml_failures,
        "failed": n_fail,
        "skipped": int(summary["s"]) if summary else 0,
        "seed": int(seed["seed"]) if seed else None,
        "tests_by_name": tests,
        "line_coverage": (round(int(cov["hit"]) / int(cov["found"]), 4)
                          if cov and int(cov["found"]) else None),
        "lines_hit": int(cov["hit"]) if cov else None,
        "lines_found": int(cov["found"]) if cov else None,
    }
    return out


def _int(v: str | None) -> int | None:
    return int(v) if v and v.isdigit() else None


SPEC = ToolSpec(
    name="cocotb_sim",
    version_key="cocotb",
    parse=parse,
    failure_patterns=(r"(?m)^%Error", r"\bERROR\b", r"FAIL=[1-9]"),
)

# Runs inside s2s-eda with cocotb's Python; arguments come from a JSON file.
_RUNNER = r'''
import json, subprocess, sys
from pathlib import Path
from cocotb.runner import get_runner
a = json.loads(Path(sys.argv[1]).read_text())
r = get_runner(a["simulator"])
build_args = ["--coverage-line"] if a["coverage"] else []
r.build(verilog_sources=a["sources"], hdl_toplevel=a["toplevel"], build_dir=a["build_dir"],
        timescale=("1ns", "1ps"), build_args=build_args, always=True)
r.test(hdl_toplevel=a["toplevel"], test_module=a["test_module"], build_dir=a["build_dir"],
       test_dir=a["test_dir"], seed=a["seed"], results_xml=a["results_xml"])
if a["coverage"]:
    info = Path(a["build_dir"]) / "coverage.info"
    subprocess.run(["verilator_coverage", "--write-info", str(info),
                    str(Path(a["test_dir"]) / "coverage.dat")], check=True)
    # lcov records: "DA:<line>,<hit count>" per instrumented line (no LF/LH totals emitted)
    lf = lh = 0
    for line in info.read_text().splitlines():
        if line.startswith("DA:"):
            lf += 1
            lh += int(line[3:].split(",")[1]) > 0
    print(f"S2S_COVERAGE lines_hit={lh} lines_found={lf}")
print("S2S_COCOTB_DONE")
'''


def run_cocotb_sim(
    sources: list[Path], toplevel: str, test_module: str, workdir: Path,
    simulator: str = "verilator", seed: int | None = None, coverage: bool = False,
    timeout_s: float = 1800,
) -> ToolResult:
    """`test_module` is a Python module name importable from `workdir`."""
    if simulator not in ("verilator", "icarus"):
        raise ValueError(f"unsupported simulator {simulator!r}")
    if coverage and simulator != "verilator":
        raise ValueError("coverage is collected only with verilator")
    workdir = workdir.resolve()
    s2s_dir = workdir / ".s2s"
    s2s_dir.mkdir(exist_ok=True)
    build_dir = workdir / f"sim_build_{simulator}"
    results_xml = build_dir / "results.xml"
    args = {
        "simulator": simulator, "sources": [str(Path(s).resolve()) for s in sources],
        "toplevel": toplevel, "test_module": test_module, "build_dir": str(build_dir),
        "test_dir": str(build_dir), "seed": seed, "results_xml": str(results_xml),
        "coverage": coverage,
    }
    # test_dir is the build dir, so make the test module importable from workdir.
    (s2s_dir / "cocotb_args.json").write_text(json.dumps(args, indent=2))
    (s2s_dir / "run_cocotb.py").write_text(_RUNNER)
    if results_xml.exists():
        results_xml.unlink()  # never read a stale result
    cmd = [COCOTB_PYTHON, str(s2s_dir / "run_cocotb.py"), str(s2s_dir / "cocotb_args.json")]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"cocotb_{simulator}.log", SPEC.version_key,
                         timeout_s, env={"PYTHONPATH": str(workdir)})
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec, {"results_xml": results_xml})
