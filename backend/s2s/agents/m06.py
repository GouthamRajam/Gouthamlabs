"""M0.6 verification organization: Zone 2B (test_build) and Zone 2C (verification).

test_build (lead Vera, manager Nadia), written from spec.yaml / arch.yaml and the DUT port list
ONLY (independence rule, 6.7.5: no 2B agent is given any RTL file):
  Vera     tb/testplan.yaml: tests per requirement, functional coverage bins over port names,
           the reference-model transaction format            -> checks: schema, trace, bins parse
  Mira x2  two independent reference models (instances A and B never see each other's model)
           -> N-version check on 2000 seeded random transactions; differences go to Vera
  Proto    a protocol checker with positive and negative self-tests (only for standard protocols)
  Theo     the cocotb testbench (one @cocotb.test per test-plan test, scoreboard vs RefModel)
  Euclid   formal/formal_top.sv: port-level properties, each with its cover (vacuity check)
  Sentinel reviews the plan, testbench and properties; the accepted set is the guard BASELINE.

verification (lead Rex, manager Rhea):
  Rex      regression: Verilator seeds 1-3 with line/toggle coverage + waveforms, Icarus seed 1;
           a failure is re-run on the same seed (different result = flaky = environment bug)
  Euclid   SymbiYosys prove + cover + free-stub (tautology) check
  Dex      triages every failure: DESIGN -> the RTL owner fixes (Lumen re-checks lint), TEST ->
           Theo/Euclid fix (anti-cheating guard on the diff), SPEC -> stop for a human
  Cora     coverage closure: line/toggle from Verilator, functional bins from the waveforms;
           holes closed with new tests, never by removing bins
  Myra     20 screened mutants of the final RTL; missed ones go back (via Nadia) to Theo once
  Guard    the final test set is diffed against the baseline; any weakening needs Sentinel.
Real tools decide every check; agents only write files.
"""
from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import yaml

from s2s.agents import llm
from s2s.agents.m05 import (OWNER_BY_KIND, REPO, _answer_fields, _author_loop, _inputs, _read, _record,
                            _sage_search, _task_result, _write, lumen_checks, stop_if_blocked)
from s2s.agents.runtime import Step, StepContext
from s2s.config import _load
from s2s.design import checks
from s2s.design.schemas import (ADJUDICATE_ANSWER, DEX_ANSWER, REVIEW_ANSWER, TESTPLAN_SCHEMA, WRITER_ANSWER)
from s2s.org import load_org
from s2s.tools import runner
from s2s.tools.cocotb_regress import run_cocotb_regress
from s2s.verify import fcov, guard
from s2s.verify.formal import FormalHarnessError, run_formal
from s2s.verify.mutation_run import MutationHarnessError, run_mutation
from s2s.verify.nversion import run_nversion

SEEDS = [1, 2, 3]
THEO_SINGLE_ANSWER_MAX_TESTS = 12  # larger plans: shared env + tests in batches (one answer cannot hold them)
THEO_BATCH = 6
DEBUG_ROUNDS = 3
MAX_FIX_ATTEMPTS = 3  # an RTL fix that breaks lint gets the tool output back, like the M0.5 RTL loop
CORA_ROUNDS = 2
ALLOWED_IMPORTS = {"cocotb", "random", "math", "itertools", "collections", "dataclasses", "typing", "enum",
                   "functools", "ref_model", "statistics", "operator"}
FORBIDDEN_CALLS = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint"}


def targets() -> dict:
    return _load("coverage_targets.yaml", "S2S_COVERAGE_TARGETS")


def _spec(ctx: StepContext) -> dict:
    return yaml.safe_load(_read(ctx, "spec/spec.yaml"))


def _arch(ctx: StepContext) -> dict:
    return yaml.safe_load(_read(ctx, "arch/arch.yaml"))


def _ports(ctx: StepContext) -> list[dict]:
    return json.loads(_read(ctx, "tb/dut_ports.json"))["ports"]


def _plan(ctx: StepContext) -> dict:
    return yaml.safe_load(_read(ctx, "tb/testplan.yaml"))


def _tb_files(ctx: StepContext) -> dict[str, str]:
    return {f"tb/{p.name}": p.read_text() for p in sorted((ctx.workdir / "tb").glob("*.py"))}


def _test_modules(ctx: StepContext) -> list[str]:
    return [p.stem for p in sorted((ctx.workdir / "tb").glob("test_*.py"))]


def _rtl_files(ctx: StepContext) -> list[Path]:
    return sorted((ctx.workdir / "rtl").glob("*.v"))


def _who(name: str) -> dict:
    return {"agent_id": name, "team": llm.agent(name).team}


def _assign(ctx: StepContext, mgr: str, owner: str, goal: str, exit_criteria: list[str], signal: str) -> None:
    ctx.emit("handoff", f"{mgr} assigned '{goal[:80]}' to {owner}", agent_id=mgr,
             team=load_org().team_of_agent(owner).id, to_agent_id=owner,
             detail={"goal": goal, "exit_criteria": exit_criteria, "budget": llm.agent(owner).budget,
                     "progress_signal": signal})


def _json_report(ctx: StepContext, who: str, path: str, data) -> None:
    _write(ctx, who, [{"path": path, "content": json.dumps(data, indent=2, default=str)}], "report")


# --- static checks on model-written verification code ---------------------------------------------
def _always_true(t: ast.AST) -> bool:
    """`assert True`, `assert x or True`, `assert 1`, `assert x == x`: an assertion that cannot fail."""
    if isinstance(t, ast.Constant):
        return bool(t.value)
    if isinstance(t, ast.BoolOp) and isinstance(t.op, ast.Or):
        return any(_always_true(v) for v in t.values)
    if isinstance(t, ast.Compare) and len(t.ops) == 1 and isinstance(t.ops[0], (ast.Eq, ast.LtE, ast.GtE)):
        return ast.dump(t.left) == ast.dump(t.comparators[0])
    return False


def tb_static_problems(files: dict[str, str], plan: dict | None, test_files_only: bool = False) -> list[str]:
    """Parse (never import) every testbench file: allowed imports, no file/exec access, and every
    test-plan test present as a @cocotb.test function."""
    p: list[str] = []
    found: set[str] = set()
    for path, text in files.items():
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            p.append(f"{path}:{e.lineno}: syntax error: {e.msg}")
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                mods = [(n.module or "").split(".")[0]]
            else:
                mods = []
            for m in mods:
                if m not in ALLOWED_IMPORTS and not m.startswith(("proto_", "tb_")):
                    p.append(f"{path}:{n.lineno}: import '{m}' is not allowed in the testbench")
            if isinstance(n, ast.Assert) and _always_true(n.test):
                p.append(f"{path}:{n.lineno}: assertion can never fail ({ast.unparse(n.test)[:80]})")
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FORBIDDEN_CALLS:
                p.append(f"{path}:{n.lineno}: call to {n.func.id}() is not allowed (no file or code access)")
            if isinstance(n, ast.Attribute) and n.attr in ("system", "popen", "_sub_handles") :
                p.append(f"{path}:{n.lineno}: attribute .{n.attr} is not allowed")
        if Path(path).name.startswith("test_"):
            found |= set(guard.analyze_tests(text))
    if plan is not None:
        names = {t["name"] for r in plan["requirements"] for t in r["tests"] if t["kind"] != "formal"}
        for n in sorted(names - found):
            p.append(f"test-plan test '{n}' has no @cocotb.test function of that name")
    return p


# --- Zone 2B: test_build ----------------------------------------------------------------------
def validate_testplan(ctx: StepContext) -> list[str]:
    try:
        plan = yaml.safe_load(_read(ctx, "tb/testplan.yaml"))
    except (FileNotFoundError, yaml.YAMLError) as e:
        problems = [f"tb/testplan.yaml: {e}"]
        _record(ctx, "testplan_schema", problems, "jsonschema", "Vera")
        return problems
    problems = checks.schema_problems(plan, TESTPLAN_SCHEMA, "testplan.yaml")
    _record(ctx, "testplan_schema", problems, "jsonschema", "Vera")
    if problems:
        return problems
    spec, ports = _spec(ctx), {p["name"] for p in _ports(ctx)}
    trace: list[str] = []
    req_ids = {r["id"] for r in spec["requirements"]}
    planned = {r["id"] for r in plan["requirements"] if r["tests"]}
    trace += [f"{r} has no test in the plan" for r in sorted(req_ids - planned)]
    trace += [f"plan lists {r}, which is not in the spec" for r in sorted(planned - req_ids)]
    names = [t["name"] for r in plan["requirements"] for t in r["tests"]]
    trace += [f"test name '{n}' is used more than once" for n in sorted({n for n in names if names.count(n) > 1})]
    for key in ("clock",):
        if plan[key] not in ports:
            trace.append(f"clock '{plan[key]}' is not a DUT port")
    if plan["reset"]["name"] not in ports:
        trace.append(f"reset '{plan['reset']['name']}' is not a DUT port")
    for b in plan["coverage_bins"]:
        try:
            fcov.compile_expr(b["expr"], ports)
        except fcov.BadExpression as e:
            trace.append(f"coverage bin '{b['name']}': {e}")
        if b["req"] not in req_ids:
            trace.append(f"coverage bin '{b['name']}' traces to unknown {b['req']}")
    _record(ctx, "testplan_trace", trace, "s2s.agents.m06", "Vera")
    return trace


def _validate_model(which: str):
    def v(ctx: StepContext) -> list[str]:
        path = ctx.workdir / f"tb/ref_model_{which}.py"
        probs = tb_static_problems({f"tb/ref_model_{which}.py": path.read_text()}, None) if path.exists() \
            else [f"tb/ref_model_{which}.py was not written"]
        if not probs and "class RefModel" not in path.read_text():
            probs = ["no class RefModel"]
        _record(ctx, f"ref_model_{which}_static", probs, "python ast", "Mira")
        return probs
    return v


def validate_tb(ctx: StepContext) -> list[str]:
    files = {k: v for k, v in _tb_files(ctx).items() if Path(k).name.startswith(("test_", "tb_"))}
    probs = tb_static_problems(files, _plan(ctx)) if files else ["no tb/test_*.py written"]
    _record(ctx, "testbench_static", probs, "python ast", "Theo")
    return probs


def validate_props(ctx: StepContext) -> list[str]:
    from s2s.verify.formal import lint_properties, stub_module
    path = ctx.workdir / "formal/formal_top.sv"
    if not path.exists():
        probs = ["formal/formal_top.sv was not written"]
    else:
        _, probs = lint_properties(path.read_text())
        if not probs:  # it must elaborate against the DUT's port list (a stub: no RTL is read)
            stub = ctx.workdir / "formal/stub" / f"{_arch(ctx)['top']}.v"
            stub.parent.mkdir(parents=True, exist_ok=True)
            stub.write_text(stub_module(_arch(ctx)["top"], _ports(ctx)))
            rec = runner.run(["yosys", "-p", f"read_verilog -formal -sv {stub.resolve()} {path.resolve()}; "
                              "hierarchy -check -top formal_top; proc"], ctx.workdir,
                             ctx.workdir / "logs/formal_parse.log", "yosys", 120)
            if rec.exit_code != 0:
                log = Path(rec.log_path).read_text()
                probs = [ln.strip() for ln in log.splitlines() if "ERROR" in ln][:5] or [f"yosys exit {rec.exit_code}"]
    _record(ctx, "formal_properties_static", probs, "yosys", "Euclid")
    return probs


TB_CONTRACT = """TESTBENCH CONTRACT (the runtime runs it; you cannot):
- cocotb 1.9 (Python 3.11), simulators Verilator 5.018 and Icarus. Files: tb/test_<name>.py (tests),
  optional helpers tb/tb_<name>.py. Imports allowed: cocotb, random, math, itertools, collections,
  dataclasses, typing, enum, functools, statistics, operator, ref_model, proto_*, tb_*. No file access,
  no os/sys/subprocess, no eval/exec.
- One `@cocotb.test(timeout_time=<n>, timeout_unit="ms")` async function per test-plan test, with
  EXACTLY the test-plan name. Each test starts its own clock (cocotb.clock.Clock) on the plan's clock
  port, applies reset itself, drives inputs on the falling edge and checks outputs after the rising
  edge (await RisingEdge, then await ReadOnly() before reading; never write in ReadOnly).
- Use `random` for stimulus (cocotb seeds it; every failure must be reproducible from the seed).
- Expected values come from `from ref_model import RefModel` (the reference model), never from
  reading the DUT. Assertion messages must give cycle, inputs, expected and actual.
- Connect only to the DUT ports listed in tb/dut_ports.json. Keep each test under ~60 s wall time.
"""

FORMAL_CONTRACT = """FORMAL CONTRACT (open-source Yosys/SymbiYosys, Verilog formal style; no bind support):
- Write formal/formal_top.sv: `module formal_top(<every DUT input as an input port>);` that declares
  the DUT outputs as wires and instantiates the DUT by port name (named connections only). Do NOT
  reference DUT internals (no dut.<signal>): properties are on ports only (independence rule).
- Open-source Yosys (no Verific): only immediate assert/assume/cover inside always blocks. NO `->`,
  `|->`, `|=>`, `##`, sequences, `property ... endproperty` or `bind`. Write an implication a -> b as
  `(!(a) || (b))`.
- Use `reg past_valid = 1'b0; always @(posedge <clk>) past_valid <= 1'b1;` and `$past()`.
- Reset: assume reset is active in the first cycle (e.g. `always @(*) if (!past_valid) am_reset: assume(<reset active>);`).
- Every property is a LABELLED pair inside `always @(posedge <clk>) if (past_valid) begin ... end`:
    ap_<name>: assert(<property>);   cp_<name>: cover(<the condition that triggers it>);
  Assumptions: am_<name>: assume(...), each justified from the spec in a comment. At least 3
  properties that matter (reset values, no overflow/underflow, protocol rules, data integrity).
- The runtime runs prove (k-induction) and cover (vacuity) at depth {depth}, and a check that each
  property FAILS when the DUT is replaced by a stub with free outputs (a property that holds without
  the design is a tautology and does not count).
"""


def test_build_steps() -> list[Step]:
    def setup(ctx: StepContext) -> None:
        src = ctx.task.inputs.get("source_run")
        from s2s.agents.runtime import artifact_dir
        root = artifact_dir() / "runs" / src
        ctx.workdir.mkdir(parents=True, exist_ok=True)
        for d in ("spec", "arch", "rtl"):
            shutil.copytree(root / d, ctx.workdir / d, dirs_exist_ok=True)
        for f in ("request.md", "reports/standards.md"):
            if (root / f).exists():
                (ctx.workdir / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(root / f, ctx.workdir / f)
        arch = _arch(ctx)
        # The DUT port list, extracted by Yosys: the ONLY view of the RTL the 2B agents get.
        out = ctx.workdir / "logs/dut_ports_yosys.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        srcs = " ".join(str(f.resolve()) for f in _rtl_files(ctx))
        rec = runner.run(["yosys", "-q", "-p", f"read_verilog -sv {srcs}; hierarchy -check -top {arch['top']}; "
                          f"proc; write_json {out.resolve()}"], ctx.workdir, ctx.workdir / "logs/dut_ports.log", "yosys", 300)
        mod = json.loads(out.read_text())["modules"][arch["top"]]
        ports = [{"name": n, "dir": {"input": "in", "output": "out", "inout": "inout"}[x["direction"]],
                  "width": len(x["bits"])} for n, x in mod["ports"].items()]
        p = ctx.workdir / "tb/dut_ports.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"top": arch["top"], "ports": ports, "source": "yosys write_json (ports only)"}, indent=2))
        ctx.artifact("tb", "tb/dut_ports.json", p.read_bytes(), agent_id="Vera")
        ctx.check("dut_port_list", "yosys", rec.exit_code == 0, {"ports": len(ports)}, agent_id="Vera",
                  team=llm.agent("Vera").team)
        ctx.state.update({"top": arch["top"], "design": _spec(ctx)["design"]})
        ctx.emit("plan", "Vera: plan - test plan from the spec (every requirement traced, coverage bins on port "
                 "names); two independent reference models (Mira A/B, N-version check); protocol checker if a "
                 "standard applies (Proto); cocotb testbench (Theo); formal properties (Euclid); Sentinel review",
                 **_who("Vera"))
        mgr = "Nadia"
        for owner, goal in (("Vera", "Write the test plan from spec.yaml"), ("Mira", "Two independent reference models"),
                            ("Theo", "cocotb testbench for every test-plan test"),
                            ("Euclid", "Port-level formal properties with covers")):
            _assign(ctx, mgr, owner, goal, ["deterministic checks pass", "no RTL read"], "files passing checks / files")

    def vera(ctx: StepContext) -> None:
        _author_loop(ctx, "Vera", goal="Write tb/testplan.yaml: for every requirement the tests that prove it "
                     "(name test_<snake>, kind directed|random|formal, description incl. corner cases), coverage_bins "
                     "as boolean expressions over DUT PORT NAMES sampled at the clock edge (e.g. 'count == 255 and "
                     "enable'), each traced to a requirement, and the reference-model `transaction` (input fields "
                     "with bit widths, the outputs it predicts).",
                     inputs=["spec/spec.yaml", "spec/spec.md", "arch/arch.yaml", "tb/dut_ports.json"],
                     validate=validate_testplan, kind="testplan",
                     constraints="tb/testplan.yaml JSON Schema:\n" + json.dumps(TESTPLAN_SCHEMA, indent=1)
                     + "\nRules: no RTL is available to you (independence rule). Bins must be reachable through "
                     "the ports. The transaction is what RefModel.step(txn) consumes and returns "
                     "(fields: name -> width; outputs: names). Tests of kind 'formal' are proven by Euclid, not simulated.")

    def mira(ctx: StepContext) -> None:
        plan = _plan(ctx)
        contract = ("REFERENCE MODEL CONTRACT: tb/ref_model_{x}.py defines `class RefModel` with `reset()` and "
                    "`step(txn: dict) -> dict`. `txn` has exactly these fields (ints): "
                    + json.dumps(plan["transaction"]["fields"]) + "; the result must contain exactly these keys: "
                    + json.dumps(plan["transaction"]["outputs"]) + ". Plain Python, no imports except math, "
                    "collections, dataclasses, typing, enum. Model the spec at transaction level, including reset, "
                    "error and corner behavior. You have NO access to the RTL.")
        for x in ("a", "b"):
            ctx.emit("tool_call", f"Mira (instance {x.upper()}) writes reference model {x.upper()} independently",
                     **_who("Mira"))
            _author_loop(ctx, "Mira", goal=f"Write tb/ref_model_{x}.py: the golden reference model, from the spec "
                         "and the test plan's transaction format only.",
                         inputs=["spec/spec.yaml", "tb/testplan.yaml"], validate=_validate_model(x), kind="ref_model",
                         constraints=contract.replace("{x}", x))
            if ctx.state.get("blocked"):
                return
        res = run_nversion(ctx.workdir, ctx.workdir / "tb/ref_model_a.py", ctx.workdir / "tb/ref_model_b.py",
                           plan["transaction"])
        _json_report(ctx, "Vera", "reports/nversion.json", res)
        ctx.emit("tool_result", f"N-version: {res['steps']} transactions, {res.get('total_mismatches', 0)} difference(s)"
                 + (f", errors: {res['errors'][0][:120]}" if res["errors"] else ""), **_who("Mira"),
                 detail={"tool": "nversion", **{k: v for k, v in res.items() if k != "mismatches"}})
        decision = "model_a"
        if res["errors"] or res.get("total_mismatches"):
            data = llm.ask(ctx, "Vera", goal="The two independent reference models disagree (or one crashed). Decide "
                           "from the SPEC which model is right, or raise a spec question if the spec does not decide it.",
                           inputs=_inputs(ctx, ["spec/spec.yaml", "tb/testplan.yaml", "tb/ref_model_a.py",
                                                "tb/ref_model_b.py", "reports/nversion.json"]),
                           exit_criteria=["decision justified by spec requirement ids"], schema=ADJUDICATE_ANSWER)
            _answer_fields(ctx, "Vera", data)
            decision = data["decision"]
            ctx.emit("finding" if decision == "spec_question" else "handoff",
                     f"Vera: N-version decision {decision}: {data['reason'][:200]}", **_who("Vera"),
                     detail={"decision": decision, "reason": data["reason"], "spec_question": data["spec_question"]})
            if decision == "spec_question":
                ctx.state["blocked"] = f"spec question from the N-version check: {data['spec_question']}"
                _record(ctx, "nversion_agreement", [data["spec_question"]], "nversion", "Vera")
                return
        chosen = "a" if decision == "model_a" else "b"
        shutil.copy(ctx.workdir / f"tb/ref_model_{chosen}.py", ctx.workdir / "tb/ref_model.py")
        ctx.artifact("ref_model", "tb/ref_model.py", (ctx.workdir / "tb/ref_model.py").read_bytes(), agent_id="Vera")
        # passes when both models agree, or when Vera decided a difference from the spec (her reason is recorded)
        _record(ctx, "nversion_agreement", [], "nversion", "Vera")
        ctx.state["nversion"] = {"steps": res["steps"], "mismatches": res.get("total_mismatches", 0),
                                 "errors": len(res["errors"]), "decision": decision}

    def proto(ctx: StepContext) -> None:
        spec = _spec(ctx)
        protos = sorted({i["protocol"] for i in spec["interfaces"] if i.get("protocol")})
        if not protos:
            ctx.emit("plan", "Proto: no interface names a standard protocol; no protocol checker needed", **_who("Proto"))
            return
        _assign(ctx, "Nadia", "Proto", f"Protocol checker for {', '.join(protos)}", ["self-tests pass, incl. negative"],
                "self-tests passing")

        def validate(c: StepContext) -> list[str]:
            files = {f"tb/{p.name}": p.read_text() for p in sorted((c.workdir / "tb").glob("proto_*.py"))}
            probs = tb_static_problems(files, None) if files else ["no tb/proto_*.py written"]
            if not probs:
                code = "import json,sys; sys.path.insert(0,'tb'); " + "; ".join(
                    f"import {Path(f).stem} as m{i}; r{i}=m{i}.selftest(); assert r{i}['negative']>=1, 'no negative test'"
                    for i, f in enumerate(files) if hasattr(ast, "parse") and "def selftest" in files[f]) + "; print('S2S_PROTO_OK')"
                rec = runner.run(["/opt/cocotb/bin/python3", "-c", code], c.workdir, c.workdir / "logs/proto_selftest.log",
                                 "cocotb", 300)
                log = Path(rec.log_path).read_text()
                if "S2S_PROTO_OK" not in log:
                    probs = ["protocol checker self-test failed or missing selftest(): " + log[-600:]]
            _record(c, "protocol_checker_selftest", probs, "python", "Proto")
            return probs
        _author_loop(ctx, "Proto", goal=f"Write a reusable protocol checker for {', '.join(protos)} as "
                     "tb/proto_<name>.py: a monitor class Theo can feed with sampled pin values, which raises on a "
                     "protocol violation, and `def selftest() -> dict` that runs positive AND negative tests (negative "
                     "tests must make the checker fire) and returns {'positive': n, 'negative': m}. Cite the standard "
                     "section each rule enforces.", inputs=["spec/spec.yaml", "tb/dut_ports.json", "tb/testplan.yaml"],
                     validate=validate, kind="vip",
                     constraints="Plain Python (imports: math, collections, dataclasses, typing, enum). No RTL access.")

    def theo(ctx: StepContext) -> None:
        protos = [f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("proto_*.py"))]
        base = ["spec/spec.yaml", "arch/arch.yaml", "tb/dut_ports.json", "tb/testplan.yaml", "tb/ref_model.py", *protos]
        d = ctx.state["design"]
        tests = [t["name"] for r in _plan(ctx)["requirements"] for t in r["tests"] if t["kind"] != "formal"]
        if len(tests) <= THEO_SINGLE_ANSWER_MAX_TESTS:
            _author_loop(ctx, "Theo", goal=f"Write the cocotb testbench tb/test_{d}.py implementing EVERY test in "
                         "tb/testplan.yaml (same names), with a scoreboard against RefModel, constrained-random plus "
                         "directed corner cases (reset during operation, min/max values, simultaneous events).",
                         inputs=base, validate=validate_tb, kind="testbench", constraints=TB_CONTRACT)
            return
        # A large plan does not fit one answer: the shared environment first, then the tests in batches.
        env = f"tb/tb_{d}.py"

        def v_env(c: StepContext) -> list[str]:
            f = c.workdir / env
            probs = tb_static_problems({env: f.read_text()}, None) if f.exists() else [f"{env} was not written"]
            if not probs and guard.analyze_tests(f.read_text()):
                probs = [f"{env} must not contain @cocotb.test functions (tests go in the batch files)"]
            _record(c, "testbench_env_static", probs, "python ast", "Theo")
            return probs
        _author_loop(ctx, "Theo", goal=f"Write ONLY the shared verification environment {env} (no tests): clock and "
                     "reset helpers, drivers, monitors and a scoreboard that compares the DUT against RefModel (and "
                     "the protocol checker if any), as functions/classes the test files will import. The tests "
                     f"themselves ({len(tests)} of them) are written next, in batches, and import this module.",
                     inputs=base, validate=v_env, kind="testbench", constraints=TB_CONTRACT)
        if ctx.state.get("blocked"):
            return
        for k, i in enumerate(range(0, len(tests), THEO_BATCH), 1):
            names = tests[i:i + THEO_BATCH]
            path = f"tb/test_{d}_{k}.py"

            def v_batch(c: StepContext, path=path, names=names) -> list[str]:
                f = c.workdir / path
                probs = tb_static_problems({path: f.read_text()}, None) if f.exists() else [f"{path} was not written"]
                if not probs:
                    missing = sorted(set(names) - set(guard.analyze_tests(f.read_text())))
                    probs = [f"{path}: test '{n}' missing" for n in missing]
                _record(c, "testbench_batch_static", probs, "python ast", "Theo")
                return probs
            _author_loop(ctx, "Theo", goal=f"Write {path} with exactly these test-plan tests (same names), each a "
                         f"@cocotb.test using the shared environment from {env}: {', '.join(names)}.",
                         inputs=[*base, env], validate=v_batch, kind="testbench", constraints=TB_CONTRACT)
            if ctx.state.get("blocked"):
                return
        validate_tb(ctx)  # every test-plan test present across the files

    def euclid(ctx: StepContext) -> None:
        _author_loop(ctx, "Euclid", goal="Write formal/formal_top.sv with at least 3 meaningful port-level "
                     "properties (reset values, no overflow/underflow, protocol rules, data integrity), each with "
                     "its cover, and justified assumptions.",
                     inputs=["spec/spec.yaml", "arch/arch.yaml", "tb/dut_ports.json", "tb/testplan.yaml"],
                     validate=validate_props, kind="formal",
                     constraints=FORMAL_CONTRACT.replace("{depth}", str(targets()["formal_min_depth"])))

    def sentinel(ctx: StepContext) -> None:
        files = ["spec/spec.yaml", "tb/testplan.yaml", "tb/ref_model.py", "formal/formal_top.sv",
                 *[f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("test_*.py"))]]
        sent = llm.agent("Sentinel")
        data = llm.ask(ctx, sent, goal="Review the verification plan, testbench and formal properties: tests that "
                       "cannot fail, weak scoreboards, coverage bins that do not correspond to requirements, "
                       "vacuous or over-constrained formal assumptions. Mark 'blocking' only what would let a real "
                       "bug through.", inputs=_inputs(ctx, files),
                       exit_criteria=["every finding specific: file, location, evidence, suggested action"],
                       schema=REVIEW_ANSWER, extra_note="Put each finding in `findings` (empty list if none). ")
        _json_report(ctx, "Sentinel", "reports/sentinel_tests.json", data["findings"])
        for f in data["findings"]:
            ctx.emit("finding", f"Sentinel [{f['severity']}] {f['target']}: {f['what'][:200]}", **_who("Sentinel"),
                     to_agent_id="Vera", detail=f)
        blocking = [f for f in data["findings"] if f["severity"] == "blocking"]
        if blocking:
            prev = "Sentinel filed these blocking findings:\n" + json.dumps(blocking, indent=2)
            by_file = {"Euclid": [f for f in blocking if ".sv" in f["target"]],
                       "Theo": [f for f in blocking if ".sv" not in f["target"]]}
            rejected_before = len(ctx.state.get("guard_rejections", []))
            if by_file["Theo"]:
                theo_revise(ctx, prev)
            if by_file["Euclid"]:
                _author_loop(ctx, "Euclid", goal="Revise formal/formal_top.sv to resolve the blocking findings.",
                             inputs=["spec/spec.yaml", "tb/dut_ports.json", "tb/testplan.yaml", "formal/formal_top.sv",
                                     "reports/sentinel_tests.json"], validate=validate_props, kind="formal", previous=prev,
                             constraints=FORMAL_CONTRACT.replace("{depth}", str(targets()["formal_min_depth"])))
            open_ = ([f"{f['target']}: {f['what'][:160]} (fix rejected by the anti-cheating guard)" for f in by_file["Theo"]]
                     if len(ctx.state.get("guard_rejections", [])) > rejected_before else [])
            _record(ctx, "sentinel_tests_review", open_, "sentinel", "Sentinel")
            return
        _record(ctx, "sentinel_tests_review", [], "sentinel", "Sentinel")

    def baseline(ctx: StepContext) -> None:
        """The accepted verification set: the anti-cheating guard's reference from now on."""
        files = {**_tb_files(ctx), "tb/testplan.yaml": _read(ctx, "tb/testplan.yaml"),
                 "formal/formal_top.sv": _read(ctx, "formal/formal_top.sv")}
        snap = ctx.workdir / "guard_baseline"
        shutil.rmtree(snap, ignore_errors=True)
        for path, text in files.items():
            (snap / path).parent.mkdir(parents=True, exist_ok=True)
            (snap / path).write_text(text)
        ctx.state["baseline_files"] = sorted(files)
        ctx.evidence = f"baseline: {len(files)} verification files"

    return [setup, vera, stop_if_blocked, mira, stop_if_blocked, proto, theo, euclid, stop_if_blocked, sentinel,
            stop_if_blocked, baseline, lambda c: _task_result(c, "test_build")]


# --- guarded revisions -------------------------------------------------------------------------
def _snapshot(ctx: StepContext) -> dict[str, str]:
    snap = {**_tb_files(ctx)}
    for p in ("tb/testplan.yaml", "formal/formal_top.sv"):
        if (ctx.workdir / p).exists():
            snap[p] = _read(ctx, p)
    return snap


def guarded(ctx: StepContext, author: str, change, reason: str) -> list[str]:
    """Run `change()` (an agent rewriting verification files); diff before/after with the
    anti-cheating guard. Flags go to Sentinel; rejected changes are reverted."""
    before = _snapshot(ctx)
    change()
    after = _snapshot(ctx)
    flags = guard.diff_files(before, after)
    ctx.state.setdefault("guard_events", []).append({"author": author, "reason": reason, "flags": flags})
    if not flags:
        ctx.check("anti_cheat_guard", "s2s.verify.guard", True, {"flags": 0, "author": author}, **_who("Sentinel"))
        return []
    ctx.emit("finding", f"Anti-cheating guard: {author}'s change weakens verification ({len(flags)} flag(s)); "
             "Sentinel review required", **_who("Sentinel"), to_agent_id=author,
             detail={"severity": "blocking", "flags": flags, "reason": reason})
    data = llm.ask(ctx, "Sentinel", goal="The anti-cheating guard flagged this verification change as weakening. "
                   "Approve ONLY if each flagged change is a correction of a test that was itself wrong per the spec "
                   "(cite the requirement); otherwise file a blocking finding.",
                   inputs={"spec/spec.yaml": _read(ctx, "spec/spec.yaml"),
                           **{f"reports/guard_before_{Path(k).name}.txt": before[k] for k in before if k in after and before[k] != after[k]},
                           **{k: after[k] for k in after if k in before and before[k] != after[k]}},
                   exit_criteria=["approve only spec-justified corrections"], schema=REVIEW_ANSWER,
                   previous_attempts="Guard flags:\n- " + "\n- ".join(flags) + f"\nAuthor's reason: {reason}")
    blocking = [f for f in data["findings"] if f["severity"] == "blocking"]
    approved = not blocking
    ctx.check("anti_cheat_guard", "s2s.verify.guard", approved, {"flags": len(flags), "detail": flags,
              "sentinel": "approved" if approved else "rejected"}, **_who("Sentinel"))
    if not approved:
        outputs = ctx.state.setdefault("outputs", {})
        for path, text in before.items():
            if after.get(path) != text:
                (ctx.workdir / path).write_text(text)
                outputs[path] = ctx.artifact("reverted", path, text.encode(), agent_id="Sentinel")
        for path in set(after) - set(before):
            (ctx.workdir / path).unlink()
            outputs.pop(path, None)
        ctx.emit("escalation", f"Sentinel rejected {author}'s weakened change; reverted", **_who("Sentinel"),
                 to_agent_id="human", detail={"flags": flags, "findings": blocking})
        ctx.state.setdefault("guard_rejections", []).append({"author": author, "flags": flags})
    else:
        ctx.state.setdefault("guard_approvals", []).append({"author": author, "flags": flags,
                                                            "sentinel": [f["what"] for f in data["findings"]]})
    return flags


def theo_revise(ctx: StepContext, previous: str) -> None:
    protos = [f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("proto_*.py"))]
    tbs = [f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("test_*.py")) if not p.name.startswith("test_cora_")]
    tbs += [f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("tb_*.py"))]
    extras = [p for p in ("reports/sentinel_tests.json", "reports/mutation_missed.json") if (ctx.workdir / p).exists()]
    extras += [f"reports/{p.name}" for p in sorted((ctx.workdir / "reports").glob("bug_*.json"))]
    guarded(ctx, "Theo", lambda: _author_loop(
        ctx, "Theo", goal="Revise the testbench as described. Return ONLY the files you change (full content). Never "
        "delete a test, assertion or check, never reduce iterations, never add skip/expect_fail: the anti-cheating "
        "guard rejects weakening.",
        inputs=["spec/spec.yaml", "arch/arch.yaml", "tb/dut_ports.json", "tb/testplan.yaml", "tb/ref_model.py",
                *protos, *tbs, *extras], validate=validate_tb, kind="testbench", previous=previous,
        constraints=TB_CONTRACT), previous[:300])


def reclassify_bin(ctx: StepContext, bin_name: str, reason: str) -> None:
    """Operator decision: a coverage bin that can never be hit is a must-never-happen state. Vera moves it
    from coverage_bins to illegal_states and Euclid proves it never happens; one guarded change, which
    Sentinel must approve (the guard flags the removed bin)."""
    plan = _plan(ctx)
    b = next((x for x in plan["coverage_bins"] if x["name"] == bin_name), None)
    if b is None:
        raise ValueError(f"coverage bin {bin_name!r} is not in the test plan")
    assertion = f"never_{bin_name}"
    _assign(ctx, "Nadia", "Vera", f"Reclassify bin {bin_name} as an illegal state (operator decision)",
            ["bin moved to illegal_states", f"Euclid proves ap_{assertion}"], "files passing checks")

    def v_plan(c: StepContext) -> list[str]:
        probs = validate_testplan(c)
        p = _plan(c) if not probs else {}
        if not probs:
            if any(x["name"] == bin_name for x in p["coverage_bins"]):
                probs.append(f"coverage bin {bin_name} is still a coverage bin")
            st = next((x for x in p.get("illegal_states") or [] if x["name"] == bin_name), None)
            if st is None:
                probs.append(f"illegal_states has no entry {bin_name}")
            elif st["assertion"] != assertion:
                probs.append(f"illegal state {bin_name} must name assertion {assertion}")
            else:
                try:
                    fcov.compile_expr(st["expr"], {x["name"] for x in _ports(c)})
                except fcov.BadExpression as e:
                    probs.append(f"illegal state {bin_name}: {e}")
        return probs

    def v_props(c: StepContext) -> list[str]:
        probs = validate_props(c)
        if not probs and f"ap_{assertion}" not in _read(c, "formal/formal_top.sv"):
            probs.append(f"formal/formal_top.sv has no ap_{assertion}")
        return probs

    def change() -> None:
        _author_loop(ctx, "Vera", goal=f"Operator decision: coverage bin '{bin_name}' ({b['expr']}) can never be hit by a "
                     "correct design; it is a must-never-happen state, not a coverage target. Move it from coverage_bins "
                     f"to a new top-level list `illegal_states` as {{name: {bin_name}, expr: <same condition>, req: "
                     f"{b['req']}, assertion: {assertion}, reason: <one sentence>}}. Change NOTHING else in the plan.",
                     inputs=["spec/spec.yaml", "tb/dut_ports.json", "tb/testplan.yaml"], validate=v_plan, kind="testplan",
                     previous=f"Reason from the operator: {reason}",
                     constraints="tb/testplan.yaml JSON Schema:\n" + json.dumps(TESTPLAN_SCHEMA, indent=1))
        if ctx.state.get("blocked"):
            return
        _author_loop(ctx, "Euclid", goal=f"Add ONE property to formal/formal_top.sv: ap_{assertion} asserting that the "
                     f"illegal state never happens ({b['expr']}, on ports), with a cover cp_{assertion} whose trigger is "
                     "reachable (e.g. the FIFO is full, or it is empty) so the vacuity check is meaningful. Keep every "
                     "existing property, cover and assumption unchanged.",
                     inputs=["spec/spec.yaml", "tb/dut_ports.json", "tb/testplan.yaml", "formal/formal_top.sv"],
                     validate=v_props, kind="formal",
                     constraints=FORMAL_CONTRACT.replace("{depth}", str(targets()["formal_min_depth"])))
    guarded(ctx, "Vera", change, f"operator decision: reclassify coverage bin {bin_name} as an illegal-state "
            f"assertion ap_{assertion} (not a waiver: it is now proven never to happen). {reason}")
    rejected = [g for g in ctx.state.get("guard_rejections", []) if g["author"] == "Vera"]
    if rejected:
        ctx.state["blocked"] = f"Sentinel rejected the reclassification of {bin_name}"


# --- Zone 2C: verification ---------------------------------------------------------------------
def regress_timeout_s() -> float:
    """Harness capacity for one regression (all seeds + Icarus): S2S_REGRESS_TIMEOUT_S, default 2400 s.
    A regression whose tests pass runs full length (uart: ~14 min per seed), so long designs need more."""
    import os
    return float(os.environ.get("S2S_REGRESS_TIMEOUT_S", "2400"))


def _regress(ctx: StepContext, name: str, seeds=SEEDS, sims=("verilator", "icarus")):
    who = _who("Rex")
    mods = _test_modules(ctx)
    ctx.beat(f"regression {name} started")
    ctx.emit("tool_call", f"Rex: regression {name}: {', '.join(mods)} x seeds {list(seeds)} ({', '.join(sims)})",
             status="working", detail={"tool": "cocotb_regress", "seeds": list(seeds)}, **who)
    r = run_cocotb_regress(_rtl_files(ctx), ctx.state["top"], ",".join(mods), ctx.workdir / "tb", ctx.workdir,
                           f"sim/{name}", list(seeds), simulators=sims, coverage=True, waves=True,
                           timeout_s=regress_timeout_s())
    ctx.compute("cocotb_regress", r.duration_s or 0.0, agent_id="Rex")
    ctx.beat(f"regression {name}: {r.metrics.get('test_runs', 0) - r.metrics.get('failed_runs', 0)}/"
             f"{r.metrics.get('test_runs', 0)} test runs passed")
    m = r.metrics
    ctx.emit("tool_result", f"Rex: {name}: {m.get('test_runs', 0) - m.get('failed_runs', 0)}/{m.get('test_runs', 0)} "
             f"test runs passed; line {m.get('line_coverage')}, toggle {m.get('toggle_coverage')} ({r.status})",
             detail={"tool": "cocotb_regress", "status": r.status, "reasons": r.reasons[:5],
                     "tests": m.get("tests_by_name"), "line": m.get("line_coverage"), "toggle": m.get("toggle_coverage"),
                     "tool_version": r.tool_version, "env_hash": r.env_hash}, **who)
    return r


def _failures(r) -> list[dict]:
    out = [{"kind": "simulation", "message": i.message} for i in r.errors]
    if not r.passed and not r.errors:
        out.append({"kind": "harness", "message": "; ".join(r.reasons[:3] + r.stage_failures[:3])})
    return out


def _formal(ctx: StepContext) -> dict:
    who = _who("Euclid")
    ctx.beat("formal run started")
    ctx.emit("tool_call", "Euclid: SymbiYosys prove + cover + free-stub check", status="working",
             detail={"tool": "sby"}, **who)
    try:
        f = run_formal(ctx.workdir, _rtl_files(ctx), ctx.workdir / "formal/formal_top.sv",
                       int(targets()["formal_min_depth"]), top=ctx.state["top"], ports=_ports(ctx))
    except FormalHarnessError as e:
        f = {"error": str(e), "properties": {}, "proven_meaningful": 0, "failed": [], "vacuous": [], "tautologies": []}
    ctx.emit("tool_result", f"Euclid: {f.get('proven_meaningful', 0)} meaningful properties proven; failed "
             f"{f.get('failed')}; vacuous {f.get('vacuous')}; tautologies {f.get('tautologies')}",
             detail={"tool": "sby", **{k: v for k, v in f.items() if k != "runs"}}, **who)
    _json_report(ctx, "Euclid", "reports/formal_report.json", f)
    ctx.beat(f"formal: {f.get('proven_meaningful', 0)} meaningful proven")
    return f


def _dex(ctx: StepContext, failures: list[dict], rnd: int) -> list[dict]:
    """Dex triages; returns the bugs (B.7-like) with their routing."""
    _assign(ctx, "Rhea", "Dex", f"Triage {len(failures)} failure(s), round {rnd}", ["every failure classified"],
            "failures classified / failures")
    report = {"round": rnd, "failures": failures}
    _json_report(ctx, "Rex", f"reports/regression_failures_{rnd}.json", report)
    files = ["spec/spec.yaml", "arch/arch.yaml", "tb/testplan.yaml", "tb/ref_model.py", "formal/formal_top.sv",
             *[f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("test_*.py"))],
             *[f"rtl/{p.name}" for p in _rtl_files(ctx)], f"reports/regression_failures_{rnd}.json"]
    data = llm.ask(ctx, "Dex", goal="Classify every failure as DESIGN (RTL wrong vs spec), TEST (testbench, reference "
                   "model or formal property wrong vs spec) or SPEC (the spec does not decide the behavior). Give a "
                   "one-sentence root cause and evidence. For DESIGN name the RTL module to fix. For TEST describe "
                   "the fix in terms of ports and spec requirements only (the test side may not see RTL internals).",
                   inputs=_inputs(ctx, files), exit_criteria=["every failure explained by exactly one bug"],
                   schema=DEX_ANSWER)
    _answer_fields(ctx, "Dex", data)
    bugs = data["bugs"]
    for i, b in enumerate(bugs, 1):
        b["bug_id"] = f"bug_{rnd}_{i}"
        b["found_by"] = "Dex"
        _json_report(ctx, "Dex", f"reports/bug_{rnd}_{i}.json", b)
        route = {"DESIGN": OWNER_BY_KIND.get(next((m["kind"] for m in _arch(ctx)["modules"] if m["name"] == b["module"]),
                                                  "datapath"), "Ada"),
                 "TEST": "Euclid" if any(f.startswith("ap_") or "formal" in f for f in b["failures"]) else "Theo",
                 "SPEC": "human"}[b["classification"]]
        b["routed_to"] = route
        ctx.emit("finding", f"Dex [{b['classification']}] {b['requirement']}: {b['root_cause'][:180]} -> {route}",
                 **_who("Dex"), to_agent_id=route, detail=b)
    ctx.state.setdefault("bugs", []).extend(bugs)
    return bugs


def _fix(ctx: StepContext, bug: dict) -> None:
    prev = "Bug report from Dex (Appendix B.7):\n" + json.dumps(bug, indent=2)
    if bug["classification"] == "DESIGN":
        owner, mod = bug["routed_to"], bug["module"]
        coding_std = (REPO / "docs" / "coding_standard.md").read_text()
        before = {p.name: p.read_text() for p in _rtl_files(ctx)}  # last lint-clean RTL (it ran in the regression)
        previous = prev
        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
            data = llm.ask(ctx, owner, goal=f"Fix the bug in rtl/{mod}.v: reproduce it from the report, explain the root "
                           "cause, fix it, and say which other code could share the mistake. Keep the module's ports "
                           "EXACTLY as arch.yaml defines them (other modules instantiate it; you may not edit them). "
                           "Do not change the testbench.",
                           inputs=_inputs(ctx, ["spec/spec.yaml", "arch/arch.yaml", *[f"rtl/{p.name}" for p in _rtl_files(ctx)]]),
                           exit_criteria=["lint clean", "ports unchanged", "the failing tests pass"], schema=WRITER_ANSWER,
                           previous_attempts=previous, constraints="Coding standard:\n" + coding_std,
                           extra_note="Put the fixed file(s) in `files` (rtl/<module>.v). ")
            _answer_fields(ctx, owner, data)
            _write(ctx, owner, data["files"], "rtl", assigned={f"rtl/{mod}.v"})
            problems = lumen_checks(ctx)
            if not problems:
                return
            previous = (prev + f"\n\nYour fix attempt {attempt} broke lint/elaboration (exact tool output):\n- "
                        + "\n- ".join(problems[:20]))
            ctx.emit("handoff", f"Lumen -> {owner}: fix attempt {attempt} broke lint/elaboration ({len(problems)} issue(s))",
                     **_who("Lumen"), to_agent_id=owner, detail={"issues": problems[:20]})
        for name, text in before.items():  # never leave broken RTL behind
            (ctx.workdir / "rtl" / name).write_text(text)
        ctx.state["blocked"] = (f"RTL fix by {owner} still breaks lint/elaboration after {MAX_FIX_ATTEMPTS} attempts "
                                f"(RTL reverted to the last lint-clean version): {problems[:3]}")
    elif bug["routed_to"] == "Euclid":
        guarded(ctx, "Euclid", lambda: _author_loop(
            ctx, "Euclid", goal="Fix formal/formal_top.sv per the bug report (the property or assumption is wrong "
            "vs the spec). Do not remove properties or add assumptions without a spec reason.",
            inputs=["spec/spec.yaml", "tb/dut_ports.json", "tb/testplan.yaml", "formal/formal_top.sv",
                    f"reports/{bug['bug_id']}.json"], validate=validate_props, kind="formal", previous=prev,
            constraints=FORMAL_CONTRACT.replace("{depth}", str(targets()["formal_min_depth"]))), bug["root_cause"])
    elif bug["classification"] == "TEST":
        theo_revise(ctx, prev)
    else:
        ctx.state["blocked"] = f"SPEC question from Dex ({bug['requirement']}): {bug['root_cause']}"


def _debug_loop(ctx: StepContext, label: str) -> tuple[object, dict]:
    """Regression + formal; Dex triage and fixes until clean (DEBUG_ROUNDS max)."""
    for rnd in range(1, DEBUG_ROUNDS + 1):
        r = _regress(ctx, f"{label}_r{rnd}")
        sim_fail = _failures(r)
        if sim_fail and r.errors:  # Rex: re-run a failing seed once (flaky = environment bug)
            again = _regress(ctx, f"{label}_r{rnd}_rerun", seeds=SEEDS, sims=("verilator", "icarus"))
            if {i.message for i in again.errors} != {i.message for i in r.errors}:
                sim_fail.append({"kind": "flaky", "message": "results differ on re-run with the same seeds and code: "
                                 "environment (test) bug"})
        f = _formal(ctx)
        form_fail = [{"kind": "formal", "message": f"property ap_{n} failed (counterexample: "
                      f"{(f.get('runs', {}).get('prove') or {}).get('counterexample_vcd')})"} for n in f.get("failed", [])]
        if f.get("error"):
            form_fail.append({"kind": "harness", "message": f["error"]})
        quality = [f"the {m} run did not finish within {600 // 60} minutes: the properties (or a model embedded in "
                   "formal_top) are too expensive for the solver; keep each property small and port-level"
                   for m in f.get("timed_out", [])] + \
                  [f"ap_{n}: its cover cp_{n} is never reached (vacuous)" for n in f.get("vacuous", [])] + \
                  [f"ap_{n}: holds even with the DUT replaced by free outputs (tautology: it checks nothing about the design)"
                   for n in f.get("tautologies", [])]
        if not sim_fail and not form_fail and not quality:
            return r, f
        if rnd == DEBUG_ROUNDS:
            break
        if sim_fail or form_fail:
            ctx.state["dex_round"] = ctx.state.get("dex_round", 0) + 1
            for bug in _dex(ctx, sim_fail + form_fail, ctx.state["dex_round"]):
                _fix(ctx, bug)
                if ctx.state.get("blocked"):
                    return r, f
        if quality:  # decided by the tools, not a triage question: back to the property author
            ctx.emit("handoff", f"Euclid's properties fail the formal quality checks: {len(quality)} issue(s)",
                     **_who("Euclid"), detail={"issues": quality})
            prev = ("The formal harness found these property-quality problems (vacuous = the cover is never "
                    "reached, so the assertion can pass without ever being exercised; tautology = it holds even "
                    "when the DUT outputs are free, so it says nothing about the design). Rewrite those properties "
                    "so each constrains the DUT's behavior and its trigger is reachable; keep every other property:\n- "
                    + "\n- ".join(quality))
            guarded(ctx, "Euclid", lambda: _author_loop(
                ctx, "Euclid", goal="Fix the vacuous/tautological properties in formal/formal_top.sv.",
                inputs=["spec/spec.yaml", "tb/dut_ports.json", "tb/testplan.yaml", "formal/formal_top.sv",
                        "reports/formal_report.json"], validate=validate_props, kind="formal", previous=prev,
                constraints=FORMAL_CONTRACT.replace("{depth}", str(targets()["formal_min_depth"]))), "formal quality")
    ctx.state["blocked"] = f"{label}: failures remain after {DEBUG_ROUNDS} debug rounds"
    return r, f


def _coverage(ctx: StepContext, r) -> dict:
    plan = _plan(ctx)
    ports = {p["name"] for p in _ports(ctx)}
    vcds = [Path(v) for v in r.metrics.get("vcds", []) if v]
    hits = fcov.bin_hits(vcds, plan["clock"], plan["coverage_bins"], ports) if vcds else {}
    t = targets()
    cov = {"line": r.metrics.get("line_coverage"), "toggle": r.metrics.get("toggle_coverage"),
           "functional": round(sum(1 for v in hits.values() if v) / len(hits), 4) if hits else None,
           "bins": hits, "unhit_bins": [b for b, v in hits.items() if not v],
           "uncovered_lines": r.metrics.get("uncovered_lines", []), "untoggled": r.metrics.get("untoggled", []),
           "targets": {"line": t["line"], "toggle": t["toggle"], "functional_bins": t["functional_bins"]}}
    cov["met"] = bool(cov["line"] is not None and cov["line"] >= t["line"] and cov["toggle"] is not None
                      and cov["toggle"] >= t["toggle"] and cov["functional"] is not None
                      and cov["functional"] >= t["functional_bins"])
    return cov


def verification_steps() -> list[Step]:
    def setup(ctx: StepContext) -> None:
        src = ctx.task.inputs.get("source_run")
        if src and not (ctx.workdir / "tb").exists():
            # a verification-only run (e.g. after a change request) starts from a previous M0.6 run's files
            # and its REVIEWED guard baseline, so the anti-cheating guard still compares against that baseline
            from s2s.agents.runtime import artifact_dir
            root = artifact_dir() / "runs" / src
            for d in ("spec", "arch", "rtl", "tb", "formal", "guard_baseline"):
                shutil.copytree(root / d, ctx.workdir / d, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("__pycache__", "props_*", "stub"))
            for f in ("request.md",):
                if (root / f).exists():
                    shutil.copy(root / f, ctx.workdir / f)
            ctx.emit("plan", f"Rex: verification continues from run {src} (its files and reviewed baseline)", **_who("Rex"))
        ctx.state.update({"top": _arch(ctx)["top"], "design": _spec(ctx)["design"]})
        ctx.emit("plan", "Rex: plan - regression (Verilator 3 seeds + Icarus), formal (prove/cover/free-stub), Dex "
                 "triage of every failure, Cora coverage closure, Myra mutation testing, anti-cheating guard; report",
                 **_who("Rex"))
        for owner, goal in (("Rex", "Run the regression and track per-test/per-seed results"),
                            ("Cora", "Close coverage to the targets in coverage_targets.yaml"),
                            ("Myra", "Mutation-test the regression (20 screened mutants)")):
            _assign(ctx, "Rhea", owner, goal, ["checks pass in the Trust Layer"], "checks passed / checks")

    def change_requests(ctx: StepContext) -> None:
        """Operator change requests (task.inputs.change_requests), each a guarded change Sentinel must approve."""
        for cr in ctx.task.inputs.get("change_requests") or []:
            if cr["kind"] != "reclassify_bin_to_illegal_state":
                raise ValueError(f"unknown change request {cr['kind']!r}")
            reclassify_bin(ctx, cr["bin"], cr["reason"])
            if ctx.state.get("blocked"):
                return

    def regress_debug(ctx: StepContext) -> None:
        r, f = _debug_loop(ctx, "main")
        ctx.state["formal"] = {k: f.get(k) for k in ("proven_meaningful", "failed", "vacuous", "tautologies", "error")}
        ctx.evidence = f"regression {'clean' if not ctx.state.get('blocked') else 'blocked'}"

    def cora(ctx: StepContext) -> None:
        for rnd in range(0, CORA_ROUNDS + 1):
            r = _regress(ctx, f"cov_{rnd}")
            cov = _coverage(ctx, r)
            _json_report(ctx, "Cora", f"reports/coverage_{rnd}.json", cov)
            ctx.emit("tool_result", f"Cora: line {cov['line']}, toggle {cov['toggle']}, functional {cov['functional']} "
                     f"({len(cov['unhit_bins'])} bin(s) unhit) - {'targets met' if cov['met'] else 'below target'}",
                     **_who("Cora"), detail={"tool": "coverage", **{k: v for k, v in cov.items() if k not in ('uncovered_lines', 'untoggled')}})
            if _failures(r):
                ctx.state["blocked"] = "regression failing during coverage closure"
                return
            if cov["met"]:
                break
            if rnd == CORA_ROUNDS:
                break
            k = rnd + 1
            rtl_lines = {}
            for loc in cov["uncovered_lines"][:60]:
                fname, ln = loc.rsplit(":", 1)
                p = ctx.workdir / "rtl" / fname
                if p.exists():
                    rtl_lines[loc] = p.read_text().splitlines()[int(ln) - 1].strip()
            hole = {"unhit_bins": [b for b in _plan(ctx)["coverage_bins"] if b["name"] in cov["unhit_bins"]],
                    "uncovered_lines": rtl_lines, "untoggled_signals": cov["untoggled"][:80],
                    "line": cov["line"], "toggle": cov["toggle"], "functional": cov["functional"]}
            _json_report(ctx, "Cora", f"reports/coverage_holes_{k}.json", hole)

            def validate(c: StepContext, k=k) -> list[str]:
                f = c.workdir / f"tb/test_cora_{k}.py"
                probs = tb_static_problems({f"tb/test_cora_{k}.py": f.read_text()}, None) if f.exists() else [f"tb/test_cora_{k}.py not written"]
                if not probs and not guard.analyze_tests(f.read_text()):
                    probs = ["no @cocotb.test in the file"]
                _record(c, "cora_tests_static", probs, "python ast", "Cora")
                return probs
            guarded(ctx, "Cora", lambda: _author_loop(
                ctx, "Cora", goal=f"Close the coverage holes with NEW targeted tests in tb/test_cora_{k}.py (do not "
                "edit other files, never exclude bins). Reuse the existing reference model and helpers.",
                inputs=["spec/spec.yaml", "tb/testplan.yaml", "tb/dut_ports.json", "tb/ref_model.py",
                        *[f"tb/{p.name}" for p in sorted((ctx.workdir / "tb").glob("*.py"))
                          if p.name not in ("ref_model_a.py", "ref_model_b.py")], f"reports/coverage_holes_{k}.json"],
                validate=validate, kind="testbench", constraints=TB_CONTRACT), "coverage closure")
            _debug_loop(ctx, f"cora{k}")
            if ctx.state.get("blocked"):
                return
        ctx.state["coverage"] = {k: cov[k] for k in ("line", "toggle", "functional", "unhit_bins", "met")}
        t = targets()
        _record(ctx, "coverage_line", [] if (cov["line"] or 0) >= t["line"] else [f"line {cov['line']} < {t['line']}"], "verilator_coverage", "Cora")
        _record(ctx, "coverage_toggle", [] if (cov["toggle"] or 0) >= t["toggle"] else [f"toggle {cov['toggle']} < {t['toggle']}"], "verilator_coverage", "Cora")
        _record(ctx, "coverage_functional", [f"bin {b} never hit" for b in cov["unhit_bins"]] if cov["functional"] is not None else ["no waveform"],
                "vcd bins", "Cora")
        illegal = _plan(ctx).get("illegal_states") or []
        ill_probs: list[str] = []
        if illegal:
            ports = {p["name"] for p in _ports(ctx)}
            seen = fcov.bin_hits([Path(v) for v in r.metrics.get("vcds", []) if v], _plan(ctx)["clock"], illegal, ports)
            ill_probs += [f"illegal state {n} was SEEN {k} time(s) in simulation" for n, k in seen.items() if k]
            ctx.state["illegal_states_seen"] = seen
        reg_ok = not _failures(r)
        _record(ctx, "regression_100pct", [] if reg_ok else ["failures in the final regression"], "cocotb_regress", "Rex")
        tests = r.metrics.get("tests_by_name", {})
        plan = _plan(ctx)
        untraced = [req["id"] for req in plan["requirements"]
                    if not all(t["kind"] == "formal" or (tests.get(t["name"], {}).get("pass", 0) and not tests.get(t["name"], {}).get("fail"))
                               for t in req["tests"])]
        _record(ctx, "requirements_traced", [f"{x} has a test that did not pass" for x in untraced], "cocotb_regress", "Vera")
        fr = _formal(ctx)
        _record(ctx, "formal_3_meaningful", [] if fr["proven_meaningful"] >= 3 else
                [f"only {fr['proven_meaningful']} meaningful proven properties"], "sby", "Euclid")
        _record(ctx, "formal_vacuity", [f"ap_{n}: cover never reached" for n in fr.get("vacuous", [])], "sby", "Euclid")
        if illegal:
            props = fr.get("properties") or {}
            for st in illegal:
                pr = props.get(st["assertion"])
                if not pr or not pr["counts"]:
                    ill_probs.append(f"illegal state {st['name']}: assertion ap_{st['assertion']} is "
                                     f"{'missing' if not pr else pr['status'] + ('' if pr['depends_on_design'] else ', tautology')}")
            _record(ctx, "illegal_states_never_happen", ill_probs, "vcd + sby", "Euclid")
        ctx.state["formal"] = {k: fr.get(k) for k in ("proven_meaningful", "failed", "vacuous", "tautologies", "error")}
        ctx.state["formal_props"] = fr.get("properties")
        ctx.evidence = f"coverage met={cov['met']}"

    def myra(ctx: StepContext) -> None:
        who = _who("Myra")
        rtl = {f"rtl/{p.name}": p.read_text() for p in _rtl_files(ctx)}
        mods = ",".join(_test_modules(ctx))
        for attempt in (1, 2):
            ctx.emit("tool_call", f"Myra: mutation run {attempt}: 20 screened mutants of the final RTL", status="working",
                     detail={"tool": "mutation"}, **who)
            try:
                res = run_mutation(workdir=ctx.workdir, rtl_files=rtl, top=ctx.state["top"], tb_dir=ctx.workdir / "tb",
                                   test_module=mods, log=ctx.beat)
            except MutationHarnessError as e:
                _record(ctx, "mutation_detection", [f"harness error: {e}"], "mutation", "Myra")
                ctx.state["blocked"] = f"mutation harness error: {e}"
                return
            ctx.compute("mutation", sum(m["duration_s"] or 0 for m in res["mutants"]), agent_id="Myra")
            _json_report(ctx, "Myra", f"reports/mutation_{attempt}.json", res)
            ctx.emit("tool_result", f"Myra: {res['detected']}/{res['total']} injected bugs caught ({res['rate']:.0%}); "
                     f"by type {res['by_type']}; {len(res['screened_out'])} screened out", **who,
                     detail={"tool": "mutation", "rate": res["rate"], "by_type": res["by_type"],
                             "missed": [m["description"] for m in res["mutants"] if not m["detected"]]})
            ctx.state.setdefault("mutation", []).append({"attempt": attempt, "detected": res["detected"],
                                                         "total": res["total"], "rate": res["rate"], "by_type": res["by_type"]})
            if res["rate"] >= targets()["mutation_detection"] or attempt == 2:
                break
            missed = [{"bug_type": m["type"], "requirements": m["reqs"],
                       "what": "a realistic bug of this type in the logic implementing these requirements was not "
                               "detected by any test"} for m in res["mutants"] if not m["detected"]]
            _json_report(ctx, "Myra", "reports/mutation_missed.json", missed)
            ctx.emit("handoff", f"Myra -> Nadia: {len(missed)} missed injected bug(s) -> test-improvement task for Theo",
                     **who, to_agent_id="Nadia", detail={"missed": missed})
            _assign(ctx, "Nadia", "Theo", "Strengthen tests so the missed bug types are caught", ["mutation >= 85%"],
                    "mutants caught / mutants")
            theo_revise(ctx, "Myra's mutation run missed these injected bugs (type and requirements only; you may not "
                        "see the RTL). Add or strengthen tests for the behavior of those requirements:\n"
                        + json.dumps(missed, indent=2))
            r, _ = _debug_loop(ctx, "mut")
            if ctx.state.get("blocked"):
                return
        last = ctx.state["mutation"][-1]
        probs = [] if last["rate"] >= targets()["mutation_detection"] else \
            [f"{last['detected']}/{last['total']} = {last['rate']:.0%} < {targets()['mutation_detection']:.0%}"]
        if last["total"] < 20:  # acceptance: 20 seeded bugs; fewer distinct mutants is a failed measurement
            probs.append(f"only {last['total']} distinct non-equivalent mutants could be generated (20 required)")
        _record(ctx, "mutation_detection", probs, "mutation", "Myra")

    def anticheat(ctx: StepContext) -> None:
        base = ctx.workdir / "guard_baseline"
        before = {str(p.relative_to(base)): p.read_text() for p in base.rglob("*") if p.is_file()}
        after = _snapshot(ctx)
        flags = guard.diff_files(before, after)
        approved = [f for g in ctx.state.get("guard_approvals", []) for f in g["flags"]]
        unreviewed = [f for f in flags if f not in approved]
        ctx.state["anticheat_final"] = {"flags": flags, "approved_by_sentinel": approved, "unreviewed": unreviewed}
        _record(ctx, "anti_cheat_final", unreviewed, "s2s.verify.guard", "Sentinel")

    def report(ctx: StepContext) -> None:
        st = ctx.state
        real = [b for b in st.get("bugs", []) if b["classification"] == "DESIGN"]
        summary = {"design": st["design"], "coverage": st.get("coverage"), "formal": st.get("formal"),
                   "formal_properties": st.get("formal_props"), "mutation": st.get("mutation"),
                   "bugs": st.get("bugs", []), "real_rtl_bugs": real, "guard": st.get("guard_events", []),
                   "anticheat_final": st.get("anticheat_final")}
        _json_report(ctx, "Rex", "reports/verification_report.json", summary)
        st.setdefault("answers", {})["Rex"] = {
            "status": "success", "summary": f"{st['design']}: regression clean; coverage {st.get('coverage')}; formal "
            f"{(st.get('formal') or {}).get('proven_meaningful')} meaningful proven; mutation {st.get('mutation', [{}])[-1]}; "
            f"{len(real)} real RTL bug(s) found and fixed", "assumptions": [], "open_issues": [],
            "self_assessment": {"confidence": "medium", "reason": "tool results; see verification_report.json"}}
        _task_result(ctx, "verification")

    return [setup, change_requests, stop_if_blocked, regress_debug, stop_if_blocked, cora, stop_if_blocked, myra,
            stop_if_blocked, anticheat, report]


# Registered with the design agent (orchestrator agent kind "s2s").
from s2s.agents.m05 import DesignAgent  # noqa: E402

DesignAgent.STAGES.update({"test_build": test_build_steps, "verification": verification_steps})
