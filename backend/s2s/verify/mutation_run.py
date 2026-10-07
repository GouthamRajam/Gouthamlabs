"""Myra's mutation harness (A3.12; M0.6 acceptance 2): 20 bugs injected into copies of the
known-good RTL, the regression run against each copy, detection rate reported.

Screening, with real tools, before a mutant counts:
  1. It must compile (Verilator --lint-only, errors only). A file that does not compile is not a
     bug the tests could catch; it is replaced by the next candidate.
  2. It must not be PROVEN equivalent to the original (Yosys miter + SAT temporal induction from
     the all-zero state, every input free; reset is an input, so "reset during operation" is
     explored). A proven-equivalent mutant (e.g. a change in an unreachable `default:`) cannot be
     detected by any test; it is reported and replaced. A mutant the solver cannot decide within
     the step bound goes to step 3.
  3. Unbounded sequential equivalence (CEO decision D2, prove-then-exclude): SymbiYosys builds the miter, then
     its PDR or ABC dprove (latch correspondence + induction). A mutant PROVEN equivalent is screened out with its
     proof log and replaced; one proven different or still undecided is KEPT and counted (never dropped on a guess).
Detection: the regression (seed 1, Verilator) has any failing test or crashes. A run that times out is
retried once at twice the limit; if it times out again it counts as NOT detected (never as a catch).
"""
from __future__ import annotations

import hashlib
import json
import os
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
    try:
        e = subprocess.run(["yosys", "-p", load + "equiv_make gold gate equiv; hierarchy -top equiv; "
                            "equiv_simple -seq 5; equiv_induct -seq 5; equiv_status -assert"],
                           capture_output=True, text=True, timeout=a["equiv_timeout"])
    except subprocess.TimeoutExpired:
        e = None  # not proven equivalent in time: the mutant stays in (conservative)
    if e is not None and e.returncode == 0 and "Equivalence successfully proven" in e.stdout:
        eq, log = "equivalent", "equiv_induct: equivalence proven"
    else:
        # bounded search for a difference from the all-zero state (every input free, incl. reset)
        try:
            y = subprocess.run(["yosys", "-p", load + "miter -equiv -flatten -make_assert -ignore_gold_x gold gate miter; "
                                f"hierarchy -top miter; sat -tempinduct -prove-asserts -set-init-zero -maxsteps {a['steps']} miter"],
                               capture_output=True, text=True, timeout=a["miter_timeout"])
            log = y.stdout + y.stderr
        except subprocess.TimeoutExpired:
            log = f"miter search timed out after {a['miter_timeout']} s"
        eq = "different" if "FAIL!" in log else "unknown"
        log = next((ln for ln in log.splitlines() if "FAIL!" in ln or "Reached maximum" in ln), log[-200:])
    out.append({"id": m["id"], "compiles": True, "equiv": eq, "detail": log[-300:]})
print("S2S_SCREEN " + json.dumps(out))
'''


def _tree_hash(root: Path) -> str:
    """Content hash of every file under `root` (paths and bytes), ignoring Python caches."""
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(str(f.relative_to(root)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def _verdict_key(rtl_dir: Path, tb_hash: str, top: str, test_module: str) -> str:
    return hashlib.sha256("\0".join([_tree_hash(rtl_dir), tb_hash, top, test_module]).encode()).hexdigest()


def classify_dprove(log: str) -> str:
    """ABC dprove's own verdict line; anything else is undecided (never read as a proof)."""
    if "Networks are equivalent" in log:
        return "equivalent"
    if "Networks are NOT EQUIVALENT" in log or "was asserted in frame" in log:
        return "different"
    return "undecided"


def _unbounded_equivalence(base: Path, m: Mutant, orig_dir: Path, rtl_files: dict[str, str], top: str,
                           cache: Path) -> dict:
    """Unbounded sequential equivalence of a mutant vs the original (CEO decision D2, prove-then-exclude).
    SymbiYosys builds the miter (both designs from the all-zero state; reset is a free input, so every run from
    reset is covered); its PDR may finish first, else ABC dprove (latch correspondence + induction + fraiging).
    Only 'equivalent' from a completed engine screens a mutant out; 'different' and 'undecided' keep it."""
    names = [Path(p).name for p in rtl_files]
    gate = base / m.id / "rtl"
    key = hashlib.sha256("\0".join([_tree_hash(orig_dir / "rtl"), _tree_hash(gate), top, "equiv-v1"]).encode()).hexdigest()
    hit = cache / f"equiv_{key}.json"
    if hit.exists():
        return {**json.loads(hit.read_text()), "cached": True}
    d = base / m.id / "eq"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    # the tool container mounts only `d`: both RTL versions are copied inside it
    for tag, src in (("gold", orig_dir / "rtl"), ("gate", gate)):
        (d / tag).mkdir()
        for n in names:
            shutil.copy2(src / n, d / tag / n)
    load = lambda tag: (f"read_verilog -sv {' '.join(f'{tag}/{n}' for n in names)}\nhierarchy -check -top {top}\n"
                                f"proc\nmemory\nflatten\nopt_clean\nrename {top} {tag}\ndesign -stash {tag}\n")
    (d / "eq.sby").write_text(
        "[options]\nmode prove\n\n[engines]\nabc pdr\n\n[script]\n" + load("gold") + load("gate")
        + "design -copy-from gold -as gold gold\ndesign -copy-from gate -as gate gate\n"
        "miter -equiv -flatten -make_assert -ignore_gold_x gold gate miter\nhierarchy -top miter\nzinit -all\n\n[files]\n"
        + "".join(f"gold/{n} {d / 'gold' / n}\ngate/{n} {d / 'gate' / n}\n" for n in names))
    runner.run(["sby", "-f", "eq.sby"], d, d / "sby.log", "sby", 120, cwd=d)
    sby_log = (d / "sby.log").read_text(errors="replace")
    if "DONE (PASS" in sby_log:
        out = {"status": "equivalent", "method": "SymbiYosys abc pdr", "log": str(d / "sby.log")}
    elif "DONE (FAIL" in sby_log:
        out = {"status": "different", "method": "SymbiYosys abc pdr", "log": str(d / "sby.log")}
    elif not (d / "eq" / "model" / "design_aiger.aig").exists():
        return {"status": "undecided", "method": "miter model not built", "log": str(d / "sby.log")}
    else:
        rec = runner.run(["yosys-abc", "-c", "read_aiger eq/model/design_aiger.aig; fold; strash; dprove -v"],
                         d, d / "dprove.log", "yosys", float(os.environ.get("S2S_EQUIV_TIMEOUT_S", "300")), cwd=d)
        st = classify_dprove((d / "dprove.log").read_text(errors="replace"))
        out = {"status": st, "method": "ABC dprove", "log": str(d / "dprove.log"),
               "timed_out": bool(rec.timed_out)}
    if out["status"] != "undecided":  # a decided verdict depends only on the two RTL versions
        hit.write_text(json.dumps(out))
    return out


class MutationHarnessError(RuntimeError):
    """The measurement itself failed (never reported as a detection rate)."""


def run_mutation(*, workdir: Path, rtl_files: dict[str, str], top: str, tb_dir: Path, test_module: str,
                 n: int = 20, timeout_s: float = 900, parallel: int | None = None, log=print) -> dict:
    """Returns {"mutants": [...], "detected": k, "total": n, "rate": k/n, "screened_out": [...]}."""
    # Concurrent design runs share the cores: every simulation also takes a machine-wide tool slot
    # (s2s.tools.runner), so oversubscription only queues runs. A timeout never counts as a catch.
    parallel = parallel or int(os.environ.get("S2S_MUTATION_PARALLEL", "4"))
    base = (workdir / "mutation").resolve()
    cache = (workdir / "mutation_verdicts").resolve()
    cache.mkdir(parents=True, exist_ok=True)
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
        args = {"top": top, "orig": [str(orig_dir / p) for p in rtl_files], "mutants": specs, "steps": 25,
                "equiv_timeout": 120, "miter_timeout": 90}
        (base / "screen_args.json").write_text(json.dumps(args))
        (base / "screen.py").write_text(_SCREEN)
        rec = runner.run(["/opt/cocotb/bin/python3", str(base / "screen.py"), str(base / "screen_args.json")],
                         base, base / f"screen_{i}.log", "yosys", 3600)
        text = Path(rec.log_path).read_text()
        res = {r["id"]: r for line in text.splitlines() if line.startswith("S2S_SCREEN ")
               for r in json.loads(line[len("S2S_SCREEN "):])}
        missing = [m.id for m in batch if m.id not in res]
        if missing:  # the screen itself failed: never read as "does not compile"
            raise MutationHarnessError(f"equivalence screen gave no result for {len(missing)} mutant(s) "
                                       f"(e.g. {missing[0]}); see {base}/screen_{i}.log")
        undecided = [m for m in batch if res[m.id]["compiles"] and res[m.id]["equiv"] == "unknown"]
        with ThreadPoolExecutor(max_workers=parallel) as pool:  # CEO decision D2: unbounded proof, never a guess
            proofs = dict(zip([m.id for m in undecided],
                              pool.map(runner.carry_heartbeat(lambda m: _unbounded_equivalence(base, m, orig_dir, rtl_files, top, cache)),
                                       undecided)))
        for m in batch:
            r = res[m.id]
            screen[m.id] = r.get("equiv")
            pr = proofs.get(m.id)
            if pr:
                screen[m.id] = f"{r.get('equiv')}; unbounded: {pr['status']} ({pr['method']})"
            if r["compiles"] and pr and pr["status"] == "equivalent":
                screened_out.append({"id": m.id, "type": m.type, "description": m.description,
                                     "reason": f"proven equivalent to the original ({pr['method']}; proof log "
                                               f"{pr['log']})", "proof": pr})
            elif not r["compiles"]:
                screened_out.append({"id": m.id, "type": m.type, "description": m.description, "reason": "does not compile"})
            elif r["equiv"] == "equivalent":
                screened_out.append({"id": m.id, "type": m.type, "description": m.description,
                                     "reason": "proven equivalent to the original (yosys equiv_induct)"})
            elif len(kept) < n:
                kept.append(m)
        log(f"mutation screening: {len(kept)}/{n} kept, {len(screened_out)} screened out so far")

    def regress(rtl_dir: Path, name: str, limit: float):
        return run_cocotb_regress([rtl_dir / Path(p).name for p in rtl_files], top, test_module, tb_copy, base,
                                  f"{name}/regress", [1], simulators=("verilator",), coverage=False, waves=False,
                                  timeout_s=limit, extra_build_args=["-Wno-fatal"])

    # The unmutated original must pass through the identical path, or the measurement is void. Its own
    # limit is the regression capacity; each mutant then gets max(timeout_s, 3 x the original's run
    # time), retried once at twice that; a mutant that still times out counts as NOT caught.
    ref = regress(orig_dir / "rtl", "orig", float(os.environ.get("S2S_REGRESS_TIMEOUT_S", str(max(timeout_s, 2400)))))
    if not ref.passed:
        raise MutationHarnessError("the unmutated RTL does not pass the regression in the mutation harness: "
                                   + "; ".join(ref.reasons[:3]))
    mutant_timeout = max(timeout_s, 3 * (ref.duration_s or 0))
    log(f"mutation: unmutated regression passed in {ref.duration_s:.0f} s; mutant limit {mutant_timeout:.0f} s")

    tb_hash = _tree_hash(tb_copy)

    def run_one(m: Mutant) -> dict:
        # A verdict reached without any timeout depends only on the mutant RTL, the testbench and the
        # top/test module, so it is cached outside mutation/ (which each run wipes): a run cut off by a
        # restart redoes only the mutants that had not finished. Timeouts are never cached.
        key = _verdict_key(base / m.id / "rtl", tb_hash, top, test_module)
        hit = cache / f"{key}.json"
        if hit.exists():
            res = {**json.loads(hit.read_text()), "cached": True}
            log(f"mutant {m.id}: {'caught' if res['detected'] else 'missed'} (cached verdict, same RTL and tests)")
            return res
        r = regress(base / m.id / "rtl", m.id, mutant_timeout)
        timeouts = 0
        if r.timed_out:  # retried once with twice the limit before any verdict
            timeouts = 1
            r = regress(base / m.id / "rtl", f"{m.id}_retry", 2 * mutant_timeout)
        failed = r.metrics.get("failed_runs", 0)
        ran = bool(r.metrics.get("test_runs"))
        if r.timed_out:
            # CEO rule: a timed-out simulation is never counted as a caught bug (it may only be slow).
            timeouts = 2
            detected, how = False, f"regression timed out twice ({mutant_timeout:.0f} s, then {2 * mutant_timeout:.0f} s): NOT counted as caught"
        elif failed:
            detected = True
            how = f"{failed} failing test run(s): " + ", ".join(
                sorted(k for k, v in r.metrics.get("tests_by_name", {}).items() if v["fail"]))
        elif ran:
            detected, how = False, "all tests passed"
        else:  # build or harness error: never counted as a detection
            detected, how = None, "harness error: " + "; ".join(r.reasons[:2])
        log(f"mutant {m.id}: {'caught' if detected else ('missed' if detected is False else 'harness error')}")
        res = {"id": m.id, "type": m.type, "file": m.file, "line": m.line, "description": m.description,
               "reqs": list(m.reqs), "before": m.before.strip(), "after": m.after.strip(), "detected": detected,
               "how": how, "duration_s": r.duration_s, "timeouts": timeouts, "equivalence_screen": screen.get(m.id)}
        if detected is not None and timeouts == 0:
            hit.write_text(json.dumps(res))
        return res

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        results = list(pool.map(runner.carry_heartbeat(run_one), kept))  # tool heartbeats reach the step
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
            "timed_out_not_counted": sum(1 for r in results if r["timeouts"] == 2),
            "cached_verdicts": sum(1 for r in results if r.get("cached")),
            "equivalence_screen": {m.id: screen.get(m.id) for m in kept}}
