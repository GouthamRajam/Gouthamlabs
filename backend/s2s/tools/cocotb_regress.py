"""cocotb_regress: one regression = build once, run the cocotb test module for several seeds
(MASTER_SPEC Part 7.5; M0.6 Rex/Cora). Verilator builds collect line + toggle coverage and a
port-level VCD per seed; an Icarus build (no coverage) cross-checks the simulator.

Everything runs inside s2s-eda with networking off (the testbench is model-written code).
Pass/fail per seed comes from cocotb's JUnit results.xml for that seed; zero tests is a failure.
Coverage comes from Verilator's own coverage.dat (merged over seeds): line from
`verilator_coverage --write-info`, toggle from the v_toggle points.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from s2s.tools import runner
from s2s.tools.base import ToolSpec, finish, unavailable
from s2s.tools.cocotb_sim import _failure_detail
from s2s.tools.result import Issue, ParsedLog, ToolResult

COCOTB_PYTHON = "/opt/cocotb/bin/python3"
_DONE = "S2S_REGRESS_DONE"
_SUMMARY = re.compile(r"^S2S_REGRESS_SUMMARY (?P<json>\{.*\})$", re.M)


def parse(log: str, reports: dict[str, str]) -> ParsedLog:
    out = ParsedLog(success_marker=_DONE in log)
    m = None
    for m in _SUMMARY.finditer(log):
        pass
    summary = json.loads(m["json"]) if m else {}
    runs = summary.get("runs", [])
    tests: dict[str, dict] = {}
    total = failed = 0
    for r in runs:
        xml = r.get("results_xml_text") or ""
        if not xml.strip():
            out.stage_failures.append(f"{r['simulator']} seed {r['seed']}: no results.xml (simulation did not finish)")
            continue
        for case in ET.fromstring(xml).iter("testcase"):
            name = case.get("name", "")
            bad = case.find("failure")
            if bad is None:
                bad = case.find("error")
            total += 1
            res = tests.setdefault(name, {"pass": 0, "fail": 0, "fail_seeds": []})
            if bad is None:
                res["pass"] += 1
            else:
                failed += 1
                res["fail"] += 1
                res["fail_seeds"].append(f"{r['simulator']}:{r['seed']}")
                msg = (_failure_detail(log, name) or bad.get("message") or bad.tag)[:400]
                out.errors.append(Issue("error", f"{r['simulator']} seed {r['seed']}: test {name} failed: {msg}",
                                        case.get("file"), _int(case.get("lineno")), rule="test_failure"))
    if runs and total == 0:
        out.stage_failures.append("no cocotb tests ran")
    cov = summary.get("coverage") or {}
    out.metrics = {
        "runs": [{k: v for k, v in r.items() if k != "results_xml_text"} for r in runs],
        "tests": len(tests), "test_runs": total, "failed_runs": failed, "tests_by_name": tests,
        "line_coverage": cov.get("line"), "toggle_coverage": cov.get("toggle"),
        "lines_hit": cov.get("lines_hit"), "lines_found": cov.get("lines_found"),
        "toggles_hit": cov.get("toggles_hit"), "toggles_found": cov.get("toggles_found"),
        "uncovered_lines": cov.get("uncovered_lines", [])[:200],
        "untoggled": cov.get("untoggled", [])[:200],
        "vcds": [r.get("vcd") for r in runs if r.get("vcd")],
    }
    return out


def _int(v: str | None) -> int | None:
    return int(v) if v and v.isdigit() else None


SPEC = ToolSpec(name="cocotb_regress", version_key="cocotb", parse=parse,
                failure_patterns=(r"(?m)^%Error", r"FAIL=[1-9]"))

# Runs inside s2s-eda with cocotb's Python; arguments come from a JSON file.
_RUNNER = r'''
import json, re, subprocess, sys, traceback
from pathlib import Path
from cocotb.runner import get_runner
a = json.loads(Path(sys.argv[1]).read_text())
base = Path(a["out_dir"])
runs, cov = [], None
for sim in a["simulators"]:
    r = get_runner(sim)
    bdir = base / f"build_{sim}"
    args = list(a.get("extra_build_args", [])) if sim == "verilator" else []
    if sim == "verilator":
        if a["coverage"]:
            args += ["--coverage-line", "--coverage-toggle"]
        if a["waves"]:
            args += ["--trace", "--trace-depth", "1"]
    r.build(verilog_sources=a["sources"], hdl_toplevel=a["toplevel"], build_dir=str(bdir),
            timescale=("1ns", "1ps"), build_args=args, always=True, waves=a["waves"] and sim == "verilator",
            defines=a.get("defines", {}))
    seeds = a["seeds"] if sim == "verilator" else a["seeds"][:1]
    for seed in seeds:
        tdir = base / f"{sim}_seed{seed}"
        tdir.mkdir(parents=True, exist_ok=True)
        xml = tdir / "results.xml"
        if xml.exists():
            xml.unlink()
        try:
            r.test(hdl_toplevel=a["toplevel"], test_module=a["test_module"], build_dir=str(bdir), test_dir=str(tdir),
                   seed=seed, results_xml=str(xml), waves=a["waves"] and sim == "verilator",
                   extra_env={"PYTHONPATH": a["pythonpath"]})
        except Exception:
            traceback.print_exc()
        vcd = tdir / "dump.vcd"
        runs.append({"simulator": sim, "seed": seed, "results_xml_text": xml.read_text() if xml.exists() else "",
                     "vcd": str(vcd) if vcd.exists() else None})
if a["coverage"]:
    dats = [str(base / f"verilator_seed{s}" / "coverage.dat") for s in a["seeds"]
            if (base / f"verilator_seed{s}" / "coverage.dat").exists()]
    if dats:
        merged = base / "coverage_merged.dat"
        subprocess.run(["verilator_coverage", "--write", str(merged), *dats], check=True)
        info = base / "coverage.info"
        subprocess.run(["verilator_coverage", "--write-info", str(info), str(merged)], check=True)
        lf = lh = 0
        uncovered, cur = [], None
        for line in info.read_text().splitlines():
            if line.startswith("SF:"):
                cur = line[3:]
            elif line.startswith("DA:"):
                ln, n = line[3:].split(",")[:2]
                lf += 1
                if int(n) > 0:
                    lh += 1
                else:
                    uncovered.append(f"{Path(cur).name}:{ln}")
        th = tf = 0
        untoggled = []
        for line in merged.read_text().splitlines():
            if not line.startswith("C '"):
                continue
            key, count = line[3:].rsplit("' ", 1)
            fields = dict(re.findall(r"\x01(\w+)\x02([^\x01]*)", "\x01" + key))
            if not fields.get("page", "").startswith("v_toggle"):
                continue
            tf += 1
            if int(count) > 0:
                th += 1
            else:
                untoggled.append(f"{fields.get('page', '').split('/')[-1]}.{fields.get('o', '?')}")
        cov = {"line": round(lh / lf, 4) if lf else None, "lines_hit": lh, "lines_found": lf,
               "toggle": round(th / tf, 4) if tf else None, "toggles_hit": th, "toggles_found": tf,
               "uncovered_lines": uncovered, "untoggled": untoggled}
print("S2S_REGRESS_SUMMARY " + json.dumps({"runs": runs, "coverage": cov}))
print("S2S_REGRESS_DONE")
'''


def run_cocotb_regress(sources: list[Path], toplevel: str, test_module: str, tb_dir: Path, workdir: Path,
                       out_name: str, seeds: list[int], simulators: tuple[str, ...] = ("verilator", "icarus"),
                       coverage: bool = True, waves: bool = True, timeout_s: float = 3600,
                       extra_build_args: list[str] | None = None, defines: dict | None = None) -> ToolResult:
    """Build once per simulator and run `test_module` (importable from `tb_dir`) for each seed.
    Results land in <workdir>/<out_name>/."""
    workdir = workdir.resolve()
    out_dir = workdir / out_name
    out_dir.mkdir(parents=True, exist_ok=True)
    args = {"simulators": list(simulators), "sources": [str(Path(s).resolve()) for s in sources],
            "toplevel": toplevel, "test_module": test_module, "out_dir": str(out_dir), "seeds": seeds,
            "coverage": coverage, "waves": waves, "pythonpath": str(Path(tb_dir).resolve()),
            "extra_build_args": extra_build_args or [], "defines": defines or {}}
    (out_dir / "regress_args.json").write_text(json.dumps(args, indent=2))
    (out_dir / "run_regress.py").write_text(_RUNNER)
    cmd = [COCOTB_PYTHON, str(out_dir / "run_regress.py"), str(out_dir / "regress_args.json")]
    try:
        rec = runner.run(cmd, workdir, workdir / "logs" / f"regress_{out_name}.log", SPEC.version_key, timeout_s,
                         env={"PYTHONPATH": str(Path(tb_dir).resolve())})
    except runner.EdaUnavailable as e:
        return unavailable(SPEC, str(e), cmd)
    return finish(SPEC, rec)
