"""M0.6 acceptance tests (MASTER_SPEC 13.2), re-executed independently of the runs' own records.

    cd backend && python scripts/m06_acceptance.py <m06_run_id> [<m06_run_id> ...] [--dex]

Per design (from the run's final RTL and verification files, copied into a fresh folder):
  1. Regression re-run (Verilator seeds 1-3 + Icarus seed 1): 100% passing; coverage at target
     (line, toggle from Verilator; functional bins from the waveforms).
  2. Mutation re-run: 20 screened mutants of the final RTL; the regression catches >= 17 (85%).
  3. Formal re-run: >= 3 meaningful properties proven (cover reached, not a tautology).
  4. Anti-cheating guard: weakened copies of the design's real testbench are all flagged.
Once (--dex):
  5. Dex triage suite: 10 seeded failures (each a real failing simulation) classified, >= 9 correct.
     REAL model calls, metered under the design "dex_triage_suite".
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
os.environ.setdefault("S2S_SECRETS_DIR", str(REPO / "var" / "secrets"))
os.environ.setdefault("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))
sys.path.insert(0, str(BACKEND))

import yaml  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from s2s.agents import llm  # noqa: E402
from s2s.agents.m06 import targets  # noqa: E402
from s2s.agents.runtime import Agent, StepContext, artifact_dir, run_task  # noqa: E402
from s2s.db.models import Design, Project, Task, UsageRecord  # noqa: E402
from s2s.db.session import session  # noqa: E402
from s2s.design.schemas import DEX_ANSWER  # noqa: E402
from s2s.ids import new_id  # noqa: E402
from s2s.models.gateway import ModelGateway  # noqa: E402
from s2s.orchestrator.engine import create_run  # noqa: E402
from s2s.tools.cocotb_regress import run_cocotb_regress  # noqa: E402
from s2s.verify import fcov, guard  # noqa: E402
from s2s.verify.dex_suite import SCENARIOS, build  # noqa: E402
from s2s.verify.formal import run_formal  # noqa: E402
from s2s.verify.mutation_run import run_mutation  # noqa: E402

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def fresh_copy(run_id: str) -> tuple[Path, dict]:
    root = artifact_dir() / "runs" / run_id
    d = artifact_dir() / "acceptance_m06" / run_id
    shutil.rmtree(d, ignore_errors=True)
    for sub in ("rtl", "tb", "formal", "spec", "arch"):
        shutil.copytree(root / sub, d / sub, ignore=shutil.ignore_patterns("stub", "props_*", "__pycache__"))
    spec = yaml.safe_load((d / "spec/spec.yaml").read_text())
    arch = yaml.safe_load((d / "arch/arch.yaml").read_text())
    return d, {"design": spec["design"], "top": arch["top"]}


def per_design(run_id: str) -> None:
    d, info = fresh_copy(run_id)
    name, top = info["design"], info["top"]
    t = targets()
    rtl = sorted((d / "rtl").glob("*.v"))
    mods = ",".join(p.stem for p in sorted((d / "tb").glob("test_*.py")))
    print(f"\n=== {name} ({run_id}) - fresh copy {d} ===", flush=True)
    # 1. regression + coverage
    r = run_cocotb_regress(rtl, top, mods, d / "tb", d, "sim", [1, 2, 3], timeout_s=3000)
    m = r.metrics
    plan = yaml.safe_load((d / "tb/testplan.yaml").read_text())
    ports = {p["name"] for p in json.loads((d / "tb/dut_ports.json").read_text())["ports"]}
    hits = fcov.bin_hits([Path(v) for v in m.get("vcds", [])], plan["clock"], plan["coverage_bins"], ports)
    func_cov = sum(1 for v in hits.values() if v) / len(hits)
    print(f"   $ {' '.join(r.command[-2:])}  ({r.tool_version}, {r.duration_s}s)")
    print(f"   tests: {m['tests']} x runs: {m['test_runs']} (verilator seeds 1-3 + icarus seed 1), failed runs: {m['failed_runs']}")
    for tname, v in sorted(m["tests_by_name"].items()):
        print(f"     {tname:<44} pass {v['pass']} fail {v['fail']}")
    record(f"1. {name}: regression 100% passing", r.passed and m["failed_runs"] == 0 and m["test_runs"] > 0,
           f"{m['test_runs'] - m['failed_runs']}/{m['test_runs']} test runs passed")
    record(f"1. {name}: line coverage >= {t['line']}", (m["line_coverage"] or 0) >= t["line"],
           f"{m['line_coverage']} ({m['lines_hit']}/{m['lines_found']} lines)")
    record(f"1. {name}: toggle coverage >= {t['toggle']}", (m["toggle_coverage"] or 0) >= t["toggle"],
           f"{m['toggle_coverage']} ({m['toggles_hit']}/{m['toggles_found']} toggle points)")
    record(f"1. {name}: functional bins = {t['functional_bins']}", func_cov >= t["functional_bins"],
           f"{sum(1 for v in hits.values() if v)}/{len(hits)} bins hit; unhit: {[b for b, v in hits.items() if not v]}")
    # 2. mutation
    res = run_mutation(workdir=d, rtl_files={f"rtl/{p.name}": p.read_text() for p in rtl}, top=top,
                       tb_dir=d / "tb", test_module=mods, log=lambda s: None)
    for mu in res["mutants"]:
        print(f"     {'CAUGHT' if mu['detected'] else 'MISSED'}  {mu['type']:<18} {mu['description'][:80]}")
    for so in res["screened_out"]:
        print(f"     (screened out: {so['reason'][:40]}) {so['description'][:70]}")
    record(f"2. {name}: mutation detection >= 85% of 20", res["total"] == 20 and res["rate"] >= t["mutation_detection"],
           f"{res['detected']}/{res['total']} caught = {res['rate']:.0%}; by type {res['by_type']}; "
           f"{len(res['screened_out'])} proven-equivalent/non-compiling mutants screened out")
    # 3. formal
    ports_l = json.loads((d / "tb/dut_ports.json").read_text())["ports"]
    f = run_formal(d, rtl, d / "formal/formal_top.sv", int(t["formal_min_depth"]), top=top, ports=ports_l)
    for pn, pv in f["properties"].items():
        print(f"     ap_{pn:<28} {pv['status']:<10} cover {'reached' if pv['cover_reached'] else 'NOT reached'}, "
              f"{'depends on the design' if pv['depends_on_design'] else 'TAUTOLOGY'}")
    record(f"3. {name}: >= 3 meaningful properties proven, vacuity check passes",
           f["proven_meaningful"] >= 3 and not f["vacuous"] and not f["failed"],
           f"{f['proven_meaningful']} meaningful proven (depth {f['depth']}, prove {f['prove_status']}); "
           f"vacuous {f['vacuous']}; failed {f['failed']}")
    # 4. guard on weakened copies of the real testbench
    tb_name = f"tb/test_{name}.py"
    tb = (d / tb_name).read_text()
    weakened = _weaken(tb)
    flagged = {k: guard.diff_files({tb_name: tb}, {tb_name: v}) for k, v in weakened.items()}
    for k, fl in flagged.items():
        print(f"     weakening '{k}': {fl[:2] if fl else 'NOT FLAGGED'}")
    record(f"4. {name}: anti-cheating guard flags weakened tests", all(flagged.values()) and len(flagged) >= 3,
           f"{sum(1 for v in flagged.values() if v)}/{len(flagged)} weakened versions flagged")


def _weaken(tb: str) -> dict[str, str]:
    """Deliberately weakened copies of a real testbench: one per cheating pattern."""
    tree = ast.parse(tb)
    lines = tb.split("\n")
    out = {}
    tests = [n for n in ast.walk(tree) if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef)) and
             any("cocotb.test" in ast.unparse(dd) for dd in n.decorator_list)]
    asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    if asserts:
        a = asserts[0]
        cp = list(lines)
        cp[a.lineno - 1] = " " * a.col_offset + "pass"
        for i in range(a.lineno, a.end_lineno):
            cp[i] = ""
        out["assertion removed"] = "\n".join(cp)
    if tests:
        t = tests[-1]
        cp = list(lines)
        start = min(dd.lineno for dd in t.decorator_list) - 1
        for i in range(start, t.end_lineno):
            cp[i] = ""
        out["test deleted"] = "\n".join(cp)
        cp = list(lines)
        dl = t.decorator_list[0]
        cp[dl.lineno - 1] = cp[dl.lineno - 1].replace("cocotb.test(", "cocotb.test(skip=True, ", 1) \
            if "cocotb.test(" in cp[dl.lineno - 1] else cp[dl.lineno - 1].replace("cocotb.test", "cocotb.test(skip=True)", 1)
        out["skip marker added"] = "\n".join(cp)
    loops = [n for n in ast.walk(tree) if isinstance(n, ast.For) and isinstance(n.iter, ast.Call)
             and ast.unparse(n.iter.func) == "range" and any(isinstance(c, ast.Constant) and type(c.value) is int and c.value > 2
                                                         for c in ast.walk(n.iter))]
    if loops:
        lp = loops[0]
        c = max((c for c in ast.walk(lp.iter) if isinstance(c, ast.Constant) and type(c.value) is int), key=lambda c: c.value)
        cp = list(lines)
        ln = cp[c.lineno - 1]
        cp[c.lineno - 1] = ln[:c.col_offset] + "1" + ln[c.end_col_offset:]
        out["iterations reduced"] = "\n".join(cp)
    return out


class DexSuite(Agent):
    def steps(self, task: Task):
        def classify(ctx: StepContext) -> None:
            out = []
            for sc in SCENARIOS:
                d = ctx.workdir / sc.id
                shutil.rmtree(d, ignore_errors=True)
                files = build(sc, d)
                r = run_cocotb_regress([d / "rtl/counter8.v"], "counter8", "test_counter8", d / "tb", d, "sim", [1],
                                       simulators=("verilator",), coverage=False, waves=False, timeout_s=600)
                if not r.metrics.get("failed_runs"):
                    raise RuntimeError(f"scenario {sc.id} does not fail in simulation; it cannot be used")
                failures = {"failures": [{"kind": "simulation", "message": e.message} for e in r.errors]}
                (d / "reports").mkdir(exist_ok=True)
                (d / "reports/regression_failures.json").write_text(json.dumps(failures, indent=2))
                inputs = {k: v for k, v in files.items()}
                inputs["reports/regression_failures.json"] = json.dumps(failures, indent=2)
                data = llm.ask(ctx, "Dex", goal="Classify every failure as DESIGN (RTL wrong vs spec), TEST (testbench, "
                               "reference model or formal property wrong vs spec) or SPEC (the spec does not decide the "
                               "behavior, or contradicts itself). Give a one-sentence root cause and evidence.",
                               inputs=inputs, exit_criteria=["every failure explained by exactly one bug"], schema=DEX_ANSWER)
                classes = sorted({b["classification"] for b in data["bugs"]})
                got = classes[0] if len(classes) == 1 else "/".join(classes)
                out.append({"id": sc.id, "truth": sc.truth, "dex": got, "correct": got == sc.truth, "seeded": sc.what,
                            "root_cause": [b["root_cause"] for b in data["bugs"]],
                            "failing_tests": sorted(k for k, v in r.metrics["tests_by_name"].items() if v["fail"])})
                ctx.emit("finding", f"Dex suite {sc.id}: truth {sc.truth}, Dex said {got}", agent_id="Dex",
                         team=llm.agent("Dex").team, detail=out[-1])
            ctx.task.outputs = {"dex_suite": out}
        return [classify]


def dex_suite() -> None:
    print("\n=== 5. Dex triage suite (10 seeded failures, real simulations, real model) ===", flush=True)
    with session() as s:
        prj = Project(id=new_id("prj"), name="M0.6 acceptance")
        s.add(prj)
        s.flush()
        dsn = Design(id=new_id("des"), project_id=prj.id, name="dex_triage_suite", request_text="M0.6 acceptance test 5")
        s.add(dsn)
        s.flush()
        run = create_run(s, dsn, from_stage="verification", to_stage="verification", agent_kind="s2s")
        t = s.scalar(select(Task).where(Task.run_id == run.id))
        t.status, t.title, t.agent_id, t.team_id = "running", "Dex triage suite: 10 seeded failures", "Dex", "debug_triage"
        tid, run_id = t.id, run.id
    o = run_task(tid, DexSuite(), ModelGateway.from_settings())
    with session() as s:
        rows = (s.get(Task, tid).outputs or {}).get("dex_suite", [])
        cost = s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0)).where(UsageRecord.run_id == run_id))
    for row in rows:
        print(f"   {row['id']}  truth {row['truth']:<6}  Dex {row['dex']:<6}  {'OK ' if row['correct'] else 'WRONG'}  "
              f"failing {row['failing_tests']}  | seeded: {row['seeded']}")
        print(f"        Dex root cause: {row['root_cause'][0][:200] if row['root_cause'] else '-'}")
    n = sum(r["correct"] for r in rows)
    print(f"   suite run {run_id}: task {o.status}; cost ${float(cost):.4f}")
    record("5. Dex classifies 10 seeded failures, >= 9 correct", o.status == "completed" and len(rows) == 10 and n >= 9,
           f"{n}/{len(rows)} correct")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for run_id in args:
        per_design(run_id)
    if "--dex" in sys.argv:
        dex_suite()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} acceptance checks passed")
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
