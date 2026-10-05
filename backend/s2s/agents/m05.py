"""M0.5 design agents: Zone 1 (spec, architecture) and Zone 2A (RTL). MASTER_SPEC 13.2 M0.5.

One task per stage, run by the stage's team lead; inside it, each agent acts in its own
model call and real tools decide every check:

  spec          Sage (kb_search) -> Ivy (standards) -> Iris (spec.yaml, spec.md)
                -> checks: spec_schema, spec_consistency -> Sentinel review (Iris revises once on
                blocking findings) -> task.result
  architecture  Sage -> Kepler (arch.yaml) -> checks: arch_schema, arch_consistency
                -> Pascal (PPA review) -> Sentinel review (Kepler revises once) -> task.result
  rtl           Reid assigns each arch module to Ada / Ada-C / Ada-I by kind -> they write RTL
                -> Lumen runs verilator_lint (-Wall), yosys_elab, port and structure checks;
                failures go back to the owners with the tools' exact output (3 rounds max)
                -> Watt (low-power advice, no function change) -> Sage (retrospective, lessons)
                -> task.result

A step never raises after recording checks (its transaction would roll back the evidence):
it marks `state["blocked"]`, commits, and the next `stop_if_blocked` step pauses the task for a
human (runtime.NeedsHuman).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from s2s.agents import llm
from s2s.agents.runtime import Agent, NeedsHuman, Step, StepContext
from s2s.db.models import Task
from s2s.design import checks
from s2s.design.schemas import ARCH_SCHEMA, SPEC_SCHEMA, REPORT_ANSWER, REVIEW_ANSWER, SAGE_ANSWER, WRITER_ANSWER
from s2s.knowledge import kb
from s2s.org import load_org
from s2s.tools import runner
from s2s.tools.verilator_lint import run_verilator_lint
from s2s.tools.yosys_elab import run_yosys_elab

REPO = Path(__file__).resolve().parents[3]
MAX_ATTEMPTS = 3  # preamble rule 7: stop and escalate after three honest attempts
OWNER_BY_KIND = {"datapath": "Ada", "control": "Ada-C", "interface": "Ada-I"}


# --- shared helpers ---------------------------------------------------------------------------
def _read(ctx: StepContext, path: str) -> str:
    return (ctx.workdir / path).read_text()


def _inputs(ctx: StepContext, paths: list[str]) -> dict[str, str]:
    return {p: _read(ctx, p) for p in paths if (ctx.workdir / p).exists()}


def _write(ctx: StepContext, who: str, files: list[dict], kind: str,
           assigned: set[str] | None = None) -> dict[str, str]:
    """Write an agent's files into the run folder, enforcing its writes_to. Returns path -> sha.
    `assigned`: the only files this agent was assigned (RTL ownership); others are refused, not
    written, and reported to its manager."""
    a = llm.agent(who)
    out: dict[str, str] = {}
    for f in files:
        if not llm.path_allowed(f["path"], a.writes_to):
            raise llm.OutsideAllowedPaths(f"{who} may not write {f['path']} (writes_to: {list(a.writes_to)})")
    if assigned is not None:
        refused = [f["path"] for f in files if f["path"] not in assigned]
        if refused:
            mgr = (load_org().manager_chain(a.team) or [None])[0]
            ctx.emit("finding", f"{mgr}: refused {who}'s {', '.join(refused)} (not assigned to {who}); not written",
                     agent_id=mgr, team=a.team, to_agent_id=who,
                     detail={"severity": "major", "rule": "write only assigned modules", "refused": refused,
                             "assigned": sorted(assigned)})
            ctx.state.setdefault("ownership_refusals", []).extend(refused)
        files = [f for f in files if f["path"] in assigned]
    for f in files:
        dest = ctx.workdir / f["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = f["content"] if f["content"].endswith("\n") else f["content"] + "\n"
        dest.write_text(content)
        out[f["path"]] = ctx.artifact(kind, f["path"], content.encode(), agent_id=who, team=a.team)
    ctx.state.setdefault("outputs", {}).update(out)
    return out


def _sage_search(ctx: StepContext, asker: str, query: str) -> str:
    """kb_search, answered by Sage (keyword retrieval, no model call)."""
    hits = kb.search(query)
    sage = llm.agent("Sage")
    ctx.emit("tool_call", f"{asker} -> Sage: kb_search '{query[:80]}'", agent_id=asker,
             team=llm.agent(asker).team if (llm.DEFS_DIR / f"{asker}.yaml").exists() else ctx.task.team_id,
             to_agent_id="Sage", detail={"tool": "kb_search", "query": query})
    ctx.emit("tool_result", f"Sage: {len(hits)} knowledge entries for {asker}: "
             + "; ".join(h["id"] for h in hits), agent_id="Sage", team=sage.team, to_agent_id=asker,
             detail={"tool": "kb_search", "entries": [{"id": h["id"], "title": h["title"],
                                                       "source": h["source"]} for h in hits]})
    ctx.state.setdefault("kb_entries", [])
    ctx.state["kb_entries"] += [h["id"] for h in hits if h["id"] not in ctx.state["kb_entries"]]
    return kb.brief(hits)


def _record(ctx: StepContext, name: str, problems: list[str], tool: str, who: str) -> bool:
    return ctx.check(name, tool, not problems, {"problems": len(problems), "detail": problems[:20]},
                     agent_id=who, team=llm.agent(who).team)


def _answer_fields(ctx: StepContext, who: str, data: dict) -> None:
    """Keep each agent's B.6 fields for the task.result."""
    ctx.state.setdefault("answers", {})[who] = {k: data[k] for k in
                                               ("status", "summary", "assumptions", "open_issues", "self_assessment")}


def stop_if_blocked(ctx: StepContext) -> None:
    if ctx.state.get("blocked"):
        raise NeedsHuman(ctx.state["blocked"])


def _review(ctx: StepContext, artifact: str, author: str, files: list[str], fix_inputs: list[str],
            validate, kind: str) -> None:
    """Sentinel reviews; on blocking findings the author revises once, the checks re-run and
    Sentinel reviews again. Blocking findings left = the stage stops for a human."""
    sentinel = llm.agent("Sentinel")
    report = f"reports/sentinel_{artifact}.json"
    for round_ in (1, 2):
        knowledge = _sage_search(ctx, "Sentinel", f"review {artifact} " + ctx.task.inputs.get("design_name", ""))
        data = llm.ask(ctx, sentinel, goal=f"Independently review the {artifact} for {ctx.task.inputs['design_name']}. "
                       "File findings only for real, specific problems; say why each matters.",
                       inputs=_inputs(ctx, ["request.md", *files]),
                       exit_criteria=["every finding is specific: artifact, location, evidence, suggested action"],
                       schema=REVIEW_ANSWER, relevant_knowledge=knowledge,
                       extra_note="Put each finding in `findings` (an empty list if you find none). ")
        findings = data["findings"]
        path = report if round_ == 1 else report.replace(".json", f"_round{round_}.json")
        _write(ctx, "Sentinel", [{"path": path, "content": json.dumps(findings, indent=2)}], "review")
        for f in findings:
            ctx.emit("finding", f"Sentinel [{f['severity']}] {f['target']}: {f['what'][:200]}",
                     agent_id="Sentinel", team=sentinel.team, to_agent_id=author, detail=f)
        blocking = [f for f in findings if f["severity"] == "blocking"]
        _record(ctx, f"sentinel_{artifact}_review", [f"{f['target']}: {f['what']}" for f in blocking],
                "sentinel", "Sentinel")
        ctx.state.setdefault("findings", {})[f"{artifact}_round{round_}"] = findings
        if not blocking:
            return
        if round_ == 2:
            ctx.state["blocked"] = (f"{len(blocking)} blocking Sentinel finding(s) on the {artifact} remain after "
                                    "one revision; a human must resolve or overrule them")
            return
        ctx.emit("handoff", f"Sentinel -> {author}: {len(blocking)} blocking finding(s) on the {artifact}",
                 agent_id="Sentinel", team=sentinel.team, to_agent_id=author, detail={"findings": blocking})
        prev = "Sentinel filed these blocking findings on your previous version:\n" + json.dumps(blocking, indent=2)
        _author_loop(ctx, author, goal=f"Revise the {artifact} to resolve the blocking findings without "
                     "inventing scope.", inputs=fix_inputs + [path], validate=validate, kind=kind, previous=prev,
                     constraints=schema_brief("B.1", SPEC_SCHEMA) if artifact == "spec" else schema_brief("B.2", ARCH_SCHEMA))
        if ctx.state.get("blocked"):
            return


EXAMPLES = {"B.1": "B.1_spec_yaml.md", "B.2": "B.2_arch_yaml.md"}


def schema_brief(appendix: str, schema: dict) -> str:
    """The format a writer must follow: the Appendix B example (verbatim) and the exact JSON Schema
    the deterministic check validates against."""
    return (f"OUTPUT FORMAT - Appendix {appendix} example (verbatim from the spec):\n"
            f"{llm._prompt(EXAMPLES[appendix])}\n"
            "The file is validated with this JSON Schema (draft 2020-12) before any review:\n"
            + json.dumps(schema, indent=1))


def _author_loop(ctx: StepContext, author: str, *, goal: str, inputs: list[str], validate, kind: str,
                 previous: str = "", exit_criteria: list[str] | None = None, constraints: str = "") -> bool:
    """The author writes; the deterministic checks run; failures go back verbatim. 3 attempts."""
    knowledge = _sage_search(ctx, author, f"{goal} {ctx.task.inputs.get('design_name', '')}")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        data = llm.ask(ctx, author, goal=goal, inputs=_inputs(ctx, inputs),
                       exit_criteria=exit_criteria or ["the deterministic checks pass"], schema=WRITER_ANSWER,
                       previous_attempts=previous, relevant_knowledge=knowledge, constraints=constraints,
                       extra_note="Put every file you write in `files` (path relative to the run folder, full content). ")
        _answer_fields(ctx, author, data)
        _write(ctx, author, data["files"], kind)
        problems = validate(ctx)
        if not problems:
            return True
        previous = (f"Attempt {attempt} failed these deterministic checks (exact output):\n- "
                    + "\n- ".join(problems))
        ctx.emit("handoff", f"checks -> {author}: attempt {attempt} has {len(problems)} problem(s)",
                 agent_id=author, team=llm.agent(author).team, detail={"problems": problems[:30]})
    ctx.state["blocked"] = f"{author}: checks still failing after {MAX_ATTEMPTS} attempts"
    return False


def _task_result(ctx: StepContext, name: str) -> None:
    """Assemble and validate task.result (Appendix B.6) from the agents' answers and the checks."""
    answers = ctx.state.get("answers", {})
    lead = answers.get(ctx.task.agent_id) or next(iter(answers.values()), {})
    # The result attests the outputs as they are now. A step that was interrupted (budget stop, restart) may
    # have rewritten an output after the last saved checkpoint; such a difference is reported, not hidden.
    rewritten = []
    for p, sha in list(ctx.state.get("outputs", {}).items()):
        f = ctx.workdir / p
        if f.exists():
            now = hashlib.sha256(f.read_bytes()).hexdigest()
            if now != sha:
                rewritten.append(p)
                ctx.state["outputs"][p] = now
    result = {
        "task_id": ctx.task.id,
        "status": "success",
        "summary": lead.get("summary", ""),
        "outputs": [{"path": p, "sha256": s} for p, s in sorted(ctx.state.get("outputs", {}).items())],
        "checks_run": ctx.state.get("checks_run", []),
        "assumptions": sorted({a for x in answers.values() for a in x.get("assumptions", [])}),
        "open_issues": sorted({a for x in answers.values() for a in x.get("open_issues", [])}
                              | {f"{p} was rewritten by an interrupted step attempt after its last recorded hash; "
                                 "the result records the file as it is now" for p in rewritten}),
        "messages": [{"from": who, "summary": x.get("summary", "")} for who, x in answers.items()
                     if who != ctx.task.agent_id],
        "self_assessment": lead.get("self_assessment", {"confidence": "low", "reason": "no answer recorded"}),
    }
    problems = checks.task_result_schema(result)
    _record(ctx, "task_result_schema", problems, "jsonschema", ctx.task.agent_id)
    path = f"reports/task_result_{name}.json"
    dest = ctx.workdir / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n")
    ctx.artifact("task.result", path, dest.read_bytes())  # the lead reports
    ctx.task.outputs = {**(ctx.task.outputs or {}), "task_result": path,
                        "artifacts": ctx.state.get("outputs", {})}
    ctx.evidence = f"{len(result['outputs'])} outputs, {len(result['checks_run'])} checks recorded"


def _load_yaml(ctx: StepContext, path: str):
    try:
        return yaml.safe_load(_read(ctx, path)), []
    except FileNotFoundError:
        return None, [f"{path} was not written"]
    except yaml.YAMLError as e:
        return None, [f"{path} is not valid YAML: {e}"]


# --- Zone 1: spec -------------------------------------------------------------------------------
def validate_spec(ctx: StepContext) -> list[str]:
    spec, problems = _load_yaml(ctx, "spec/spec.yaml")
    problems = problems or checks.spec_schema(spec)
    _record(ctx, "spec_schema", problems, "jsonschema", "Iris")
    cons = checks.spec_consistency(spec) if not problems else ["skipped: schema failed"]
    _record(ctx, "spec_consistency", cons, "s2s.design.checks", "Iris")
    if not (ctx.workdir / "spec/spec.md").exists():
        cons = cons + ["spec/spec.md (readable version) was not written"]
    return problems + cons


def spec_steps() -> list[Step]:
    def setup(ctx: StepContext) -> None:
        req = (REPO / "designs" / ctx.task.inputs["design_name"] / "request.md")
        text = ctx.task.inputs.get("request_text") or req.read_text()
        ctx.workdir.mkdir(parents=True, exist_ok=True)
        (ctx.workdir / "request.md").write_text(text)
        ctx.artifact("request", "request.md", text.encode(), agent_id="Iris")
        ctx.emit("plan", "Iris: plan - look up standards (Ivy) and past lessons (Sage); write spec.yaml and spec.md; "
                 "pass schema and consistency checks; Sentinel review; report", agent_id="Iris")

    def standards(ctx: StepContext) -> None:
        knowledge = _sage_search(ctx, "Ivy", _read(ctx, "request.md"))
        data = llm.ask(ctx, "Ivy", goal="Identify the interface standards involved in this request and the rules "
                       "that matter for design and verification; recommend reusable IP with license notes. "
                       "Say plainly if no external standard applies.",
                       inputs=_inputs(ctx, ["request.md"]), exit_criteria=["standards listed with version, or none"],
                       schema=REPORT_ANSWER, relevant_knowledge=knowledge,
                       extra_note="Put the report (Markdown) in `report_markdown`. ")
        _answer_fields(ctx, "Ivy", data)
        _write(ctx, "Ivy", [{"path": "reports/standards.md", "content": data["report_markdown"]}], "report")
        ctx.emit("handoff", "Ivy -> Iris: standards notes", agent_id="Ivy", team=llm.agent("Ivy").team,
                 to_agent_id="Iris", detail={"path": "reports/standards.md"})

    def write_spec(ctx: StepContext) -> None:
        _author_loop(ctx, "Iris", goal="Write spec/spec.yaml (schema Appendix B.1) and spec/spec.md (readable "
                     "version) for the request. Give every output a reset value (`reset_value` or a reset "
                     "requirement naming it).", inputs=["request.md", "reports/standards.md"],
                     validate=validate_spec, kind="spec", constraints=schema_brief("B.1", SPEC_SCHEMA),
                     exit_criteria=["spec.yaml passes schema B.1", "spec consistency checks pass",
                                    "every requirement typed and testable"])
        ctx.evidence = f"spec checks passed: {not ctx.state.get('blocked')}"

    def review(ctx: StepContext) -> None:
        _review(ctx, "spec", "Iris", ["spec/spec.yaml", "spec/spec.md"],
                ["request.md", "reports/standards.md", "spec/spec.yaml", "spec/spec.md"], validate_spec, "spec")

    return [setup, standards, write_spec, stop_if_blocked, review, stop_if_blocked,
            lambda ctx: _task_result(ctx, "spec")]


# --- Zone 1: architecture -----------------------------------------------------------------------
def validate_arch(ctx: StepContext) -> list[str]:
    spec, _ = _load_yaml(ctx, "spec/spec.yaml")
    arch, problems = _load_yaml(ctx, "arch/arch.yaml")
    problems = problems or checks.arch_schema(arch)
    _record(ctx, "arch_schema", problems, "jsonschema", "Kepler")
    cons = checks.arch_consistency(arch, spec) if not problems else ["skipped: schema failed"]
    _record(ctx, "arch_consistency", cons, "s2s.design.checks", "Kepler")
    return problems + cons


def arch_steps() -> list[Step]:
    def write_arch(ctx: StepContext) -> None:
        ctx.emit("plan", "Kepler: plan - map every requirement to a module; write arch.yaml; pass schema and "
                 "consistency checks; Pascal PPA review; Sentinel review; report", agent_id="Kepler")
        _author_loop(ctx, "Kepler", goal="Write arch/arch.yaml (schema Appendix B.2) for this spec. Each module "
                     "has `kind` (datapath | control | interface: which RTL team writes it) and `implements` "
                     "(REQ ids). Use `ports_from_spec: true` for the top module.",
                     inputs=["spec/spec.yaml", "spec/spec.md"], validate=validate_arch, kind="arch",
                     constraints=schema_brief("B.2", ARCH_SCHEMA), exit_criteria=["arch.yaml passes schema B.2", "every spec I/O at the top with matching widths",
                                    "every requirement maps to a module", "slack margin >= 15%"])

    def pascal(ctx: StepContext) -> None:
        data = llm.ask(ctx, "Pascal", goal="Review the PPA estimate in arch.yaml against the spec targets: area "
                       "(cells), logic depth at the target clock, power assumptions. No past synthesis results "
                       "exist yet to calibrate against; say so and give an error band.",
                       inputs=_inputs(ctx, ["spec/spec.yaml", "arch/arch.yaml"]),
                       exit_criteria=["trade-off table with numbers and assumptions"], schema=REPORT_ANSWER,
                       extra_note="Put the report (Markdown) in `report_markdown`. ")
        _answer_fields(ctx, "Pascal", data)
        _write(ctx, "Pascal", [{"path": "reports/ppa_pascal.md", "content": data["report_markdown"]}], "report")
        ctx.emit("handoff", "Pascal -> Kepler: PPA review", agent_id="Pascal", team=llm.agent("Pascal").team,
                 to_agent_id="Kepler", detail={"path": "reports/ppa_pascal.md"})

    def review(ctx: StepContext) -> None:
        _review(ctx, "arch", "Kepler", ["spec/spec.yaml", "arch/arch.yaml"],
                ["spec/spec.yaml", "spec/spec.md", "arch/arch.yaml", "reports/ppa_pascal.md"], validate_arch, "arch")

    return [write_arch, stop_if_blocked, pascal, review, stop_if_blocked, lambda ctx: _task_result(ctx, "architecture")]


# --- Zone 2A: RTL -------------------------------------------------------------------------------
def _arch(ctx: StepContext) -> dict:
    return yaml.safe_load(_read(ctx, "arch/arch.yaml"))


def _leaf_first(arch: dict) -> list[str]:
    mods = {m["name"]: m for m in arch["modules"]}
    order: list[str] = []

    def visit(n: str, seen: tuple = ()) -> None:
        if n in order or n in seen:
            return
        for c in mods[n].get("instances") or []:
            visit(c, seen + (n,))
        order.append(n)
    for n in mods:
        visit(n)
    return order


def lumen_checks(ctx: StepContext) -> list[str]:
    """Lumen: real Verilator lint (-Wall) and Yosys elaboration, plus port/structure checks."""
    arch, spec = _arch(ctx), yaml.safe_load(_read(ctx, "spec/spec.yaml"))
    files = sorted((ctx.workdir / "rtl").glob("*.v")) + sorted((ctx.workdir / "rtl").glob("*.sv"))
    who = dict(agent_id="Lumen", team=llm.agent("Lumen").team)
    problems: list[str] = []
    report: dict = {"tools": {}}
    texts = {f"rtl/{f.name}": f.read_text() for f in files}
    structure = checks.rtl_structure(texts, arch)
    _record(ctx, "rtl_structure", structure, "s2s.design.checks", "Lumen")
    problems += structure
    for name, fn in (("verilator_lint", run_verilator_lint), ("yosys_elab", run_yosys_elab)):
        ctx.emit("tool_call", f"Lumen: {name} on {len(files)} file(s), top {arch['top']}", status="working",
                 detail={"tool": name}, **who)
        r = fn(files, arch["top"], ctx.workdir)
        ctx.compute(name, r.duration_s or 0.0, agent_id="Lumen")
        ctx.emit("tool_result", f"Lumen: {name} {r.status} ({r.error_count} errors, {r.warning_count} warnings)",
                 detail={"tool": name, "status": r.status, "metrics": r.metrics, "reasons": r.reasons,
                         "command": runner.command_str(r.command), "tool_version": r.tool_version,
                         "env_hash": r.env_hash, "log": str(Path(r.log_path).relative_to(ctx.workdir)) if r.log_path else None},
                 **who)
        ctx.check(name, name, r.passed, {"errors": r.error_count, "warnings": r.warning_count, **r.metrics,
                                          "status": r.status, "tool_version": r.tool_version},
                  command=runner.command_str(r.command), **who)
        report["tools"][name] = {"status": r.status, "passed": r.passed, "reasons": r.reasons,
                                 "issues": [{"severity": i.severity, "file": _rel(ctx, i.file), "line": i.line, "rule": i.rule,
                                             "message": i.message, "class": "error" if i.severity == "error" else "blocking warning"}
                                            for i in r.errors + r.warnings]}
        if not r.passed:
            problems += [f"{name}: {_rel(ctx, i.file)}:{i.line or ''} [{i.rule or i.severity}] {i.message}"
                         for i in r.errors + r.warnings] or [f"{name}: {x}" for x in r.reasons]
    # ports of the elaborated top against arch.yaml
    ports_json = ctx.workdir / "logs" / "rtl_ports.json"
    srcs = " ".join(str(f.resolve()) for f in files)
    cmd = ["yosys", "-q", "-p", f"read_verilog -sv {srcs}; hierarchy -check -top {arch['top']}; proc; "
           f"write_json {ports_json.resolve()}"]
    rec = runner.run(cmd, ctx.workdir, ctx.workdir / "logs" / "yosys_ports.log", "yosys", 300)
    port_problems = (checks.rtl_ports(json.loads(ports_json.read_text()), arch, spec)
                     if rec.exit_code == 0 and ports_json.exists() else [f"yosys write_json failed (exit {rec.exit_code})"])
    _record(ctx, "rtl_ports_match_arch", port_problems, "yosys", "Lumen")
    problems += port_problems
    report.update({"structure": structure, "ports": port_problems, "waivers": [],
                   "blocking": len(problems), "passed": not problems})
    _write(ctx, "Lumen", [{"path": "reports/lint_report.json", "content": json.dumps(report, indent=2)},
                          {"path": "reports/waivers.yaml", "content": "# no waivers\nwaivers: []"}], "report")
    return problems


def _rel(ctx: StepContext, path: str | None) -> str:
    """Tool paths are absolute (the run folder is mounted at the same path); report them relative."""
    if not path:
        return ""
    try:
        return str(Path(path).resolve().relative_to(ctx.workdir.resolve()))
    except ValueError:
        return path


def rtl_steps() -> list[Step]:
    def assign(ctx: StepContext) -> None:
        arch = _arch(ctx)
        org = load_org()
        mgr = (org.manager_chain(ctx.task.team_id) or ["Reid"])[0]
        owners: dict[str, list[str]] = {}
        for name in _leaf_first(arch):
            kind = next(m["kind"] for m in arch["modules"] if m["name"] == name)
            owners.setdefault(OWNER_BY_KIND[kind], []).append(name)
        for owner, mods in owners.items():
            ctx.emit("handoff", f"{mgr} assigned {', '.join(mods)} to {owner}", agent_id=mgr,
                     team=org.team_of_agent(owner).id, to_agent_id=owner,
                     detail={"goal": f"Write lint-clean RTL for {', '.join(mods)}",
                             "inputs": ["spec/spec.yaml", "arch/arch.yaml"],
                             "exit_criteria": ["verilator -Wall clean", "yosys elaboration clean",
                                               "ports match arch.yaml", "REQ trace comments"],
                             "expected_minutes": 10, "budget": llm.agent(owner).budget,
                             "progress_signal": "modules passing lint / modules assigned"})
        ctx.state["owners"] = owners
        ctx.emit("plan", "Ada: plan - write each module leaf-first; Lumen runs Verilator -Wall and Yosys; fix "
                 "every blocking issue; Watt low-power review; report", agent_id=ctx.task.agent_id)

    def write_rtl(ctx: StepContext) -> None:
        owners: dict[str, list[str]] = ctx.state["owners"]
        base = ["spec/spec.yaml", "arch/arch.yaml"]
        coding_std = (REPO / "docs" / "coding_standard.md").read_text()
        for owner, mods in owners.items():
            ok = _author_loop_rtl(ctx, owner, mods, base, coding_std, previous="")
            if not ok:
                return
        for rnd in range(1, MAX_ATTEMPTS + 1):
            problems = lumen_checks(ctx)
            ctx.evidence = f"lint round {rnd}: {len(problems)} blocking issue(s)"
            if not problems:
                return
            if rnd == MAX_ATTEMPTS:
                break
            by_owner = _route(problems, owners)
            for owner, mods in owners.items():
                mine = by_owner.get(owner) or []
                if not mine:
                    continue
                ctx.emit("handoff", f"Lumen -> {owner}: {len(mine)} blocking issue(s) to fix",
                         agent_id="Lumen", team=llm.agent("Lumen").team, to_agent_id=owner,
                         detail={"issues": mine[:30], "report": "reports/lint_report.json"})
                prev = (f"Lint round {rnd} found these blocking issues (exact tool output):\n- " + "\n- ".join(mine))
                if not _author_loop_rtl(ctx, owner, mods, base + ["reports/lint_report.json"], coding_std, prev):
                    return
        ctx.state["blocked"] = f"RTL still has blocking lint/elaboration issues after {MAX_ATTEMPTS} rounds"

    def watt(ctx: StepContext) -> None:
        rtl = sorted(f"rtl/{p.name}" for p in (ctx.workdir / "rtl").iterdir() if p.suffix in (".v", ".sv"))
        data = llm.ask(ctx, "Watt", goal="Review the RTL for low-power opportunities (clock gating, operand "
                       "isolation). Recommendations only: do not change function; quantify only with data you "
                       "have, and say what switching-activity data would be needed.",
                       inputs=_inputs(ctx, ["spec/spec.yaml", "arch/arch.yaml", *rtl]),
                       exit_criteria=["recommendations with expected effect and risk"], schema=REPORT_ANSWER,
                       extra_note="Put the report (Markdown) in `report_markdown`. ")
        _answer_fields(ctx, "Watt", data)
        _write(ctx, "Watt", [{"path": "reports/low_power.md", "content": data["report_markdown"]}], "report")

    def sage(ctx: StepContext) -> None:
        events = [f"{k}: {v}" for k, v in sorted((ctx.state.get("rounds") or {}).items())]
        lint = _read(ctx, "reports/lint_report.json")
        data = llm.ask(ctx, "Sage", goal="Write a short retrospective of this run's RTL stage (what slowed us "
                       "down, which checks caught issues, which lessons were reused) and lessons for any "
                       "failure that was fixed. No lessons if nothing failed.",
                       inputs={"reports/lint_report.json": lint},
                       exit_criteria=["lessons short, specific, reusable"], schema=SAGE_ANSWER,
                       previous_attempts="\n".join(events) or "RTL author rounds: see lint report",
                       relevant_knowledge="entries used this run: " + ", ".join(ctx.state.get("kb_entries", [])),
                       extra_note="Put the retrospective (Markdown) in `report_markdown` and lessons in `lessons`. ")
        _answer_fields(ctx, "Sage", data)
        _write(ctx, "Sage", [{"path": "reports/retrospective.md", "content": data["report_markdown"]}], "report")
        rows = kb.add_lessons(data["lessons"], ctx.task.run_id)
        ctx.emit("artifact.created", f"Sage: {len(rows)} lesson(s) added to the knowledge base", agent_id="Sage",
                 team=llm.agent("Sage").team, detail={"lessons": [r["id"] for r in rows]})

    return [assign, write_rtl, stop_if_blocked, watt, sage, lambda ctx: _task_result(ctx, "rtl")]


def _route(problems: list[str], owners: dict[str, list[str]]) -> dict[str, list[str]]:
    """Send each issue to the owner of the module named in it; unplaced issues go to everyone."""
    out: dict[str, list[str]] = {}
    for p in problems:
        hit = [o for o, mods in owners.items() if any(f"{m}.v" in p or f"'{m}'" in p for m in mods)]
        for o in hit or list(owners):
            out.setdefault(o, []).append(p)
    return out


def _author_loop_rtl(ctx: StepContext, owner: str, mods: list[str], inputs: list[str], coding_std: str,
                     previous: str) -> bool:
    knowledge = _sage_search(ctx, owner, "rtl verilog lint reset " + " ".join(mods))
    others = sorted({m for o, ms in ctx.state.get("owners", {}).items() if o != owner for m in ms})
    data = llm.ask(ctx, owner, goal=f"Write synthesizable Verilog-2005 RTL for module(s) {', '.join(mods)} exactly "
                   "as arch.yaml defines them, one module per file rtl/<module>.v, with a header and // REQ-### "
                   "trace comments. Coding standard (Appendix D) is included below."
                   + (f" Write only your assigned file(s); {', '.join(others)} belong(s) to other RTL engineers "
                      "(instantiate them by the ports in arch.yaml)." if others else ""),
                   inputs=_inputs(ctx, inputs + [f"rtl/{m}.v" for m in mods]),
                   exit_criteria=["verilator --lint-only -Wall: 0 errors, 0 warnings", "yosys elaboration: 0 errors, "
                                  "no latches, no loops", "top ports match arch.yaml", "every REQ traced"],
                   schema=WRITER_ANSWER, previous_attempts=previous, relevant_knowledge=knowledge,
                   constraints="Coding standard:\n" + coding_std,
                   extra_note="Put every file you write in `files` (path rtl/<module>.v, full content). ")
    _answer_fields(ctx, owner, data)
    _write(ctx, owner, data["files"], "rtl", assigned={f"rtl/{m}.v" for m in mods})
    rounds = ctx.state.setdefault("rounds", {})
    rounds[owner] = rounds.get(owner, 0) + 1
    return True


# --- the agent ----------------------------------------------------------------------------------
class DesignAgent(Agent):
    """Runs a Zone 1 / 2A stage task (orchestrator agent kind "s2s")."""
    STAGES = {"spec": spec_steps, "architecture": arch_steps, "rtl": rtl_steps}

    def steps(self, task: Task) -> list[Step]:
        if task.stage not in self.STAGES:
            raise NotImplementedError(f"stage {task.stage!r} is not built yet (M0.5 covers spec, architecture, rtl)")
        steps = self.STAGES[task.stage]()
        for i, s in enumerate(steps):  # readable names in heartbeats
            if getattr(s, "__name__", "") == "<lambda>":
                s.__name__ = "task_result"
        return steps

