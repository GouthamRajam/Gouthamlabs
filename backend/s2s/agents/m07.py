"""M0.7 physical implementation and signoff: Zones 3 and 4 (MASTER_SPEC 13.2 M0.7).

OpenLane 2 is driven stage by stage (s2s.physical.flow); every check is decided by a real tool run,
and the model-written parts are inputs (constraints, floorplan choices, parameter changes) or
explanations of tool numbers. Directors: Mason (Division 3, Zone 3), Sloane (Division 4, Zone 4).

synthesis  (lead Sienna)  G2-frozen RTL check -> Sienna writes constraints.sdc (SDC guard: spec clock,
                          ranges, I/O delays, no unjustified exceptions) -> Sentinel reviews it (its
                          hash is then fixed) -> OpenLane synthesis + pre-layout STA -> eqy RTL vs
                          netlist -> Sienna explains the worst paths
dft        (lead Tess)    dft_plan.md (Phase 0: plan only; scan/ATPG need Phase 1 tools)
floorplan  (lead Grid)    Grid picks utilization (pnr_ranges.yaml) and the pin plan -> OpenLane floorplan,
                          tap cells, PDN, pins -> checks: utilization range, PDN violations, pins per plan
place_route (lead Orion)  placement -> CTS -> routing (+ antenna repair, fill, RCX, post-route STA) per
                          iteration; Orion changes at most 2 parameters per iteration, only inside
                          pnr_ranges.yaml, with a reason; budget = iteration_budget; Tick reports CTS;
                          Mason writes the Division 3 report
signoff    (lead Chronos) OpenLane signoff steps, then independent re-runs on the final streamed GDS:
                          Calla (Magic + KLayout DRC, extraction + Netgen LVS, antenna, PDK density deck),
                          Chronos (OpenSTA, 9 corners), Volta (power at 20% activity, IR drop), Fabian
                          (DFM scorecard), eqy RTL vs final netlist, gate-level simulation   -> G3
gdsii      (lead Gideon)  package + re-verification of the packaged GDS, Proof re-runs reproduce.sh in a
                          clean container and runs the diff guards, B.9 checklist, Part 22 readiness
                          report, release notes, signed manifest; Sloane writes the Division 4 report -> G4
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import time
from pathlib import Path

import yaml
from sqlalchemy import select

from s2s.agents import llm
from s2s.agents.m05 import (DesignAgent, _answer_fields, _author_loop, _inputs, _record, _sage_search, _task_result, _write,
                            stop_if_blocked)
from s2s.agents.m06 import _assign
from s2s.agents.runtime import Step, StepContext, artifact_dir
from s2s.config import REPO_ROOT, _load
from s2s.db.models import Artifact, Check, Gate, Task, UsageRecord
from s2s.design.schemas import FABIAN_ANSWER, ORION_ANSWER, REPORT_ANSWER, REVIEW_ANSWER
from s2s.physical import dfm, flow as olf, package as pk, readiness, signoff as so
from s2s.tools.klayout_drc import run_klayout_drc
from s2s.tools.magic_drc import run_magic_drc
from s2s.tools.opensta import run_opensta

MAX_ORION_ATTEMPTS = 3  # an invalid parameter proposal goes back with the exact problems


# --- shared helpers ----------------------------------------------------------------------------------
def _who(name: str) -> dict:
    return {"agent_id": name, "team": llm.agent(name).team}


def policy() -> dict:
    return _load("signoff.yaml", "S2S_SIGNOFF_CONFIG")


def _pnr(ctx: StepContext) -> Path:
    p = ctx.workdir / "pnr"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _phys(ctx: StepContext) -> dict:
    """Cross-stage facts of this run (frozen RTL hashes, reviewed SDC hash, current run tag, params)."""
    p = _pnr(ctx) / "s2s_physical.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _save_phys(ctx: StepContext, **kw) -> dict:
    d = {**_phys(ctx), **kw}
    p = _pnr(ctx) / "s2s_physical.json"
    p.write_text(json.dumps(d, indent=2) + "\n")
    ctx.artifact("physical.state", "pnr/s2s_physical.json", p.read_bytes(), agent_id=ctx.task.agent_id)
    return d


def _spec(ctx: StepContext) -> dict:
    return yaml.safe_load((ctx.workdir / "spec/spec.yaml").read_text())


def _top(ctx: StepContext) -> str:
    return yaml.safe_load((ctx.workdir / "arch/arch.yaml").read_text())["top"]


def _tool_json(ctx: StepContext, who: str, path: str, data) -> None:
    """Tool results written by the runtime (attributed to the agent who ran the tool)."""
    dest = ctx.workdir / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2, default=str) + "\n")
    ctx.artifact("report", path, dest.read_bytes(), agent_id=who, team=llm.agent(who).team)
    ctx.state.setdefault("outputs", {})[path] = hashlib.sha256(dest.read_bytes()).hexdigest()


def _run(ctx: StepContext, who: str, what: str, fn, *a, **kw):
    """Run a tool as `who`: tool_call event, heartbeat, compute metering."""
    ctx.emit("tool_call", f"{who}: {what}", **_who(who), detail={"tool": what.split()[0]})
    ctx.beat(f"{who}: {what[:150]}")
    t0 = time.monotonic()
    try:
        return fn(*a, **kw)
    finally:
        ctx.compute(what.split()[0], time.monotonic() - t0, agent_id=who)


def _result(ctx: StepContext, who: str, summary: str, detail: dict | None = None) -> None:
    ctx.emit("tool_result", f"{who}: {summary}"[:300], **_who(who), detail={"tool": "eda", **(detail or {})})


def _check(ctx: StepContext, who: str, name: str, tool: str, passed: bool, metrics: dict, command: str = "") -> bool:
    return ctx.check(name, tool, bool(passed), metrics, command=command, **_who(who))


def _explain(ctx: StepContext, who: str, goal: str, inputs: list[str], out_path: str, tool_data: dict,
             effort_note: str = "") -> dict:
    """The agent explains tool results it is given; numbers stay the tool's."""
    data = llm.ask(ctx, who, goal=goal, inputs=_inputs(ctx, inputs),
                   exit_criteria=["every number quoted comes from the tool data given", "plain English"],
                   schema=REPORT_ANSWER, extra_note="Put your report in `report_markdown`. The numbers come from the "
                   "tool results in your input files: quote them, never invent or change one. " + effort_note)
    _answer_fields(ctx, who, data)
    _write(ctx, who, [{"path": out_path, "content": json.dumps({
        **tool_data, "explained_by": who, "explanation": data["report_markdown"], "assumptions": data["assumptions"],
        "open_issues": data["open_issues"]}, indent=2, default=str)}], "report")
    return data


def _lineage(s, run_id: str) -> list[str]:
    """This run and its sources (task inputs.source_run, followed back to the M0.5 run)."""
    out, cur = [], run_id
    while cur and cur not in out:
        out.append(cur)
        t = s.scalars(select(Task).where(Task.run_id == cur).order_by(Task.seq)).first()
        cur = (t.inputs or {}).get("source_run") if t else None
    return out


def _latest_checks(s, run_ids: list[str], stage: str | None = None) -> dict[str, bool]:
    q = select(Check, Task.stage).join(Task, Task.id == Check.task_id).where(Task.run_id.in_(run_ids)).order_by(Check.id)
    out: dict[str, bool] = {}
    for c, st in s.execute(q):
        if stage is None or st == stage:
            out[c.check_name] = c.passed
    return out


def _spend(s, run_ids: list[str]) -> dict:
    from sqlalchemy import func
    rows = s.execute(select(UsageRecord.agent_id, func.sum(UsageRecord.cost_usd)).where(
        UsageRecord.run_id.in_(run_ids)).group_by(UsageRecord.agent_id)).all()
    return {a: round(float(c), 6) for a, c in rows}


# --- synthesis (Sienna; Mason directs Zone 3) ---------------------------------------------------------------
SDC_RULES = """CONSTRAINTS CONTRACT (checked by a deterministic SDC guard, then OpenROAD/OpenSTA read the file):
- create_clock on each spec clock port with the spec period EXACTLY: {clocks}
- set_clock_uncertainty within config/pnr_ranges.yaml [{umin}, {umax}] ns (default {udef}).
- set_max_fanout within [{fmin}, {fmax}] (default {fdef}).
- set_input_delay on every non-clock input ({ins}) and set_output_delay on every output ({outs}),
  each 0 <= delay < clock period; default 30% of the period unless the spec says otherwise (mark it DEFAULT
  in a comment). Use explicit port names, e.g. [get_ports {{load_data[*]}}] or one line per port.
- set_driving_cell / set_load may be added (mark assumptions DEFAULT).
- No set_false_path, set_multicycle_path, set_disable_timing, set_case_analysis, set_max_delay, set_min_delay or
  set_clock_groups unless the line directly above it is a comment starting `# JUSTIFICATION:` that explains why
  (never to hide timing).
- Clock propagation is the flow's job: never write the text "propagated_clock" anywhere in the file, not even in
  a comment (OpenLane searches the raw SDC text for it and, if found, never propagates the clock after CTS)."""


def _clock_override(ctx: StepContext):
    """Experiment runs only (M0.7 acceptance 2): task input `clock_override_mhz`; None on the product path."""
    return (ctx.task.inputs or {}).get("clock_override_mhz")


def _clocks(ctx: StepContext) -> list[dict]:
    """The clocks this run is constrained to: the spec's, or on an experiment run the first clock at the
    override frequency (recorded by the check clock_override_recorded). The SDC guard checks against these."""
    clocks = _spec(ctx)["clocks"]
    mhz = _clock_override(ctx)
    return clocks if mhz is None else [{**clocks[0], "freq_mhz": mhz}, *clocks[1:]]


def _override_note(ctx: StepContext) -> str:
    mhz = _clock_override(ctx)
    if mhz is None:
        return ""
    return (f"EXPERIMENT RUN (recorded): clock {_clocks(ctx)[0]['name']} is overridden from the spec's "
            f"{_spec(ctx)['clocks'][0]['freq_mhz']} MHz to {mhz} MHz ({1000.0 / float(mhz):g} ns) - acceptance "
            "experiment: intentionally tight clock. The constraints must use the override clock, not spec.yaml's.")


def _sdc_contract(ctx: StepContext) -> str:
    r = olf.ranges()
    spec = _spec(ctx)
    _, ins, outs = olf.port_bits(spec)
    clocks = ", ".join(f"{c['name']}: {1000.0 / float(c['freq_mhz']):g} ns ({c['freq_mhz']} MHz)" for c in _clocks(ctx))
    u, f = r["clock_uncertainty_ns"], r["max_fanout"]
    note = _override_note(ctx)
    return SDC_RULES.format(clocks=clocks, umin=u["min"], umax=u["max"], udef=u["default"], fmin=f["min"],
                            fmax=f["max"], fdef=f["default"], ins=", ".join(ins), outs=", ".join(outs)) + \
        ("\n- " + note if note else "")


def sdc_commands(text: str) -> list[str]:
    """The SDC's commands without comments and blank lines, whitespace normalized."""
    return [" ".join(ln.split("#", 1)[0].split()) for ln in text.splitlines() if ln.split("#", 1)[0].strip()]


def validate_sdc(ctx: StepContext) -> list[str]:
    p = ctx.workdir / "constraints/constraints.sdc"
    if not p.exists():
        problems = ["constraints/constraints.sdc was not written"]
        found = {}
    else:
        spec = _spec(ctx)
        _, ins, outs = olf.port_bits(spec)
        problems, found = olf.sdc_problems(p.read_text(), clocks=_clocks(ctx), inputs=ins, outputs=outs)
        keep = (ctx.task.inputs or {}).get("sdc_keep_commands_from")  # operator decision: comment-only rewrite
        if keep:
            old_cmds, new_cmds = sdc_commands((ctx.workdir / keep).read_text()), sdc_commands(p.read_text())
            if old_cmds != new_cmds:
                problems.append(f"only comments may change in this rewrite: every constraint command must stay "
                                f"exactly as in {keep} ({len(old_cmds)} commands); differences: "
                                f"{sorted(set(old_cmds) ^ set(new_cmds))[:4]}")
    _check(ctx, "Sienna", "sdc_guard", "s2s.physical.flow.sdc_problems", not problems,
           {"problems": len(problems), "detail": problems[:20], "found": found})
    return problems


def synthesis_steps() -> list[Step]:
    def setup(ctx: StepContext) -> None:
        src = ctx.task.inputs["source_run"]
        s = ctx.session
        g2 = s.scalars(select(Gate).where(Gate.run_id == src, Gate.gate == "G2")).first()
        root = artifact_dir() / "runs" / src
        for d in ("spec", "arch", "rtl", "tb"):
            shutil.copytree(root / d, ctx.workdir / d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        for f in ("request.md", "reports/verification_report.json"):
            if (root / f).exists():
                (ctx.workdir / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(root / f, ctx.workdir / f)
        # B.9 item 2: the RTL used here is the RTL G2 approved, byte for byte
        lineage = _lineage(s, src)
        tasks = [t.id for t in s.scalars(select(Task).where(Task.run_id.in_(lineage)))]
        frozen, problems = {}, []
        for f in sorted((ctx.workdir / "rtl").glob("*.v")):
            h = olf.sha(f)
            frozen[f.name] = h
            rec = s.scalars(select(Artifact).where(Artifact.sha256 == h, Artifact.path == f"rtl/{f.name}",
                                                   Artifact.created_by_task.in_(tasks))).first()
            if rec is None:
                problems.append(f"rtl/{f.name} (sha256 {h[:12]}) was never written by an agent of this design's runs")
            elif g2 is not None and g2.decided_at and rec.created_at and rec.created_at > g2.decided_at:
                problems.append(f"rtl/{f.name} was written after G2 was approved")
        if g2 is None or g2.status != "approved":
            problems.append(f"source run {src} has no approved G2 (RTL freeze); Zone 3 cannot start")
        _check(ctx, "Sienna", "rtl_frozen_at_g2", "sha256 vs artifact store + gate record", not problems,
               {"problems": problems, "frozen_rtl": frozen, "g2_gate": g2.id if g2 else None,
                "g2_decided_at": str(g2.decided_at) if g2 else None, "lineage": lineage})
        if problems:
            ctx.state["blocked"] = "; ".join(problems)
            return
        spec = _spec(ctx)
        mhz = _clock_override(ctx)
        if mhz is not None:
            ok = isinstance(mhz, (int, float)) and not isinstance(mhz, bool) and mhz > 0
            _check(ctx, "Mason", "clock_override_recorded", "s2s task input clock_override_mhz", ok,
                   {"spec_mhz": spec["clocks"][0]["freq_mhz"], "override_mhz": mhz,
                    "override_period_ns": round(1000.0 / float(mhz), 6) if ok else None,
                    "reason": "acceptance experiment: intentionally tight clock"})
            if not ok:
                ctx.state["blocked"] = f"clock_override_mhz {mhz!r} is not a positive number"
                return
            ctx.emit("plan", f"Mason: plan - {_override_note(ctx)} The SDC guard and the config guard check "
                     f"against {mhz} MHz.", agent_id="Mason")
        params = olf.default_params()
        strategy = (ctx.task.inputs or {}).get("synth_strategy")  # operator decision (recorded); absent = default
        if strategy is not None:
            ok = strategy in olf.SYNTH_STRATEGIES
            _check(ctx, "Mason", "synth_strategy_recorded", "s2s task input synth_strategy", ok,
                   {"synth_strategy": strategy, "allowed": olf.SYNTH_STRATEGIES,
                    "reason": (ctx.task.inputs or {}).get("synth_strategy_reason", "")})
            if not ok:
                ctx.state["blocked"] = f"synth_strategy {strategy!r} is not one of {olf.SYNTH_STRATEGIES}"
                return
            params["SYNTH_STRATEGY"] = strategy
            ctx.emit("plan", f"Mason: plan - synthesis strategy {strategy} (operator decision, an allowed "
                     "flow setting; no constraint changes)", agent_id="Mason")
        clk = _clocks(ctx)[0]
        _save_phys(ctx, source_run=src, lineage=lineage, frozen_rtl=frozen, top=_top(ctx),
                   clock_port=clk["name"], period_ns=round(1000.0 / float(clk["freq_mhz"]), 6),
                   params=params, tag="it1", iteration=1, start_stage="placement")
        ctx.emit("plan", f"Mason: plan - Zone 3 for {spec['design']}: constraints (Sienna, Sentinel review), synthesis + "
                 "equivalence, DFT plan (Tess), floorplan (Grid), placement/CTS/routing (Orion, Tick) within "
                 "pnr_ranges.yaml; every result from the tools", agent_id="Mason")
        for owner, goal in (("Sienna", "Constraints, synthesis, pre-layout STA, equivalence"),
                            ("Tess", "DFT plan (Phase 0: plan only)"), ("Grid", "Floorplan, pins, power grid"),
                            ("Orion", "Placement and routing within pnr_ranges.yaml"), ("Tick", "Clock tree")):
            _assign(ctx, "Mason", owner, goal, ["every check passes in the Trust Layer"], "checks passed / checks")

    def sienna_sdc(ctx: StepContext) -> None:
        keep = (ctx.task.inputs or {}).get("sdc_keep_commands_from")  # operator decision: comment-only rewrite
        goal = "Write constraints/constraints.sdc for this design from the spec (A.8 step 1)."
        if keep:
            goal = (f"Rewrite constraints/constraints.sdc as a COMMENT-ONLY edit of the reviewed SDC {keep}: keep every "
                    "constraint command exactly as it is (same commands, values and order) and reword or remove any "
                    "comment that breaks the contract below.")
        _author_loop(ctx, "Sienna", goal=goal,
                     inputs=["spec/spec.yaml", "arch/arch.yaml", *([keep] if keep else [])], validate=validate_sdc,
                     kind="constraints", constraints=_sdc_contract(ctx),
                     exit_criteria=["the SDC guard passes", "every assumption is marked DEFAULT"]
                     + (["every constraint command identical to the reviewed SDC"] if keep else []))

    def sentinel_constraints(ctx: StepContext) -> None:
        """Constraints are always reviewed (management.yaml always_review); the reviewed hash is fixed."""
        for rnd in (1, 2):
            data = llm.ask(ctx, "Sentinel", goal="Review constraints/constraints.sdc against the spec: is the clock "
                           "exactly the spec's, are I/O delays and uncertainty reasonable, is anything loosened or "
                           "any exception hiding timing? File findings only for real, specific problems."
                           + (" " + _override_note(ctx) if _clock_override(ctx) is not None else ""),
                           inputs=_inputs(ctx, ["spec/spec.yaml", "constraints/constraints.sdc"]),
                           exit_criteria=["every finding is specific: location, evidence, suggested action"],
                           schema=REVIEW_ANSWER, extra_note="Put each finding in `findings` (empty list if none). ")
            findings = data["findings"]
            path = "reports/sentinel_constraints.json" if rnd == 1 else "reports/sentinel_constraints_round2.json"
            _write(ctx, "Sentinel", [{"path": path, "content": json.dumps(findings, indent=2)}], "review")
            for f in findings:
                ctx.emit("finding", f"Sentinel [{f['severity']}] {f['target']}: {f['what'][:200]}", **_who("Sentinel"),
                         to_agent_id="Sienna", detail=f)
            blocking = [f for f in findings if f["severity"] == "blocking"]
            _record(ctx, "sentinel_constraints_review", [f"{f['target']}: {f['what']}" for f in blocking],
                    "sentinel", "Sentinel")
            if not blocking:
                break
            if rnd == 2:
                ctx.state["blocked"] = f"{len(blocking)} blocking Sentinel finding(s) on the constraints remain"
                return
            _author_loop(ctx, "Sienna", goal="Revise constraints/constraints.sdc to resolve Sentinel's blocking findings.",
                         inputs=["spec/spec.yaml", "arch/arch.yaml", "constraints/constraints.sdc", path],
                         validate=validate_sdc, kind="constraints", constraints=_sdc_contract(ctx),
                         previous="Sentinel's blocking findings:\n" + json.dumps(blocking, indent=2))
            if ctx.state.get("blocked"):
                return
        _save_phys(ctx, reviewed_sdc_sha=olf.sha(ctx.workdir / "constraints/constraints.sdc"))

    def synth(ctx: StepContext) -> None:
        ph, pnr = _phys(ctx), _pnr(ctx)
        olf.write_config(pnr, ph["top"], sorted((ctx.workdir / "rtl").glob("*.v")), ph["clock_port"], ph["period_ns"],
                         ctx.workdir / "constraints/constraints.sdc", ph["params"], None)
        guard = olf.config_guard(pnr, period_ns=ph["period_ns"], reviewed_sdc_sha=ph["reviewed_sdc_sha"],
                                 frozen_rtl=ph["frozen_rtl"])
        _check(ctx, "Sienna", "config_guard_synthesis", "s2s.physical.flow.config_guard", not guard, {"problems": guard})
        r = _run(ctx, "Sienna", "openlane synthesis (Verilator.Lint .. OpenROAD.STAPrePNR)", olf.run_stage, pnr, ph["tag"],
                 "synthesis")
        m = r["metrics"]
        setup = olf.corners(m, "timing__setup__ws")
        _result(ctx, "Sienna", f"synthesis {'ok' if r['ok'] else 'FAILED'}: {m.get('design__instance__count')} cells, "
                f"area {m.get('design__instance__area')} um2; pre-layout worst setup slack "
                f"{min(setup.values()) if setup else None} ns", {"failed_steps": r["failed_steps"], "errors": r["errors"][:5]})
        _check(ctx, "Sienna", "openlane_synthesis", "openlane " + str(r["tool_version"]),
               r["ok"] and m.get("synthesis__check_error__count", 1) == 0,
               {"exit_code": r["exit_code"], "errors": r["errors"][:10], "failed_steps": r["failed_steps"],
                "cells": m.get("design__instance__count"), "log": r["log"]}, r["command"])
        worst = sorted(setup.items(), key=lambda kv: kv[1])
        met = bool(setup) and worst[0][1] >= 0
        rpt = olf.step_dir(Path(r["run_dir"]), "OpenROAD.STAPrePNR")
        paths = ""
        if rpt and worst:
            mx = rpt / worst[0][0] / "max.rpt"
            paths = mx.read_text()[:12000] if mx.exists() else ""
        tool = {"cells": m.get("design__instance__count"), "area_um2": m.get("design__instance__area"),
                "cell_classes": {k.split(":", 1)[1]: v for k, v in m.items() if k.startswith("design__instance__count__class:")},
                "pre_layout_setup_ws_by_corner": setup, "pre_layout_hold_ws_by_corner": olf.corners(m, "timing__hold__ws"),
                "worst_corner": worst[0][0] if worst else None, "worst_paths_report": paths,
                "netlist": r["views"].get("nl"), "run": r["run_dir"]}
        _tool_json(ctx, "Sienna", "reports/synth_tool.json", tool)
        _check(ctx, "Sienna", "sta_pre_layout", "opensta (OpenROAD.STAPrePNR)", met,
               {"setup_ws_by_corner": setup, "note": "ideal clocks; hold is checked after CTS"})
        if not r["ok"]:
            ctx.state["blocked"] = f"synthesis failed: {r['errors'][:2] or r['failed_steps']}"
        elif not met:
            # A.8 step 5: an architectural path goes back to Kepler/Ada with the path and options
            ctx.emit("handoff", f"Sienna -> Kepler: ppa.request - pre-layout setup slack {worst[0][1]} ns at {worst[0][0]}",
                     **_who("Sienna"), to_agent_id="Kepler", detail={"message": "ppa.request", "worst": worst[:3]})
            ctx.state["blocked"] = "pre-layout timing fails; ppa.request sent to Kepler (architecture)"

    def eqy_synth(ctx: StepContext) -> None:
        ph = _phys(ctx)
        nl = json.loads((ctx.workdir / "reports/synth_tool.json").read_text())["netlist"]
        r = _run(ctx, "Sienna", "eqy RTL vs synthesized netlist", so.equivalence,
                 sorted((ctx.workdir / "rtl").glob("*.v")), Path(nl), ph["top"], ctx.workdir, "synth")
        _result(ctx, "Sienna", f"equivalence RTL vs synthesized netlist: {r.status} via {r.metrics.get('method')} "
                f"(eqy {len(r.metrics['partitions_proven'])} partitions proven, failed {r.metrics['partitions_failed']}; "
                f"LEC points proven {r.metrics.get('lec_points_proven')}, unproven {r.metrics.get('lec_points_unproven')})")
        _check(ctx, "Sienna", "eqy_rtl_vs_synth", f"eqy {r.tool_version}", r.passed,
               {"status": r.metrics["status"], "method": r.metrics.get("method"),
                "proven": len(r.metrics["partitions_proven"]), "failed": r.metrics["partitions_failed"],
                "lec_points_proven": r.metrics.get("lec_points_proven"),
                "lec_points_unproven": r.metrics.get("lec_points_unproven"), "reasons": r.reasons[:3],
                "log": r.log_path, "lec_log": r.metrics.get("lec_log")}, r.command)
        if not r.passed:
            ctx.state["blocked"] = "RTL and synthesized netlist are not proven equivalent (A.8: blocking)"

    def sienna_report(ctx: StepContext) -> None:
        tool = json.loads((ctx.workdir / "reports/synth_tool.json").read_text())
        _tool_json(ctx, "Sienna", "reports/sta_pre.json", {k: tool[k] for k in (
            "pre_layout_setup_ws_by_corner", "pre_layout_hold_ws_by_corner", "worst_corner")})
        _explain(ctx, "Sienna", "Report synthesis (cells, area) and pre-layout STA: WNS per corner and the worst "
                 "paths in plain English (where each starts and ends, what dominates the delay) (A.8 step 3).",
                 ["spec/spec.yaml", "constraints/constraints.sdc", "reports/synth_tool.json"],
                 "reports/synth_report.json", {k: v for k, v in tool.items() if k != "worst_paths_report"})

    def result(ctx: StepContext) -> None:
        _task_result(ctx, "synthesis")

    return [setup, stop_if_blocked, sienna_sdc, stop_if_blocked, sentinel_constraints, stop_if_blocked, synth,
            stop_if_blocked, eqy_synth, stop_if_blocked, sienna_report, result]


# --- dft (Tess) -----------------------------------------------------------------------------------------------
DFT_SECTIONS = ("test strategy", "scan", "test pins", "coverage", "memory", "limitation")


def validate_dft(ctx: StepContext) -> list[str]:
    p = ctx.workdir / "dft/dft_plan.md"
    text = p.read_text().lower() if p.exists() else ""
    problems = ["dft/dft_plan.md was not written"] if not text else \
        [f"dft_plan.md has no section on '{s}'" for s in DFT_SECTIONS if s not in text]
    _check(ctx, "Tess", "dft_plan_complete", "s2s section check", not problems, {"problems": problems})
    return problems


def dft_steps() -> list[Step]:
    def tess(ctx: StepContext) -> None:
        _author_loop(ctx, "Tess", goal="Write dft/dft_plan.md (Phase 0 scope, A.9): test strategy, scan approach, test "
                     "pins, expected coverage method, memory test approach, limitations of the open flow. The open "
                     "OpenLane 2 Classic flow used here has no scan insertion or ATPG step, so state the plan only.",
                     inputs=["spec/spec.yaml", "arch/arch.yaml", "reports/synth_tool.json"], validate=validate_dft,
                     kind="dft_plan", exit_criteria=["all six sections present", "no claim of a coverage number"])

    def result(ctx: StepContext) -> None:
        _task_result(ctx, "dft")

    return [tess, stop_if_blocked, result]


# --- floorplan (Grid) -----------------------------------------------------------------------------------------
def validate_floorplan(ctx: StepContext) -> list[str]:
    problems = []
    fp = ctx.workdir / "pnr/floorplan.json"
    try:
        d = json.loads(fp.read_text())
        util = d["core_utilization_pct"]
        reasons = d["reasons"]
        problems += olf.check_params({"FP_CORE_UTIL": util})
        for k in ("utilization", "pins", "power_grid", "clock_reset"):
            if not str(reasons.get(k, "")).strip():
                problems.append(f"floorplan.json reasons.{k} is missing (every choice needs a reason)")
    except FileNotFoundError:
        problems.append("pnr/floorplan.json was not written")
    except (ValueError, KeyError, TypeError) as e:
        problems.append(f"pnr/floorplan.json must be JSON with core_utilization_pct and reasons{{utilization, pins, "
                        f"power_grid, clock_reset}}: {e!r}")
    cfg = ctx.workdir / "pnr/pin_order.cfg"
    bits, _, _ = olf.port_bits(_spec(ctx))
    problems += olf.pin_cfg_problems(cfg.read_text(), bits) if cfg.exists() else ["pnr/pin_order.cfg was not written"]
    if cfg.exists() and not problems:  # the real parser OpenLane will use decides the syntax
        problems += olf.pin_cfg_parser_problems(cfg, ctx.workdir)
    _check(ctx, "Grid", "floorplan_plan", "s2s.physical.flow (ranges + pin file)", not problems, {"problems": problems})
    return problems


FLOORPLAN_FORMAT = """FILES TO WRITE
1. pnr/floorplan.json: {"core_utilization_pct": <number within config/pnr_ranges.yaml core_utilization_pct>,
   "reasons": {"utilization": "...", "pins": "...", "power_grid": "...", "clock_reset": "..."}}
   The power grid uses the PDK's default SKY130 PDN (pnr_ranges.yaml has no strap ranges, so straps stay at default).
2. pnr/pin_order.cfg: OpenLane pin order file. Sections `#N`, `#S`, `#E`, `#W`, then one pin pattern per line.
   Keep patterns simple: a port name (`clk`) or a bus prefix with `.*` (`count.*` matches count[0]..count[7]).
   OpenLane's own parser checks the file and has a narrow grammar (no anchors `^`/`$`, no character ranges
   like `[0-7]`); its exact error comes back to you if it rejects a line.
   Every pin must match exactly one pattern; every pattern must match a pin. Inputs on one side and outputs on
   the other where sensible, following the data flow in arch.yaml."""


def floorplan_steps() -> list[Step]:
    def grid(ctx: StepContext) -> None:
        _tool_json(ctx, "Grid", "reports/pnr_ranges.json", olf.ranges())
        _author_loop(ctx, "Grid", goal="Choose the floorplan (A.10 steps 1-3): core utilization from the synthesized "
                     "cell area within the allowed range, pin placement following the data flow, power grid.",
                     inputs=["spec/spec.yaml", "arch/arch.yaml", "reports/synth_tool.json", "reports/pnr_ranges.json"],
                     validate=validate_floorplan, kind="floorplan", constraints=FLOORPLAN_FORMAT,
                     exit_criteria=["utilization inside pnr_ranges.yaml", "every pin placed exactly once", "a reason per choice"])

    def fp_run(ctx: StepContext) -> None:
        ph, pnr = _phys(ctx), _pnr(ctx)
        fp = json.loads((pnr / "floorplan.json").read_text())
        params = {**ph["params"], "FP_CORE_UTIL": fp["core_utilization_pct"]}
        ph = _save_phys(ctx, params=params)
        olf.write_config(pnr, ph["top"], sorted((ctx.workdir / "rtl").glob("*.v")), ph["clock_port"], ph["period_ns"],
                         ctx.workdir / "constraints/constraints.sdc", params, pnr / "pin_order.cfg")
        guard = olf.config_guard(pnr, period_ns=ph["period_ns"], reviewed_sdc_sha=ph["reviewed_sdc_sha"],
                                 frozen_rtl=ph["frozen_rtl"])
        _check(ctx, "Grid", "config_guard_floorplan", "s2s.physical.flow.config_guard", not guard, {"problems": guard})
        r = _run(ctx, "Grid", "openlane floorplan (OpenROAD.Floorplan .. Odb.ApplyDEFTemplate)", olf.run_stage, pnr,
                 ph["tag"], "floorplan")
        m = r["metrics"]
        _check(ctx, "Grid", "openlane_floorplan", "openlane " + str(r["tool_version"]), r["ok"],
               {"exit_code": r["exit_code"], "errors": r["errors"][:10], "log": r["log"]}, r["command"])
        rg = olf.ranges()["core_utilization_pct"]
        util = m.get("design__instance__utilization")
        _check(ctx, "Grid", "utilization_in_range", "openroad (floorplan metrics)",
               util is not None and rg["min"] <= 100 * util <= rg["max"],
               {"utilization_pct": None if util is None else round(100 * util, 2), "range": rg,
                "target_pct": fp["core_utilization_pct"]})
        pdn = m.get("design__power_grid_violation__count")
        _check(ctx, "Grid", "pdn_connected", "openroad pdn (GeneratePDN check)", pdn == 0,
               {"power_grid_violations": pdn, "by_net": {k: v for k, v in m.items() if k.startswith(
                   "design__power_grid_violation__count__net")}})
        pins = olf.def_pins(Path(r["views"]["def"]).read_text()) if r["views"].get("def") else []
        sides = olf.pin_cfg_sides((pnr / "pin_order.cfg").read_text())
        bits, _, _ = olf.port_bits(_spec(ctx))
        wrong = [f"{p['name']} on {p['side']}, planned {olf.pin_side_of(p['name'], sides)}" for p in pins
                 if p["side"] not in olf.pin_side_of(p["name"], sides)]
        missing = sorted(set(bits) - {p["name"] for p in pins})
        _check(ctx, "Grid", "pins_per_plan", "DEF pins vs pin_order.cfg", bool(pins) and not wrong and not missing,
               {"pins": len(pins), "wrong_side": wrong[:20], "missing": missing})
        _result(ctx, "Grid", f"floorplan: die {m.get('design__die__area')} um2, core {m.get('design__core__area')} um2, "
                f"utilization {util}, PDN violations {pdn}, {len(pins)} pins ({len(wrong)} off-plan)")
        _tool_json(ctx, "Grid", "reports/floorplan_tool.json", {
            "die_area_um2": m.get("design__die__area"), "core_area_um2": m.get("design__core__area"),
            "utilization": util, "power_grid_violations": pdn, "pins": pins})
        _tool_json(ctx, "Grid", "reports/floorplan_report.json", {
            **json.loads((ctx.workdir / "reports/floorplan_tool.json").read_text()), "choices": fp})
        if not r["ok"] or guard:
            ctx.state["blocked"] = f"floorplan failed: {(r['errors'] or guard)[:2]}"

    def result(ctx: StepContext) -> None:
        _task_result(ctx, "floorplan")

    return [grid, stop_if_blocked, fp_run, stop_if_blocked, result]


# --- place_route (Orion, Tick; Mason reports) -------------------------------------------------------------------
PNR_STAGES = ("placement", "cts", "routing")


def _cts_data(ctx: StepContext, run_dir: Path, m: dict, period: float) -> dict:
    """Tick's numbers. Skew per corner from the routed design (STAPostPNR: 9 corners, setup and hold
    reports); OpenROAD's reported skew includes the SDC uncertainty, so the tree's own skew is the
    reported skew minus it. Slack right after CTS from STAMidPNR-2 (the hold effect of the tree)."""
    d = olf.step_dir(run_dir, "OpenROAD.STAPostPNR")
    per = {}
    for corner_dir in sorted(p for p in (d.iterdir() if d else []) if p.is_dir()):
        row = {}
        for kind, f in (("setup", "skew.max.rpt"), ("hold", "skew.min.rpt")):
            if (corner_dir / f).exists():
                row[kind] = olf.parse_skew((corner_dir / f).read_text())
        if row:
            per[corner_dir.name] = row
    vals = [v["tree_skew_ns"] for row in per.values() for v in row.values() if v["tree_skew_ns"] is not None]
    target = period * policy()["cts"]["max_skew_pct_of_period"] / 100
    mid = olf.step_dir(run_dir, "OpenROAD.STAMidPNR-2")
    mm = json.loads((mid / "state_out.json").read_text()).get("metrics", {}) if mid and (mid / "state_out.json").exists() else {}
    return {"per_corner": per, "corners_with_skew": len(per), "worst_tree_skew_ns": max(vals) if vals else None,
            "target_ns": round(target, 4), "clock_buffers": m.get("design__instance__count__class:clock_buffer"),
            "hold_ws_after_cts_by_corner": olf.corners(mm, "timing__hold__ws"),
            "setup_ws_after_cts_by_corner": olf.corners(mm, "timing__setup__ws"),
            "hold_buffers": m.get("design__instance__count__hold_buffer"),
            "timing_repair_buffers": m.get("design__instance__count__class:timing_repair_buffer")}


def _route_problems(m: dict, cts: dict) -> tuple[list[str], dict]:
    setup, hold = olf.corners(m, "timing__setup__ws"), olf.corners(m, "timing__hold__ws")
    facts = {"route_drc_errors": m.get("route__drc_errors"), "antenna_violating_nets": m.get("antenna__violating__nets"),
             "antenna_violating_pins": m.get("antenna__violating__pins"),
             "disconnected_pins": m.get("design__disconnected_pin__count"),
             "setup_ws_by_corner": setup, "hold_ws_by_corner": hold,
             "max_slew_violations": m.get("design__max_slew_violation__count"),
             "max_cap_violations": m.get("design__max_cap_violation__count"),
             "max_fanout_violations": m.get("design__max_fanout_violation__count"),
             "wirelength_um": m.get("route__wirelength"), "utilization": m.get("design__instance__utilization"),
             "cts_worst_tree_skew_ns": cts["worst_tree_skew_ns"], "cts_target_ns": cts["target_ns"]}
    p = []
    # max fanout: judged by the independent check, which applies the clock-tree rule (config/signoff.yaml
    # cts.clock_max_fanout); OpenLane's count must agree with its raw count (_independent_drv)
    for k in ("route_drc_errors", "antenna_violating_nets", "antenna_violating_pins", "disconnected_pins",
              "max_slew_violations", "max_cap_violations"):
        if facts[k] is None:
            p.append(f"{k} not reported")
        elif facts[k] != 0:
            p.append(f"{k} = {facts[k]}")
    if len(setup) < 9 or len(hold) < 9:
        p.append(f"post-route STA reported {len(setup)} setup / {len(hold)} hold corners (expected 9)")
    p += [f"setup slack {v:.4f} ns at {c}" for c, v in setup.items() if v < 0]
    p += [f"hold slack {v:.4f} ns at {c}" for c, v in hold.items() if v < 0]
    if cts["corners_with_skew"] < 9:
        p.append(f"clock skew reported for {cts['corners_with_skew']} corners (expected 9)")
    if cts["worst_tree_skew_ns"] is None or cts["worst_tree_skew_ns"] > cts["target_ns"]:
        p.append(f"clock-tree skew {cts['worst_tree_skew_ns']} ns above target {cts['target_ns']} ns")
    return p, facts


def _independent_drv(ctx: StepContext, r: dict, k: int, top: str) -> tuple[list[str], dict]:
    """Max slew / capacitance / fanout from S2S's own OpenSTA run on the routed netlist with the reviewed SDC.
    OpenLane's post-route STA can report 0 fanout violators where OpenSTA on the same netlist and SDC reports
    clock buffers over the limit (uart 2026-10-06: clkbuf_0_clk fanout 16 vs 10, caught only at signoff), so a
    violator from EITHER tool is a place-and-route problem. Fanout is structural; the slowest library corner
    is used and slew/cap without parasitics stay OpenLane's (with SPEF)."""
    nl = (r.get("views") or {}).get("nl")
    if not nl or not Path(nl).exists():
        return ["independent DRV check: routed netlist not found"], {"independent_drv_pins": None}
    res = _run(ctx, "Orion", f"opensta report_check_types on the routed netlist (iteration {k})", run_opensta,
               Path(nl), ctx.workdir / "pnr/src/constraints.sdc", top, ctx.workdir, corner="ss_100C_1v60",
               post_route=True, tag=f"pnr_it{k}_drv", paths=1)
    pins = res.metrics.get("drv_violator_pins")
    if res.status in ("ERROR", "TIMEOUT") or pins is None:
        return [f"independent DRV check did not run cleanly ({res.status})"], {"independent_drv_pins": None}
    keep, allowed = so.apply_clock_fanout_rule(pins, Path(nl).read_text(errors="replace"),
                                               float(policy()["cts"]["clock_max_fanout"]))
    p = [f"independent STA: {v['kind']} {v['pin']} {v['value']:g} (limit {v['limit']:g})" for v in keep]
    ol = (r.get("metrics") or {}).get("design__max_fanout_violation__count")
    raw = sum(1 for v in pins if v["kind"] == "max fanout")
    if ol is None or int(ol) != raw:
        p.append(f"max fanout counts disagree: OpenLane {ol} vs S2S OpenSTA {raw} (same netlist and SDC)")
    return p, {"independent_drv_pins": keep, "clock_rule_allowed": allowed, "independent_drv_log": res.log_path}


def unpropagated_clocks(run_dir: Path) -> dict[str, list[str]]:
    """Clocks OpenLane's post-route STA left ideal, per corner (its unpropagated.rpt). After CTS every clock must be
    propagated; an ideal clock hides clock latency and skips the clock nets' slew/cap/fanout checks."""
    d = olf.step_dir(run_dir, "OpenROAD.STAPostPNR")
    out: dict[str, list[str]] = {}
    for rpt in sorted(d.glob("*/unpropagated.rpt")) if d else []:
        for clk in rpt.read_text(errors="replace").split():
            out.setdefault(clk, []).append(rpt.parent.name)
    return out


CLUSTER_KNOBS = ("CTS_SINK_CLUSTERING_SIZE", "CTS_SINK_CLUSTERING_MAX_DIAMETER")


def pnr_diagnosis(run_dir: Path, nl: str | None, violators: list[dict] | None) -> dict:
    """Tool facts Orion must diagnose from BEFORE proposing a change (CEO 2026-10-06: analyze the problem before
    iterating). CTS log: sinks, whether sink clustering was applied, the H-tree stop rule, levels. Netlist: for each
    violating pin, its clock-tree level and what it drives (cell kinds and counts)."""
    out: dict = {"cts": None, "violators": []}
    logs = sorted(Path(run_dir).glob("*-openroad-cts/openroad-cts.log"))
    if logs:
        log = logs[-1].read_text(errors="replace")
        g = lambda rx: (lambda m: int(m.group(1)) if m else None)(re.search(rx, log))
        after = g(r"sinks after clustering:\s*(\d+)")
        out["cts"] = {"sinks": g(r"Total number of sinks:\s*(\d+)"), "clustering_applied": after is not None,
                      "sinks_after_clustering": after, "htree_stop_max_sinks": g(r"Max number of sinks is (\d+)"),
                      "levels": g(r"Max level of the clock tree:\s*(\d+)"),
                      "buffers": g(r"Total number of Buffers Inserted:\s*(\d+)")}
    text = Path(nl).read_text(errors="replace") if nl and Path(nl).exists() else ""
    for v in violators or []:
        inst = v["pin"].rsplit("/", 1)[0]
        lvl = re.match(r"clkbuf_(\d+)_", inst)
        row = {**v, "clock_tree_level": int(lvl.group(1)) if lvl else None, "loads_by_cell": None}
        m = re.search(rf"^\s*\S+\s+{re.escape(inst)}\s*\(([^;]*?)\);", text, re.M)
        x = re.search(r"\.X\(\s*(\S+?)\s*\)", m.group(1)) if m else None
        if x:
            kinds: dict[str, int] = {}
            for cell, _i, body in re.findall(r"^\s*(\S+)\s+(\S+)\s*\(([^;]*?)\);", text, re.M):
                if re.search(rf"\.(?!X\b)\w+\(\s*{re.escape(x.group(1))}\s*\)", body):
                    kinds[cell.split("__")[-1]] = kinds.get(cell.split("__")[-1], 0) + 1
            row["loads_by_cell"] = kinds
        out["violators"].append(row)
    return out


def diagnosis_refusals(changes: list[dict], diagnosis: dict | None, facts: dict, table: list[dict]) -> list[str]:
    """Changes refused because the tool facts show they cannot act on the problem."""
    bad = []
    d = diagnosis or {}
    if changes and (not str(d.get("root_cause", "")).strip() or not d.get("evidence")):
        bad.append("diagnose first: give root_cause and the tool facts (evidence) before proposing a change")
    cts = (facts or {}).get("cts") or {}
    if cts.get("clustering_applied") is False:
        for c in changes:
            if c["param"] in CLUSTER_KNOBS:
                bad.append(f"{c['param']}: the CTS log shows sink clustering was NOT applied "
                           f"({cts.get('sinks')} sinks, no 'sinks after clustering'), so it cannot change the tree")
    if len(table) >= 2 and table[-1]["problems"] == table[-2]["problems"]:
        last = {c["param"] for c in table[-1].get("changes") or []}
        for c in changes:
            if c["param"] in last:
                bad.append(f"{c['param']}: the last change to it left the problems identical; it does not act here")
    return bad


def _orion_changes(ctx: StepContext, k: int, problems: list[str]) -> dict:
    """Orion proposes at most two changes within pnr_ranges.yaml; invalid proposals go back verbatim."""
    ph = _phys(ctx)
    previous = ""
    guidance = (ctx.task.inputs or {}).get("operator_guidance")  # recorded operator decision, if any
    knowledge = _sage_search(ctx, "Orion", "place route " + " ".join(problems))  # S2S's own lessons first
    for attempt in range(1, MAX_ORION_ATTEMPTS + 1):
        data = llm.ask(ctx, "Orion", goal=f"Iteration {k} has problems: {problems}. FIRST diagnose: from the tool "
                       f"facts in reports/pnr_iteration_{k}.json (`diagnosis`: CTS log facts, each violator's tree level "
                       "and what it drives) state the root cause, the facts it rests on, and why a parameter acts on "
                       "that cause. THEN change at most two parameters, only inside config/pnr_ranges.yaml, with a "
                       "one-line reason each (A.10 step 3); or escalate if no allowed change can act on the cause."
                       + (f" OPERATOR GUIDANCE (CEO decision): {guidance}" if guidance else ""),
                       inputs=_inputs(ctx, ["spec/spec.yaml", "reports/pnr_ranges.json", "reports/pnr_iterations.json",
                                            f"reports/pnr_iteration_{k}.json"]),
                       exit_criteria=["<= 2 changes", "each inside pnr_ranges.yaml", "a reason per change"],
                       schema=ORION_ANSWER, previous_attempts=previous, relevant_knowledge=knowledge,
                       constraints=f"Current parameters: {json.dumps(ph['params'])} (a missing key is at its "
                       "pnr_ranges.yaml default). Tunable: FP_CORE_UTIL (percent; reruns from floorplan), "
                       "PL_TARGET_DENSITY_PCT (percent = placement_density x 100), MAX_FANOUT_CONSTRAINT (the resizer's "
                       "fanout target; the SDC set_max_fanout that STA checks is NOT changed by it), "
                       "CTS_SINK_CLUSTERING_SIZE (max flip-flops per clock-tree leaf buffer), GRT_ANTENNA_ITERS (antenna "
                       "repair iterations), GRT_ANTENNA_MARGIN (percent of over-fix in antenna repair), "
                       "CTS_SINK_CLUSTERING_MAX_DIAMETER (um; max diameter of a leaf cluster), "
                       "CTS_DISTANCE_BETWEEN_BUFFERS (um between clock buffers on tree wires; 0 = automatic) and "
                       "CTS_CLK_MAX_WIRE_LENGTH (um; 0 = no limit) - these two add buffers along the upper tree. "
                       "Antenna repair inserts diode cells, and each diode is a load that counts toward a net's "
                       "fanout. Before changing a clock-tree setting, name the tree LEVEL of each violating clock "
                       "buffer (clkbuf_<level>_* = an upper/trunk level driving leaf buffers; leaf buffers drive "
                       "flip-flops) and pick a setting that controls that level: smaller leaf clusters create MORE "
                       "leaf buffers and RAISE upper-level fanout (sync_fifo iteration 9). The clock, constraints "
                       "and rule decks are not yours to change.",
                       extra_note="Put the changes in `changes` and set `escalate`. ")
        _answer_fields(ctx, "Orion", data)
        ch = data["changes"]
        new = {**ph["params"], **{c["param"]: c["value"] for c in ch}}
        bad = olf.check_params(new)
        if len(ch) > 2:
            bad.append(f"{len(ch)} changes proposed; at most 2 per iteration")
        if not ch and not data["escalate"]["needed"]:
            bad.append("no change and no escalation")
        if any(ph["params"].get(c["param"]) == c["value"] for c in ch):
            bad.append("a 'change' that keeps the current value")
        if any(not c["reason"].strip() for c in ch):
            bad.append("every change needs a one-line reason")
        it = json.loads((ctx.workdir / f"reports/pnr_iteration_{k}.json").read_text()) \
            if (ctx.workdir / f"reports/pnr_iteration_{k}.json").exists() else {}
        table = json.loads((ctx.workdir / "reports/pnr_iterations.json").read_text()) \
            if (ctx.workdir / "reports/pnr_iterations.json").exists() else []
        bad += diagnosis_refusals(ch, data.get("diagnosis"), it.get("diagnosis") or {}, table)
        _check(ctx, "Orion", "orion_change_in_range", "s2s.physical.flow.check_params", not bad,
               {"iteration": k, "changes": ch, "problems": bad})
        if not bad or data["escalate"]["needed"]:
            return data
        previous = "Your proposal was refused by the range check (exact output):\n- " + "\n- ".join(bad)
    return {"changes": [], "escalate": {"needed": True, "why": "no valid change after 3 proposals"}}


def place_route_steps() -> list[Step]:
    def pnr_loop(ctx: StepContext) -> None:
        pnr = _pnr(ctx)
        budget = int(olf.ranges()["iteration_budget"])
        table: list[dict] = json.loads((ctx.workdir / "reports/pnr_iterations.json").read_text()) \
            if (ctx.workdir / "reports/pnr_iterations.json").exists() else []
        start_stage = _phys(ctx).get("start_stage", "placement")  # a resumed iteration starts where it was set to
        while True:
            ph = _phys(ctx)
            k, tag = ph["iteration"], ph["tag"]
            for st in olf.ORDER[olf.ORDER.index(start_stage):olf.ORDER.index("routing") + 1]:
                who = {"synthesis": "Sienna", "floorplan": "Grid", "cts": "Tick"}.get(st, "Orion")
                r = _run(ctx, who, f"openlane {st} (iteration {k}, {olf.STAGES[st][0]} .. {olf.STAGES[st][1]})",
                         olf.run_stage, pnr, tag, st)
                _check(ctx, who, f"openlane_{st}", "openlane " + str(r["tool_version"]), r["ok"],
                       {"iteration": k, "exit_code": r["exit_code"], "errors": r["errors"][:10],
                        "failed_steps": r["failed_steps"], "log": r["log"]}, r["command"])
                _result(ctx, who, f"{st} (iteration {k}): {'ok' if r['ok'] else 'FAILED ' + str(r['errors'][:2])}")
                if not r["ok"]:
                    break
            m = r["metrics"]
            cts = _cts_data(ctx, Path(r["run_dir"]), m, ph["period_ns"])
            problems, facts = _route_problems(m, cts) if r["ok"] else ([f"{st} failed: {r['errors'][:3]}"], {})
            if r["ok"]:
                p2, f2 = _independent_drv(ctx, r, k, ph["top"])
                problems += p2
                facts.update(f2)
                unprop = unpropagated_clocks(Path(r["run_dir"]))
                facts["openlane_unpropagated_clocks"] = unprop
                problems += [f"OpenLane post-route STA ran with clock '{c}' unpropagated (ideal) at {', '.join(cs)}"
                             for c, cs in unprop.items()]
            row = {"iteration": k, "tag": tag, "params": ph["params"], "problems": problems, "facts": facts,
                   "changes": ph.get("last_changes", [])}
            if problems and r["ok"]:
                row["diagnosis"] = pnr_diagnosis(Path(r["run_dir"]), (r.get("views") or {}).get("nl"),
                                                 facts.get("independent_drv_pins"))
            table.append(row)
            _tool_json(ctx, "Orion", f"reports/pnr_iteration_{k}.json", {**row, "cts": cts})
            _tool_json(ctx, "Orion", "reports/pnr_iterations.json", table)
            _result(ctx, "Orion", f"iteration {k}: {len(problems)} problem(s){': ' + '; '.join(problems[:3]) if problems else ' - routed clean, timing met at all corners'}")
            if not problems:
                _tool_json(ctx, "Tick", "reports/cts_tool.json", {"iteration": k, **cts})
                break
            if k >= budget:
                ctx.emit("escalation", f"Orion: iteration budget ({budget}) used; escalated to Mason with the table",
                         **_who("Orion"), to_agent_id="Mason", detail={"table": table})
                ctx.state["blocked"] = f"place and route not clean after {budget} iterations: {problems[:3]}"
                break
            data = _orion_changes(ctx, k, problems)
            if data["escalate"]["needed"] or not data["changes"]:
                ctx.emit("escalation", f"Orion escalated to Mason: {data['escalate']['why'][:200]}", **_who("Orion"),
                         to_agent_id="Mason", detail={"table": table})
                ctx.state["blocked"] = f"Orion escalated: {data['escalate']['why'][:300]}"
                break
            for c in data["changes"]:
                ctx.emit("plan", f"Orion: {c['param']} {ph['params'].get(c['param'])} -> {c['value']}: {c['reason']}"[:300],
                         **_who("Orion"), detail=c)
            new = {**ph["params"], **{c["param"]: c["value"] for c in data["changes"]}}
            start_stage = min((olf.TUNABLE[c["param"]][2] for c in data["changes"]), key=olf.ORDER.index)
            new_tag = f"it{k + 1}"
            if start_stage == "synthesis":
                (pnr / "runs" / new_tag).mkdir(parents=True, exist_ok=True)
            else:
                olf.fork(pnr, tag, new_tag, start_stage)
            ph = _save_phys(ctx, params=new, tag=new_tag, iteration=k + 1, last_changes=data["changes"],
                            start_stage=start_stage)
            olf.write_config(pnr, ph["top"], sorted((ctx.workdir / "rtl").glob("*.v")), ph["clock_port"],
                             ph["period_ns"], ctx.workdir / "constraints/constraints.sdc", new, pnr / "pin_order.cfg")
            guard = olf.config_guard(pnr, period_ns=ph["period_ns"], reviewed_sdc_sha=ph["reviewed_sdc_sha"],
                                     frozen_rtl=ph["frozen_rtl"])
            if guard:
                ctx.state["blocked"] = f"config guard refused iteration {k + 1}: {guard}"
                break
        ph = _phys(ctx)
        guard = olf.config_guard(pnr, period_ns=ph["period_ns"], reviewed_sdc_sha=ph["reviewed_sdc_sha"],
                                 frozen_rtl=ph["frozen_rtl"])
        _check(ctx, "Orion", "pnr_params_in_range", "s2s.physical.flow.config_guard", not guard,
               {"problems": guard, "params": ph["params"], "iterations": len(table)})
        last = table[-1]
        f = last["facts"]
        clean = not last["problems"]
        _check(ctx, "Orion", "route_drc_zero", "openroad detailed routing", f.get("route_drc_errors") == 0,
               {"route_drc_errors": f.get("route_drc_errors")})
        _check(ctx, "Orion", "antenna_clean_after_route", "openroad check_antennas",
               f.get("antenna_violating_nets") == 0 and f.get("antenna_violating_pins") == 0,
               {"nets": f.get("antenna_violating_nets"), "pins": f.get("antenna_violating_pins")})
        _check(ctx, "Orion", "no_disconnected_pins", "odb", f.get("disconnected_pins") == 0,
               {"disconnected_pins": f.get("disconnected_pins")})
        _check(ctx, "Tick", "cts_skew_target", "openroad report_clock_skew (minus SDC uncertainty)",
               f.get("cts_worst_tree_skew_ns") is not None and f["cts_worst_tree_skew_ns"] <= f["cts_target_ns"],
               {"worst_tree_skew_ns": f.get("cts_worst_tree_skew_ns"), "target_ns": f.get("cts_target_ns")})
        _check(ctx, "Orion", "post_route_timing_all_corners", "opensta (OpenROAD.STAPostPNR)", clean or not [
            p for p in last["problems"] if "slack" in p or "corners" in p],
               {"setup": f.get("setup_ws_by_corner"), "hold": f.get("hold_ws_by_corner")})
        _check(ctx, "Orion", "drv_clean", "opensta report_check_types (OpenLane post-route + S2S on the routed netlist)",
               all(f.get(k) == 0 for k in ("max_slew_violations", "max_cap_violations"))
               and f.get("independent_drv_pins") == [],
               {**{k: f.get(k) for k in ("max_slew_violations", "max_cap_violations", "max_fanout_violations")},
                "independent_drv_pins": f.get("independent_drv_pins"), "clock_rule_allowed": f.get("clock_rule_allowed")})
        ctx.evidence = f"{len(table)} iteration(s); {'clean' if clean else 'not clean'}"

    def tick(ctx: StepContext) -> None:
        cts = json.loads((ctx.workdir / "reports/cts_tool.json").read_text())
        _explain(ctx, "Tick", "Report the clock tree (A3.14): skew target and the measured per-corner skew, latency, "
                 "clock buffers, and the effect on hold timing after CTS.", ["spec/spec.yaml", "reports/cts_tool.json"],
                 "reports/cts_report.json", cts)

    def orion_report(ctx: StepContext) -> None:
        table = json.loads((ctx.workdir / "reports/pnr_iterations.json").read_text())
        _explain(ctx, "Orion", "Summarize place and route: the iteration table (what was tried and what changed), and "
                 "the final congestion/DRC/antenna/timing state from the reports.", ["spec/spec.yaml",
                 "reports/pnr_iterations.json", "reports/cts_report.json", "reports/floorplan_report.json"],
                 "reports/pnr_report.json", {"iterations": table})

    def mason(ctx: StepContext) -> None:
        s = ctx.session
        _tool_json(ctx, "Mason", "reports/division_cost.json", {"run_spend_by_agent_usd": _spend(s, [ctx.task.run_id])})
        data = llm.ask(ctx, "Mason", goal="Write the Division 3 (Zone 3) report to the human VP for this design: what "
                       "was delivered, what is at risk and why, quality (gate readiness), cost, and decisions needed.",
                       inputs=_inputs(ctx, ["reports/synth_report.json", "reports/floorplan_report.json",
                                            "reports/cts_report.json", "reports/pnr_report.json",
                                            "reports/division_cost.json", "dft/dft_plan.md"]),
                       exit_criteria=["one page", "every number from the reports"], schema=REPORT_ANSWER,
                       extra_note="Put the report in `report_markdown`. ")
        _answer_fields(ctx, "Mason", data)
        _write(ctx, "Mason", [{"path": "reports/division3_report.md", "content": data["report_markdown"]}], "report")

    def result(ctx: StepContext) -> None:
        _task_result(ctx, "place_route")

    return [pnr_loop, stop_if_blocked, tick, orion_report, mason, result]


# --- signoff (Chronos lead; Calla, Volta, Fabian) ---------------------------------------------------------------
def _final(ctx: StepContext) -> dict[str, Path]:
    ph = _phys(ctx)
    f = _pnr(ctx) / "runs" / ph["tag"] / "final"
    top = ph["top"]
    return {"gds": f / "gds" / f"{top}.gds", "nl": f / "nl" / f"{top}.nl.v", "pnl": f / "pnl" / f"{top}.pnl.v",
            "odb": f / "odb" / f"{top}.odb", "def": f / "def" / f"{top}.def", "metrics": f / "metrics.json",
            **{f"spef_{rc}": f / "spef" / rc / f"{top}.{rc}.spef" for rc in so.RC_CORNERS}}


def signoff_steps() -> list[Step]:
    def ol_signoff(ctx: StepContext) -> None:
        ph = _phys(ctx)
        ctx.emit("plan", "Sloane: plan - OpenLane signoff steps, then every check re-run independently on the final "
                 "streamed GDS: DRC Magic + KLayout, LVS Netgen, antenna, density (Calla); 9-corner STA (Chronos); "
                 "power/IR (Volta); DFM (Fabian); equivalence and gate-level simulation", agent_id="Sloane")
        for owner, goal in (("Chronos", "All-corner timing signoff"), ("Volta", "Power and IR"),
                            ("Calla", "DRC (Magic + KLayout), LVS, antenna, density on the final GDS"),
                            ("Fabian", "DFM scorecard")):
            _assign(ctx, "Sloane", owner, goal, ["every check passes in the Trust Layer"], "checks passed / checks")
        r = _run(ctx, "Calla", "openlane signoff (OpenROAD.IRDropReport .. end: stream-out, DRC, LVS, checkers)",
                 olf.run_stage, _pnr(ctx), ph["tag"], "signoff")
        m = r["metrics"]
        _result(ctx, "Calla", f"OpenLane signoff {'ok' if r['ok'] else 'FAILED'}: Magic DRC {m.get('magic__drc_error__count')}, "
                f"KLayout DRC {m.get('klayout__drc_error__count')}, LVS errors {m.get('design__lvs_error__count')}, "
                f"XOR differences {m.get('design__xor_difference__count')}")
        _check(ctx, "Calla", "openlane_signoff_steps", "openlane " + str(r["tool_version"]), r["ok"] and _final(ctx)["gds"].exists(),
               {"exit_code": r["exit_code"], "errors": r["errors"][:10], "failed_steps": r["failed_steps"],
                "magic_drc": m.get("magic__drc_error__count"), "klayout_drc": m.get("klayout__drc_error__count"),
                "lvs_errors": m.get("design__lvs_error__count"), "xor_differences": m.get("design__xor_difference__count"),
                "log": r["log"]}, r["command"])
        if not r["ok"] or not _final(ctx)["gds"].exists():
            ctx.state["blocked"] = f"OpenLane signoff steps failed: {r['errors'][:3] or r['failed_steps']}"

    def calla(ctx: StepContext) -> None:
        ph, F = _phys(ctx), _final(ctx)
        top, w = ph["top"], ctx.workdir
        mg = _run(ctx, "Calla", "magic DRC (sky130A full) on the final GDS", run_magic_drc, F["gds"], top, w)
        kl = _run(ctx, "Calla", "klayout DRC (sky130A_mr.drc) on the final GDS", run_klayout_drc, F["gds"], top, w)
        lv = _run(ctx, "Calla", "magic extraction + netgen LVS on the final GDS", so.lvs, F["gds"], F["pnl"], top, w)
        nets, ant = _run(ctx, "Calla", "openroad check_antennas -verbose (final ODB)", so.antenna, F["odb"], w)
        dn = _run(ctx, "Calla", "klayout PDK density deck (met_min_ca_density) on the final GDS", so.density, F["gds"], top, w)
        olm = json.loads(F["metrics"].read_text())
        md, kd = mg.metrics.get("drc_violations"), kl.metrics.get("drc_violations")
        _check(ctx, "Calla", "drc_magic_final_gds", f"magic {mg.tool_version}", mg.passed and md == 0,
               {"violations": md, "by_rule": mg.metrics.get("by_rule"), "reasons": mg.reasons[:3], "log": mg.log_path}, mg.command)
        _check(ctx, "Calla", "drc_klayout_final_gds", f"klayout {kl.tool_version}", kl.passed and kd == 0,
               {"violations": kd, "by_rule": kl.metrics.get("by_rule"), "reasons": kl.reasons[:3], "log": kl.log_path}, kl.command)
        agree = md == kd == olm.get("magic__drc_error__count") == olm.get("klayout__drc_error__count")
        _check(ctx, "Calla", "drc_tools_agree", "magic vs klayout vs openlane", agree,
               {"magic": md, "klayout": kd, "openlane_magic": olm.get("magic__drc_error__count"),
                "openlane_klayout": olm.get("klayout__drc_error__count")})
        _check(ctx, "Calla", "lvs_final_gds", f"netgen {lv.tool_version}", lv.passed and lv.metrics.get("lvs_status") == "match",
               {"verdict": lv.metrics.get("verdict"), "counts": lv.metrics.get("counts"), "unmatched": lv.metrics.get("unmatched"),
                "extracted_devices": lv.metrics["extraction"]["devices"], "log": lv.log_path}, lv.command)
        _check(ctx, "Calla", "antenna_final", f"openroad {ant['tool_version']}",
               ant["net_violations"] == 0 and ant["pin_violations"] == 0, {k: v for k, v in ant.items() if k != "worst"})
        _check(ctx, "Calla", "density_rules", f"klayout {dn.tool_version} (PDK met_min_ca_density.lydrc)",
               dn.passed and dn.metrics.get("drc_violations") == 0,
               {"violations": dn.metrics.get("drc_violations"), "clear_area_density": dn.metrics.get("clear_area_density"),
                "log": dn.log_path}, dn.command)
        tool = {"magic_drc": {"violations": md, "by_rule": mg.metrics.get("by_rule")},
                "klayout_drc": {"violations": kd, "by_rule": kl.metrics.get("by_rule")},
                "openlane": {"magic_drc": olm.get("magic__drc_error__count"), "klayout_drc": olm.get("klayout__drc_error__count"),
                             "lvs_errors": olm.get("design__lvs_error__count")},
                "lvs": {"verdict": lv.metrics.get("verdict"), "counts": lv.metrics.get("counts")},
                "antenna": {k: v for k, v in ant.items() if k != "log"}, "density": dn.metrics.get("clear_area_density"),
                "gds": str(F["gds"]), "gds_sha256": olf.sha(F["gds"])}
        _tool_json(ctx, "Calla", "reports/pv_tool.json", tool)
        _result(ctx, "Calla", f"final GDS: Magic DRC {md}, KLayout DRC {kd}, LVS {lv.metrics.get('verdict')}, antenna "
                f"{ant['net_violations']} net / {ant['pin_violations']} pin violations, density deck {dn.metrics.get('drc_violations')}")
        clean = md == 0 and kd == 0 and agree and lv.passed and ant["net_violations"] == 0 and dn.passed
        if clean:
            _tool_json(ctx, "Calla", "reports/pv_signoff.json", {**tool, "verdict": "clean on the final streamed GDS"})
        else:  # A.14 step 4: classify by rule, locate, send fix requests (a model call only when there is something to classify)
            _explain(ctx, "Calla", "Physical verification is not clean. Classify every violation or tool difference by "
                     "rule, locate it, and state the fix request for Orion or Grid with coordinates.",
                     ["reports/pv_tool.json"], "reports/pv_signoff.json", tool)
            ctx.emit("handoff", "Calla -> Orion: physical verification fix requests (see reports/pv_signoff.json)",
                     **_who("Calla"), to_agent_id="Orion", detail={"message": "fix request"})
            ctx.state["blocked"] = "physical verification is not clean on the final GDS"

    def chronos(ctx: StepContext) -> None:
        ph, F = _phys(ctx), _final(ctx)
        spef = {rc: F[f"spef_{rc}"] for rc in so.RC_CORNERS}
        res = _run(ctx, "Chronos", "opensta x9 corners (3 RC x 3 library) on the final netlist + SPEF", so.sta_corners,
                   F["nl"], ctx.workdir / "pnr/src/constraints.sdc", ph["top"], ctx.workdir, spef)
        olm = json.loads(F["metrics"].read_text())
        table, worst_paths, bad, mism = {}, {}, [], []
        nl_text = Path(F["nl"]).read_text(errors="replace")
        clk_lim = float(policy()["cts"]["clock_max_fanout"])
        for c, r in res.items():
            s_, h_ = r.metrics["setup_worst_slack"], r.metrics["hold_worst_slack"]
            keep, allowed = so.apply_clock_fanout_rule(r.metrics.get("drv_violator_pins") or [], nl_text, clk_lim)
            r.metrics["clock_rule_allowed"] = allowed
            if not r.passed and so.only_clock_rule_failures(r, keep, allowed):
                r.passed, r.reasons = True, []  # only clock-tree fanout within the clock rule
            table[c] = {"setup_ws_ns": s_, "setup_tns_ns": r.metrics["tns"], "hold_ws_ns": h_, "hold_tns_ns": r.metrics["hold_tns"],
                        "drv_violators": r.metrics["drv_violators"], "clock_rule_allowed": r.metrics["clock_rule_allowed"],
                        "passed": r.passed}
            worst_paths[c] = r.metrics["worst_paths"][:2]
            if not r.passed:
                bad.append(f"{c}: {r.reasons[:2]}")
            ol_s, ol_h = olm.get(f"timing__setup__ws__corner:{c}"), olm.get(f"timing__hold__ws__corner:{c}")
            if ol_s is None or s_ is None or abs(ol_s - s_) > 1e-3 or ol_h is None or h_ is None or abs(ol_h - h_) > 1e-3:
                mism.append(f"{c}: ours setup {s_}/hold {h_} vs OpenLane {ol_s}/{ol_h}")
        _check(ctx, "Chronos", "sta_all_corners", "opensta (9 corners, propagated clocks, SPEF)",
               len(res) == 9 and not bad, {"corners": table, "problems": bad})
        _check(ctx, "Chronos", "sta_matches_openlane", "opensta vs OpenLane STAPostPNR", not mism, {"mismatches": mism})
        _tool_json(ctx, "Chronos", "reports/sta_tool.json", {"corners": table, "worst_paths": worst_paths,
                                                              "clock_period_ns": ph["period_ns"]})
        ws = min(v["setup_ws_ns"] for v in table.values())
        wh = min(v["hold_ws_ns"] for v in table.values())
        _result(ctx, "Chronos", f"9 corners: worst setup slack {ws} ns, worst hold slack {wh} ns, "
                f"{len(bad)} corner(s) failing, {len(mism)} mismatch(es) with OpenLane")
        _explain(ctx, "Chronos", "Signoff timing report (A.12): per-corner setup/hold WNS/TNS and DRV violations, the "
                 "worst paths in plain words (start, end, dominant cells) and ranked fixes if any margin is thin.",
                 ["spec/spec.yaml", "constraints/constraints.sdc", "reports/sta_tool.json"], "reports/sta_signoff.json",
                 {"corners": table})
        if bad:
            ctx.state["blocked"] = f"timing not met at {len(bad)} corner(s)"

    def volta(ctx: StepContext) -> None:
        ph, F, pol = _phys(ctx), _final(ctx), policy()
        act = pol["power"]["default_toggle_rate"]
        pw = _run(ctx, "Volta", f"opensta report_power x3 corners (input activity {act})", so.power, F["nl"],
                  ctx.workdir / "pnr/src/constraints.sdc", ph["top"], ctx.workdir, F["spef_nom"], act)
        olm = json.loads(F["metrics"].read_text())
        supply = 1.8  # nominal SKY130 hd core supply at the typical corner (the tt_025C_1v80 corner name)
        drop = olm.get("ir__drop__worst")
        limit = supply * pol["ir"]["max_drop_pct_of_supply"] / 100
        _check(ctx, "Volta", "power_estimated", "opensta report_power", len(pw) == 3 and all(v["total_w"] > 0 for v in pw.values()),
               {"total_w_by_corner": {k: v["total_w"] for k, v in pw.items()}, "input_activity": act,
                "budget": "spec.yaml states no power budget: estimate reported, not compared"})
        _check(ctx, "Volta", "ir_drop_within_limit", "openroad psm (OpenROAD.IRDropReport)",
               drop is not None and drop <= limit,
               {"worst_drop_v": drop, "limit_v": round(limit, 4), "worst_voltage_v": olm.get("ir__voltage__worst"),
                "average_drop_v": olm.get("ir__drop__avg"),
                "assumption": "block-level analysis; no VSRC_LOC_FILES (no pad/bump locations), so the flow's default "
                              "voltage sources at the grid edges are assumed"})
        _tool_json(ctx, "Volta", "reports/power_tool.json", {
            "power_w_by_corner": pw, "input_activity": act, "openlane_power_total_w": olm.get("power__total"),
            "ir": {"worst_drop_v": drop, "avg_drop_v": olm.get("ir__drop__avg"), "limit_v": round(limit, 4),
                   "limit_rule": f"{pol['ir']['max_drop_pct_of_supply']}% of {supply} V (A.13 Phase 0 default)"}})
        _result(ctx, "Volta", f"power {pw['tt_025C_1v80']['total_w']:.3e} W (tt, activity {act}); worst IR drop {drop} V "
                f"(limit {limit:.3f} V)")
        tool = json.loads((ctx.workdir / "reports/power_tool.json").read_text())
        data = _explain(ctx, "Volta", "Power and IR report (A.13) with every assumption listed (activity, corners, "
                        "voltage source locations, what the open flow does not analyze, e.g. EM).",
                        ["spec/spec.yaml", "reports/power_tool.json"], "reports/power_report.json", tool)
        _write(ctx, "Volta", [{"path": "reports/ir_report.json", "content": json.dumps({
            **tool["ir"], "assumptions": data["assumptions"], "explained_by": "Volta"}, indent=2)}], "report")

    def fabian(ctx: StepContext) -> None:
        ph, F, pol = _phys(ctx), _final(ctx), policy()["dfm"]
        lay = _run(ctx, "Fabian", "klayout DFM script (A.15 checks 1-5) on the final GDS", dfm.run_dfm_layout,
                   F["gds"], ph["top"], ctx.workdir, pol)
        ant = dfm.parse_antenna_verbose((ctx.workdir / "signoff/antenna_verbose.rpt").read_text())
        items = dfm.items(lay, ant, pol)
        high = [i for i in items if i["severity"] == "high"]
        tool = {"items": items, "summary": {s: sum(1 for i in items if i["severity"] == s) for s in ("high", "medium", "low")},
                "antenna_worst_pct_of_limit": ant[0]["pct_of_limit"] if ant else None,
                "layers": {n: {k: v for k, v in L.items() if not isinstance(v, list)} for n, L in lay["layers"].items()},
                "vias": {n: {k: v for k, v in V.items() if not isinstance(v, list)} for n, V in lay["vias"].items()},
                "pdk_rules": lay["pdk_rules"], "policy": pol, "tool": lay["run"]}
        _tool_json(ctx, "Fabian", "reports/dfm_tool.json", tool)
        _result(ctx, "Fabian", f"DFM: {tool['summary']['high']} high, {tool['summary']['medium']} medium, "
                f"{tool['summary']['low']} low item(s); worst antenna net at {tool['antenna_worst_pct_of_limit']}% of limit")
        data = llm.ask(ctx, "Fabian", goal="Rank the DFM items by real yield impact and write the one-page DFM scorecard "
                       "for G3 (A.15). Severities are fixed by the tool rules: you may not change them.",
                       inputs=_inputs(ctx, ["reports/dfm_tool.json"]),
                       exit_criteria=["every item ranked", "one page", "no low-value alarms promoted"],
                       schema=FABIAN_ANSWER, extra_note="Rank every item id in `ranked`; the scorecard goes in "
                       "`scorecard_markdown`. ")
        _answer_fields(ctx, "Fabian", data)
        ids = {i["id"] for i in items}
        ranked_ids = [r["id"] for r in data["ranked"]]
        missing = sorted(ids - set(ranked_ids))
        by_id = {r["id"]: r for r in data["ranked"]}
        card = [{**i, "rank": by_id.get(i["id"], {}).get("rank"), "why_it_matters": by_id.get(i["id"], {}).get(
            "why_it_matters", i["why"]), "owner": by_id.get(i["id"], {}).get("owner", i["owner"])} for i in items]
        _write(ctx, "Fabian", [{"path": "reports/dfm_scorecard.json", "content": json.dumps(
            {"summary": tool["summary"], "items": sorted(card, key=lambda c: (c["rank"] or 999)),
             "unranked": missing}, indent=2)},
            {"path": "reports/dfm_scorecard.md", "content": data["scorecard_markdown"]}], "report")
        _check(ctx, "Fabian", "dfm_no_high_severity", "klayout DFM script + openroad antenna (rule-based severity)",
               not high, {"high": [i["title"] for i in high], "summary": tool["summary"], "unranked_by_fabian": missing})

    def equivalence_gls(ctx: StepContext) -> None:
        ph, F = _phys(ctx), _final(ctx)
        rtl = sorted((ctx.workdir / "rtl").glob("*.v"))
        eq = _run(ctx, "Sienna", "eqy RTL vs final routed netlist", so.equivalence, rtl, F["nl"], ph["top"], ctx.workdir, "final")
        _check(ctx, "Sienna", "eqy_rtl_vs_final", f"eqy {eq.tool_version}", eq.passed,
               {"status": eq.metrics["status"], "method": eq.metrics.get("method"),
                "proven": len(eq.metrics["partitions_proven"]), "failed": eq.metrics["partitions_failed"],
                "lec_points_proven": eq.metrics.get("lec_points_proven"),
                "lec_points_unproven": eq.metrics.get("lec_points_unproven"), "log": eq.log_path,
                "lec_log": eq.metrics.get("lec_log")}, eq.command)
        mods = sorted(p.stem for p in (ctx.workdir / "tb").glob("test_*.py"))
        tb = ctx.workdir / "signoff" / "gls_tb"
        shutil.copytree(ctx.workdir / "tb", tb, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        g = _run(ctx, "Rex", "gate-level simulation: verification testbench on the final netlist (icarus + PDK cells)",
                 so.gls, F["nl"], ph["top"], tb, ",".join(mods), ctx.workdir, [1])
        _check(ctx, "Rex", "gls_final_netlist", f"cocotb {g.tool_version} + icarus", g.passed and g.metrics.get("test_runs", 0) > 0,
               {"tests": g.metrics.get("tests"), "test_runs": g.metrics.get("test_runs"), "failed": g.metrics.get("failed_runs"),
                "reasons": g.reasons[:3], "log": g.log_path}, g.command)
        _result(ctx, "Rex", f"gate-level simulation: {g.metrics.get('test_runs', 0) - g.metrics.get('failed_runs', 0)}/"
                f"{g.metrics.get('test_runs', 0)} test runs passed; eqy RTL vs final netlist {eq.metrics['status']}")
        if not (eq.passed and g.passed):
            ctx.state["blocked"] = "final netlist not proven equivalent or gate-level simulation failing"

    def result(ctx: StepContext) -> None:
        _task_result(ctx, "signoff")

    return [ol_signoff, stop_if_blocked, calla, chronos, volta, fabian, equivalence_gls, stop_if_blocked, result]


# --- gdsii (Gideon lead; Proof independent; Sloane reports) -----------------------------------------------------
CHECKLIST = [  # Appendix B.9
    (1, "Spec approved at G1", "gate record"), (2, "RTL frozen at G2; no changes since", "hash comparison"),
    (3, "Regression 100% passing on frozen RTL", "packet stage 4"), (4, "Equivalence RTL vs final netlist proven", "eqy report"),
    (5, "Setup and hold met at all corners", "STA reports"), (6, "Zero DRC (Magic and KLayout) on final GDS", "DRC reports"),
    (7, "LVS clean on final GDS", "Netgen report"), (8, "Antenna clean", "report"), (9, "Density rules met", "report"),
    (10, "DFM scorecard: zero high-severity open items", "Fabian report"), (11, "Power and IR within limits", "Volta reports"),
    (12, "Pin list matches spec", "comparison report"), (13, "All Sentinel findings closed or human-overruled", "findings list"),
    (14, "reproduce.sh re-runs cleanly in a fresh container", "CI log"), (15, "versions.lock and hashes recorded", "manifest"),
    (16, "G3 approved", "gate record"),
]


def _pkg(ctx: StepContext) -> Path:
    return ctx.workdir / "tapeout"


def gdsii_steps() -> list[Step]:
    def package(ctx: StepContext) -> None:
        ph, F, P = _phys(ctx), _final(ctx), _pkg(ctx)
        top = ph["top"]
        shutil.rmtree(P, ignore_errors=True)
        ctx.emit("plan", "Gideon: plan - assemble the package, read the GDS back, re-run DRC/LVS on the packaged GDS, "
                 "B.9 checklist with evidence, hashes; Proof re-runs reproduce.sh in a clean container", **_who("Gideon"))
        _assign(ctx, "Sloane", "Gideon", "Tape-out package and checklist", ["checklist 100% with evidence"], "items done / 16")
        _assign(ctx, "Sloane", "Proof", "Independent re-execution and signed manifest", ["reproduce.sh clean"], "items")
        pk.copy(F["gds"], P / "gds" / f"{top}.gds")
        pk.copy(F["nl"], P / "netlist" / f"{top}.nl.v")
        pk.copy(F["pnl"], P / "netlist" / f"{top}.pnl.v")
        for rc in so.RC_CORNERS:
            pk.copy(F[f"spef_{rc}"], P / "spef" / rc / f"{top}.{rc}.spef")
        pk.copy(ctx.workdir / "pnr/src/constraints.sdc", P / "constraints" / "constraints.sdc")
        pk.copy(ctx.workdir / "pnr/config.json", P / "flow" / "config.json")
        pk.copy(ctx.workdir / "pnr/src", P / "flow" / "src")
        pk.copy(ctx.workdir / "rtl", P / "rtl")
        for f in sorted((ctx.workdir / "reports").glob("*")):
            if f.is_file() and f.suffix in (".json", ".md"):
                pk.copy(f, P / "reports" / f.name)
        pk.copy(ctx.workdir / "dft/dft_plan.md", P / "reports" / "dft_plan.md")
        pk.copy(REPO_ROOT / "eda" / "versions.lock", P / "versions.lock")
        sta = json.loads((ctx.workdir / "reports/sta_tool.json").read_text())["corners"]
        olm = json.loads(F["metrics"].read_text())
        (P / "expected.json").write_text(json.dumps({
            "sta": {c: {"setup": round(v["setup_ws_ns"], 4), "hold": round(v["hold_ws_ns"], 4)} for c, v in sta.items()},
            "flow_metrics": {k: olm.get(k) for k in ("design__instance__count", "route__wirelength")},
            "gds_sha256": olf.sha(F["gds"])}, indent=2) + "\n")
        s = ctx.session
        lineage = ph["lineage"] + [ctx.task.run_id]
        ev = []
        for c, st, rid in s.execute(select(Check, Task.stage, Task.run_id).join(Task, Task.id == Check.task_id)
                                    .where(Task.run_id.in_(lineage)).order_by(Check.id)):
            ev.append({"run": rid, "stage": st, "check": c.check_name, "passed": c.passed, "tool": c.tool,
                       "command": c.command, "id": c.id})
        (P / "evidence").mkdir(parents=True, exist_ok=True)
        (P / "evidence" / "index.json").write_text(json.dumps(ev, indent=1) + "\n")
        (P / "reproduce.sh").write_text(pk.reproduce_script(top))
        man = pk.write_manifest(P)
        _result(ctx, "Gideon", f"package assembled: {sum(1 for _ in P.rglob('*') if _.is_file())} files, manifest "
                f"{pk.sha256(man)[:16]}")

    def gideon_verify(ctx: StepContext) -> None:
        ph, P = _phys(ctx), _pkg(ctx)
        top, gds = ph["top"], _pkg(ctx) / "gds" / f"{ph['top']}.gds"
        rb = _run(ctx, "Gideon", "klayout read-back of the packaged GDS", so.gds_readback, gds, top, ctx.workdir, "readback_pkg")
        _check(ctx, "Gideon", "gds_readback", "klayout", rb["top_cells"] == [top] and len(rb["layers"]) > 0,
               {"top_cells": rb["top_cells"], "layers": len(rb["layers"]), "bbox_um": rb["bbox_um"]}, rb["command"])
        mg = _run(ctx, "Gideon", "magic DRC on the packaged GDS", run_magic_drc, gds, top, ctx.workdir)
        kl = _run(ctx, "Gideon", "klayout DRC on the packaged GDS", run_klayout_drc, gds, top, ctx.workdir,
                  name="klayout_drc_pkg")
        lv = _run(ctx, "Gideon", "extraction + netgen LVS on the packaged GDS", so.lvs, gds, P / "netlist" / f"{top}.pnl.v",
                  top, ctx.workdir, "ext_pkg")
        _check(ctx, "Gideon", "package_drc_magic", f"magic {mg.tool_version}", mg.passed and mg.metrics.get("drc_violations") == 0,
               {"violations": mg.metrics.get("drc_violations")}, mg.command)
        _check(ctx, "Gideon", "package_drc_klayout", f"klayout {kl.tool_version}",
               kl.passed and kl.metrics.get("drc_violations") == 0, {"violations": kl.metrics.get("drc_violations")}, kl.command)
        _check(ctx, "Gideon", "package_lvs", f"netgen {lv.tool_version}", lv.passed and lv.metrics.get("lvs_status") == "match",
               {"verdict": lv.metrics.get("verdict")}, lv.command)
        bits, _, _ = olf.port_bits(_spec(ctx))
        pins = {p["name"] for p in olf.def_pins(_final(ctx)["def"].read_text())}
        labels = set(rb["labels"])
        _check(ctx, "Gideon", "pins_match_spec", "spec.yaml vs final DEF pins vs GDS labels",
               pins == set(bits) and set(bits) <= labels,
               {"spec_pins": len(bits), "def_pins": len(pins), "missing_in_def": sorted(set(bits) - pins),
                "extra_in_def": sorted(pins - set(bits)), "missing_gds_labels": sorted(set(bits) - labels)})
        _result(ctx, "Gideon", f"packaged GDS: top {rb['top_cells']}, Magic DRC {mg.metrics.get('drc_violations')}, KLayout DRC "
                f"{kl.metrics.get('drc_violations')}, LVS {lv.metrics.get('verdict')}")

    def proof(ctx: StepContext) -> None:
        """Independent of engineering: re-run from the package alone, in a fresh container, and the diff guards."""
        ph, P = _phys(ctx), _pkg(ctx)
        clean = ctx.workdir / "proof_clean"
        shutil.rmtree(clean, ignore_errors=True)
        shutil.copytree(P, clean / "pkg")
        from s2s.tools import runner
        rec = _run(ctx, "Proof", "reproduce.sh in a fresh s2s-eda container (package only, no network)", runner.run,
                   ["bash", "reproduce.sh"], clean / "pkg", clean / "reproduce.log", "openlane", 7200, None, None)
        log = Path(rec.log_path).read_text(errors="replace")
        line = next((ln for ln in log.splitlines() if ln.startswith("S2S_REPRODUCE_RESULT ")), None)
        res = json.loads(line[len("S2S_REPRODUCE_RESULT "):]) if line else {"passed": False, "items": {}, "error": "no result line"}
        _check(ctx, "Proof", "reproduce_clean_container", "reproduce.sh (s2s-eda, --network none)",
               rec.exit_code == 0 and res.get("passed") is True,
               {"exit_code": rec.exit_code, "items": res.get("items"), "flow_metrics": res.get("flow_metrics"),
                "log": str(rec.log_path), "duration_s": rec.duration_s}, "bash reproduce.sh")
        (ctx.workdir / "reports").mkdir(exist_ok=True)
        _tool_json(ctx, "Proof", "reports/proof_reproduce.json", res)
        guard = olf.config_guard(_pnr(ctx), period_ns=ph["period_ns"], reviewed_sdc_sha=ph["reviewed_sdc_sha"],
                                 frozen_rtl=ph["frozen_rtl"])
        _check(ctx, "Proof", "constraints_not_loosened", "s2s.physical.flow.config_guard", not guard, {"problems": guard})
        waivers = sorted(str(p.relative_to(ctx.workdir)) for p in ctx.workdir.rglob("*waive*") if "proof_clean" not in str(p))
        _check(ctx, "Proof", "no_waivers", "file scan", not waivers, {"waiver_files": waivers})
        s = ctx.session
        v = _latest_checks(s, ph["lineage"], "verification")
        _check(ctx, "Proof", "tests_not_weakened", "M0.6 anti-cheating guard record", v.get("anti_cheat_final") is True,
               {"anti_cheat_final": v.get("anti_cheat_final")})
        _result(ctx, "Proof", f"reproduce.sh in a clean container: {'PASS' if res.get('passed') else 'FAIL'} "
                f"{res.get('items')}; guards: constraints {'ok' if not guard else guard}, waivers {len(waivers)}")

    def checklist(ctx: StepContext) -> None:
        ph, s = _phys(ctx), ctx.session
        here = _latest_checks(s, [ctx.task.run_id])
        src = _latest_checks(s, ph["lineage"])
        g1 = s.scalars(select(Gate).where(Gate.run_id.in_(ph["lineage"]), Gate.gate == "G1", Gate.status == "approved")).first()
        g3 = s.scalars(select(Gate).where(Gate.run_id == ctx.task.run_id, Gate.gate == "G3")).first()
        # every Sentinel review in the lineage (latest record per task and review) must have passed
        sent = {}
        for c, tid in s.execute(select(Check, Task.id).join(Task, Task.id == Check.task_id).where(
                Task.run_id.in_(ph["lineage"] + [ctx.task.run_id]), Check.check_name.like("sentinel_%")).order_by(Check.id)):
            sent[(tid, c.check_name)] = c.passed
        open_sentinel = sorted(f"{name} (task {tid})" for (tid, name), ok in sent.items() if not ok)
        status = {
            1: (g1 is not None, f"gate {g1.id if g1 else None}"),
            2: (here.get("rtl_frozen_at_g2", False) and here.get("constraints_not_loosened", False), "checks rtl_frozen_at_g2, constraints_not_loosened"),
            3: (src.get("regression_100pct", False), "M0.6 check regression_100pct"),
            4: (here.get("eqy_rtl_vs_final", False), "check eqy_rtl_vs_final"),
            5: (here.get("sta_all_corners", False), "check sta_all_corners (9 corners)"),
            6: (all(here.get(k, False) for k in ("drc_magic_final_gds", "drc_klayout_final_gds", "package_drc_magic", "package_drc_klayout")),
                "checks drc_magic_final_gds, drc_klayout_final_gds, package_drc_*"),
            7: (here.get("lvs_final_gds", False) and here.get("package_lvs", False), "checks lvs_final_gds, package_lvs"),
            8: (here.get("antenna_final", False), "check antenna_final"),
            9: (here.get("density_rules", False), "check density_rules"),
            10: (here.get("dfm_no_high_severity", False), "check dfm_no_high_severity"),
            11: (here.get("power_estimated", False) and here.get("ir_drop_within_limit", False), "checks power_estimated, ir_drop_within_limit"),
            12: (here.get("pins_match_spec", False), "check pins_match_spec"),
            13: (not open_sentinel, "open: " + ", ".join(open_sentinel) if open_sentinel else "all Sentinel reviews passed"),
            14: (here.get("reproduce_clean_container", False), "check reproduce_clean_container"),
            15: ((_pkg(ctx) / "versions.lock").exists() and (_pkg(ctx) / "MANIFEST.sha256").exists(), "tapeout/versions.lock, MANIFEST.sha256"),
            16: (g3 is not None and g3.status == "approved", f"gate {g3.id if g3 else None} ({g3.status if g3 else 'none'})"),
        }
        items = [{"n": n, "item": item, "evidence_kind": kind, "done": status[n][0], "evidence": status[n][1]}
                 for n, item, kind in CHECKLIST]
        _tool_json(ctx, "Gideon", "reports/tapeout_checklist.json", items)
        md = ["| # | Item | Done | Evidence |", "|---|---|---|---|"] + [
            f"| {i['n']} | {i['item']} | {'yes' if i['done'] else 'NO'} | {i['evidence']} |" for i in items]
        (ctx.workdir / "reports/tapeout_checklist.md").write_text("\n".join(md) + "\n")
        undone = [i["n"] for i in items if not i["done"]]
        _check(ctx, "Gideon", "tapeout_checklist_complete", "Appendix B.9", not undone,
               {"done": len(items) - len(undone), "of": len(items), "open_items": undone,
                "open_sentinel": open_sentinel})

        # Part 22: readiness from the checks that actually ran
        def res(ok: bool, partial_ok: bool = False):
            return "clean" if ok else ("partial" if partial_ok else "failed")
        rtl_sim, gls_ok = src.get("regression_100pct", False), here.get("gls_final_netlist", False)
        formal, eqy_ok = src.get("formal_3_meaningful", False) and src.get("formal_vacuity", False), here.get("eqy_rtl_vs_final", False)
        cov = all(src.get(k, False) for k in ("coverage_line", "coverage_toggle", "coverage_functional"))
        r = {
            "functional_sim": {"result": res(rtl_sim and gls_ok, rtl_sim or gls_ok), "tool": "cocotb/Verilator/Icarus",
                               "evidence": "regression_100pct (M0.6), gls_final_netlist"},
            "coverage": {"result": res(cov), "tool": "Verilator coverage + waveform bins", "evidence": "coverage_* (M0.6)"},
            "formal_equiv": {"result": res(formal and eqy_ok, formal or eqy_ok), "tool": "SymbiYosys, eqy",
                             "evidence": "formal_3_meaningful, formal_vacuity (M0.6), eqy_rtl_vs_final"},
            "drc": {"result": res(status[6][0]), "tool": "Magic + KLayout (SKY130 decks)", "evidence": status[6][1]},
            "lvs": {"result": res(status[7][0]), "tool": "Magic extraction + Netgen", "evidence": status[7][1]},
            "antenna": {"result": res(status[8][0]), "tool": "OpenROAD check_antennas", "evidence": status[8][1]},
            "density": {"result": res(status[9][0]), "tool": "KLayout PDK density deck", "evidence": status[9][1]},
            "sta_setup_hold": {"result": res(status[5][0]), "tool": "OpenSTA (9 corners)", "evidence": status[5][1]},
            "power": {"result": res(here.get("power_estimated", False)), "tool": "OpenSTA report_power",
                      "evidence": "power_estimated", "note": "20% input activity; no power budget in spec"},
            "ir_em_static": {"result": res(here.get("ir_drop_within_limit", False)), "tool": "OpenROAD PSM",
                             "evidence": "ir_drop_within_limit", "note": "static IR only; EM not analyzed"},
            # a plan is not a measurement: no fault_coverage_pct, so readiness scores DFT as deferred (0)
            "dft_atpg": {"result": "not run", "tool": "plan only (dft_plan.md)",
                         "evidence": "dft_plan_complete" if _latest_checks(s, [ctx.task.run_id], "dft").get("dft_plan_complete")
                         else "", "note": "plan only in Phase 0"},
            "signal_integrity": {"result": "not run", "tool": "-", "evidence": "", "note": "out of open-flow scope"},
            "reliability": {"result": "not run", "tool": "-", "evidence": "", "note": "out of open-flow scope"},
            "foundry_signoff": {"result": "not run", "tool": "-", "evidence": "", "note": "no foundry-certified decks"},
            "gds_integrity_repro": {"result": res(here.get("gds_readback", False) and here.get("reproduce_clean_container", False)),
                                    "tool": "KLayout read-back + reproduce.sh", "evidence": "gds_readback, reproduce_clean_container"},
        }
        # the Phase 0 gate: hard checks pass/fail (the percentages are derived)
        hard = readiness.hard_checks({"drc": status[6][0], "lvs": status[7][0], "antenna": status[8][0],
                                      "timing": status[5][0], "equivalence": status[4][0]},
                                     {"drc": status[6][1], "lvs": status[7][1], "antenna": status[8][1],
                                      "timing": status[5][1], "equivalence": status[4][1]}, ctx.workdir / "reports")
        rep = readiness.score(r, hard)
        _tool_json(ctx, "Gideon", "reports/tapeout_readiness.json", rep)
        (ctx.workdir / "reports/tapeout_readiness.md").write_text(readiness.markdown(_spec(ctx)["design"], rep, {
            "evidence packet": "tapeout/evidence/index.json", "reproduce": "tapeout/reproduce.sh",
            "checklist": "tapeout/reports/tapeout_checklist.md", "manifest": "tapeout/MANIFEST.sha256"}))
        _result(ctx, "Gideon", f"B.9 checklist {len(items) - len(undone)}/16; hard checks: {hard['verdict']} "
                f"({hard['passed']}/{hard['of']}); derived readiness (dft={rep['partial_credit']['dft']:g}, "
                f"ir_em={rep['partial_credit']['ir_em']:g}): Baseline A {rep['baseline_A_pct']}%, "
                f"Baseline B {rep['baseline_B_pct']}%")

    def release_notes(ctx: StepContext) -> None:
        data = llm.ask(ctx, "Gideon", goal="Write tapeout/release_notes.md: what this package is, its signoff status "
                       "with the checklist, the hard checks (pass/fail, with any condition stated prominently) as the "
                       "headline, the Phase 0 gate status (tapeout_readiness.json phase0_gate), the readiness "
                       "percentages only as derived figures with their arithmetic, baselines and partial-credit values, "
                       "the scope labels (DFT deferred: not measured, 0 fault coverage; static IR measured and passed, "
                       "EM not analysed), known limits and open items.",
                       inputs=_inputs(ctx, ["spec/spec.yaml", "reports/tapeout_checklist.json",
                                            "reports/tapeout_readiness.json", "reports/dfm_scorecard.json"]),
                       exit_criteria=["no claim beyond the checklist and readiness data", "both baselines shown",
                                      "hard checks lead; no percentage is presented as the pass criterion",
                                      "every percentage is copied from the input reports; none is estimated"],
                       schema=REPORT_ANSWER, extra_note="Put the release notes in `report_markdown`. ")
        _answer_fields(ctx, "Gideon", data)
        _write(ctx, "Gideon", [{"path": "tapeout/release_notes.md", "content": data["report_markdown"]}], "release_notes")

    def sign(ctx: StepContext) -> None:
        """Final package: reports and notes in, manifest rewritten, Proof re-hashes every file and signs."""
        P = _pkg(ctx)
        for f in ("tapeout_checklist.json", "tapeout_checklist.md", "tapeout_readiness.json", "tapeout_readiness.md",
                  "proof_reproduce.json", "dfm_scorecard.json", "dfm_scorecard.md"):
            if (ctx.workdir / "reports" / f).exists():
                pk.copy(ctx.workdir / "reports" / f, P / "reports" / f)
        man = pk.write_manifest(P)
        bad = []
        for line in man.read_text().splitlines():
            h, rel = line.split("  ", 1)
            if pk.sha256(P / rel) != h:
                bad.append(rel)
        signed = {"manifest_sha256": pk.sha256(man), "files": len(man.read_text().splitlines()), "signed_by": "Proof",
                  "at": dt.datetime.now(dt.timezone.utc).isoformat(), "mismatches": bad}
        _tool_json(ctx, "Proof", "reports/proof_manifest.json", signed)
        _check(ctx, "Proof", "manifest_signed", "sha256 over every package file", not bad and signed["files"] > 0, signed)

    def sloane(ctx: StepContext) -> None:
        s = ctx.session
        _tool_json(ctx, "Sloane", "reports/division_cost.json", {"run_spend_by_agent_usd": _spend(s, [ctx.task.run_id])})
        data = llm.ask(ctx, "Sloane", goal="Write the Division 4 (Zone 4) report to the human VP for this design: signoff "
                       "results led by the hard checks (pass/fail, with any condition stated prominently), the Phase 0 "
                       "gate status (tapeout_readiness.json phase0_gate), tape-out package status, the readiness "
                       "percentages only as derived figures with their partial-credit values and scope labels (DFT "
                       "deferred: not measured, 0 fault coverage; static IR measured and passed, EM not analysed), "
                       "risks, cost, and decisions needed (G4 is a human decision for real silicon).",
                       inputs=_inputs(ctx, ["reports/sta_signoff.json", "reports/power_report.json", "reports/ir_report.json",
                                            "reports/pv_signoff.json", "reports/dfm_scorecard.json",
                                            "reports/tapeout_checklist.json", "reports/tapeout_readiness.json",
                                            "reports/division_cost.json"]),
                       exit_criteria=["one page", "every number from the reports",
                                      "no percentage is presented as the pass criterion"], schema=REPORT_ANSWER,
                       extra_note="Put the report in `report_markdown`. ")
        _answer_fields(ctx, "Sloane", data)
        _write(ctx, "Sloane", [{"path": "reports/division4_report.md", "content": data["report_markdown"]}], "report")

    def result(ctx: StepContext) -> None:
        _task_result(ctx, "gdsii")

    return [package, gideon_verify, proof, checklist, release_notes, sign, sloane, result]


DesignAgent.STAGES.update({"synthesis": synthesis_steps, "dft": dft_steps, "floorplan": floorplan_steps,
                           "place_route": place_route_steps, "signoff": signoff_steps, "gdsii": gdsii_steps})
