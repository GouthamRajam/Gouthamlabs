"""Myra's mutation harness (A3.12; M0.6 acceptance 2): 20 bugs injected into copies of the
known-good RTL, the regression run against each copy, detection rate reported.

Screening, with real tools, before a mutant counts:
  1. It must compile (Verilator --lint-only, errors only). A file that does not compile is not a
     bug the tests could catch; it is replaced by the next candidate.
  2. It must not be PROVEN equivalent to the original (Yosys miter + SAT temporal induction from
     the all-zero state, every input free; reset is an input, so "reset during operation" is
     explored). A proven-equivalent mutant (e.g. a change in an unreachable `default:`) cannot be
     detected by any test; it is reported and replaced. A mutant the solver cannot decide within
     the step bound is KEPT and counted.
Detection: the regression (seed 1, Verilator) has any failing test, crashes, or times out.
"""
from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from s2s.tools import runner
from s2s.tools.cocotb_regress import run_cocotb_regress
from s2s.verify.mutate import Mutant, candidates, sample

_SCREEN = r'''
import json, subprocess, sys
from pathlib import Path
a = json.loads(Path(sys.argv[1]).read_text())
orig = " ".join(a["orig"])
out = []
for m in a["mutants"]:
    files = " ".join(m["files"])
    lint = subprocess.run(["verilator", "--lint-only", "-Wno-fatal", "-Wno-lint", "-Wno-style", "--top-module", a["top"], *m["files"]],
                          capture_output=True, text=True)
    if lint.returncode != 0:
        out.append({"id": m["id"], "compiles": False, "equiv": None, "detail": lint.stderr[-400:]})
        continue
    load = (f"read_verilog -sv {orig}; hierarchy -check -top {a['top']}; proc; memory; flatten; opt_clean; "
            f"rename {a['top']} gold; design -stash g; "
            f"read_verilog -sv {files}; hierarchy -check -top {a['top']}; proc; memory; flatten; opt_clean; "
            f"rename {a['top']} gate; design -stash m; "
            "design -copy-from g -as gold gold; design -copy-from m -as gate gate; ")
    # equivalence proof with registers matched by name (equiv_induct)
    e = subprocess.run(["yosys", "-p", load + "equiv_make gold gate equiv; hierarchy -top equiv; "
                        "equiv_simple -seq 5; equiv_induct -seq 5; equiv_status -assert"],
                       capture_output=True, text=True, timeout=300)
    if e.returncode == 0 and "Equivalence successfully proven" in e.stdout:
        eq, log = "equivalent", "equiv_induct: equivalence proven"
    else:
        # bounded search for a difference from the all-zero state (every input free, incl. reset)
        y = subprocess.run(["yosys", "-p", load + "miter -equiv -flatten -make_assert -ignore_gold_x gold gate miter; "
                            f"hierarchy -top miter; sat -tempinduct -prove-asserts -set-init-zero -maxsteps {a['steps']} miter"],
                           capture_output=True, text=True, timeout=300)
        log = y.stdout + y.stderr
        eq = "different" if "FAIL!" in log else "unknown"
        log = next((ln for ln in log.splitlines() if "FAIL!" in ln or "Reached maximum" in ln), log[-200:])
    out.append({"id": m["id"], "compiles": True, "equiv": eq, "detail": log[-300:]})
print("S2S_SCREEN " + json.dumps(out))
'''


class MutationHarnessError(RuntimeError):
    """The measurement itself failed (never reported as a detection rate)."""


def run_mutation(*, workdir: Path, rtl_files: dict[str, str], top: str, tb_dir: Path, test_module: str,
                 n: int = 20, timeout_s: float = 900, parallel: int = 4, log=print) -> dict:
    """Returns {"mutants": [...], "detected": k, "total": n, "rate": k/n, "screened_out": [...]}."""
    base = (workdir / "mutation").resolve()
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    orig_dir = base / "orig"
    (orig_dir / "rtl").mkdir(parents=True)
    for path, text in rtl_files.items():
        (orig_dir / path).write_text(text)
    tb_copy = base / "tb"
    shutil.copytree(tb_dir, tb_copy)
    order = sample(candidates(rtl_files))
    kept: list[Mutant] = []
    screened_out: list[dict] = []
    screen: dict[str, str | None] = {}
    i = 0
    while len(kept) < n and i < len(order):
        batch = order[i:i + (n - len(kept)) + 6]
        i += len(batch)
        specs = []
        for m in batch:
            d = base / m.id / "rtl"
            d.mkdir(parents=True, exist_ok=True)
            for path, text in rtl_files.items():
                (d / Path(path).name).write_text(m.apply(text) if path == m.file else text)
            specs.append({"id": m.id, "files": [str(d / Path(p).name) for p in rtl_files]})
        args = {"top": top, "orig": [str(orig_dir / p) for p in rtl_files], "mutants": specs, "steps": 25}
        (base / "screen_args.json").write_text(json.dumps(args))
        (base / "screen.py").write_text(_SCREEN)
        rec = runner.run(["/opt/cocotb/bin/python3", str(base / "screen.py"), str(base / "screen_args.json")],
                         base, base / f"screen_{i}.log", "yosys", 3600)
        text = Path(rec.log_path).read_text()
        res = {r["id"]: r for line in text.splitlines() if line.startswith("S2S_SCREEN ")
               for r in json.loads(line[len("S2S_SCREEN "):])}
        for m in batch:
            r = res.get(m.id, {"compiles": False, "equiv": None, "detail": "screen did not report"})
            screen[m.id] = r.get("equiv")
            if not r["compiles"]:
                screened_out.append({"id": m.id, "type": m.type, "description": m.description, "reason": "does not compile"})
            elif r["equiv"] == "equivalent":
                screened_out.append({"id": m.id, "type": m.type, "description": m.description,
                                     "reason": "proven equivalent to the original (yosys miter + SAT induction)"})
            elif len(kept) < n:
                kept.append(m)
        log(f"mutation screening: {len(kept)}/{n} kept, {len(screened_out)} screened out so far")

    def regress(rtl_dir: Path, name: str):
        return run_cocotb_regress([rtl_dir / Path(p).name for p in rtl_files], top, test_module, tb_copy, base,
                                  f"{name}/regress", [1], simulators=("verilator",), coverage=False, waves=False,
                                  timeout_s=timeout_s, extra_build_args=["-Wno-fatal"])

    # The unmutated original must pass through the identical path, or the measurement is void.
    ref = regress(orig_dir / "rtl", "orig")
    if not ref.passed:
        raise MutationHarnessError("the unmutated RTL does not pass the regression in the mutation harness: "
                                   + "; ".join(ref.reasons[:3]))

    def run_one(m: Mutant) -> dict:
        r = regress(base / m.id / "rtl", m.id)
        failed = r.metrics.get("failed_runs", 0)
        ran = bool(r.metrics.get("test_runs"))
        if r.timed_out:
            detected, how = True, "regression timed out (hang)"
        elif failed:
            detected = True
            how = f"{failed} failing test run(s): " + ", ".join(
                sorted(k for k, v in r.metrics.get("tests_by_name", {}).items() if v["fail"]))
        elif ran:
            detected, how = False, "all tests passed"
        else:  # build or harness error: never counted as a detection
            detected, how = None, "harness error: " + "; ".join(r.reasons[:2])
        return {"id": m.id, "type": m.type, "file": m.file, "line": m.line, "description": m.description,
                "reqs": list(m.reqs), "before": m.before.strip(), "after": m.after.strip(), "detected": detected,
                "how": how, "duration_s": r.duration_s, "equivalence_screen": screen.get(m.id)}

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        results = list(pool.map(run_one, kept))
    errors = [r for r in results if r["detected"] is None]
    if errors:
        raise MutationHarnessError(f"{len(errors)} mutant run(s) failed to run: {errors[0]['how']}")
    for r in results:
        log(f"  {'CAUGHT' if r['detected'] else 'MISSED'}  {r['type']:<18} {r['description'][:90]}  ({r['how'][:80]})")
    k = sum(r["detected"] for r in results)
    by_type: dict[str, list[int]] = {}
    for r in results:
        by_type.setdefault(r["type"], [0, 0])
        by_type[r["type"]][0] += r["detected"]
        by_type[r["type"]][1] += 1
    return {"mutants": results, "detected": k, "total": len(results), "rate": round(k / len(results), 4) if results else 0.0,
            "by_type": {t: f"{a}/{b}" for t, (a, b) in by_type.items()}, "screened_out": screened_out,
            "equivalence_screen": {m.id: screen.get(m.id) for m in kept}}
