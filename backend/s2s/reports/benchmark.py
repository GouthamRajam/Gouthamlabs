"""Benchmark report (MASTER_SPEC M0.8 acceptance 2): per design pass/fail per stage, iterations, wall
time, tokens used, cost, and PPA vs the default flow.

Every number comes from the database (tasks, checks, usage records, events) or from a tool report in
the run folder (<S2S_ARTIFACT_DIR>/runs/<run_id>/reports/). Nothing is estimated here: a value that is
not recorded is None, with the reason next to it, and renders as "–" with that reason.

The "default flow" PPA is P&R iteration 1 of pnr_iterations.json, which runs with the
config/pnr_ranges.yaml defaults; S2S's result is the final iteration. Signoff STA, power, DFM and
readiness run only on the final layout, so they have no default-flow value.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from s2s.db.models import Check, Design, Event, Run, Task, UsageRecord
from s2s.orchestrator.flow import STAGE_NAMES

SKIP = ("*_suite", "*_seeded_flaw")  # test fixtures, not benchmark designs (include_all=True keeps them)
BRIDGE_MODEL = "claude-code-bridge"  # $0, ESTIMATED tokens (~4 chars/token): see models/gateway.py
REGRESSION = re.compile(r"^Rex: regression (\S+)_r(\d+): ")  # M0.6 debug round <k> of a regression label
TT_CORNER = "tt_025C_1v80"
PHYSICAL = ("synthesis", "dft", "floorplan", "place_route", "signoff", "gdsii")


def _seconds(a: dt.datetime | None, b: dt.datetime | None) -> float | None:
    return (b - a).total_seconds() if a and b else None


def _union_seconds(spans: list[tuple[dt.datetime, dt.datetime]]) -> float:
    """Wall time covered by the intervals (rtl and test_build overlap, so a plain sum overcounts)."""
    total, cur = 0.0, None
    for a, b in sorted(spans):
        if cur and a <= cur[1]:
            cur = (cur[0], max(cur[1], b))
            continue
        if cur:
            total += (cur[1] - cur[0]).total_seconds()
        cur = (a, b)
    if cur:
        total += (cur[1] - cur[0]).total_seconds()
    return total


def _json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _worst(by_corner: dict | None, key: str | None = None) -> float | None:
    vals = [(v.get(key) if key else v) for v in (by_corner or {}).values()]
    vals = [v for v in vals if isinstance(v, (int, float))]
    return min(vals) if vals else None


def _usage(recs: list[UsageRecord]) -> dict:
    llm = [u for u in recs if u.source == "llm"]
    by_model: dict[str, dict] = {}
    for u in llm:
        m = by_model.setdefault(u.model or "(unknown)", {"records": 0, "tokens": 0, "cost_usd": Decimal(0),
                                                         "estimated_tokens": (u.model == BRIDGE_MODEL)})
        m["records"] += 1
        m["tokens"] += int(u.quantity)
        m["cost_usd"] += Decimal(u.cost_usd)
    for m in by_model.values():
        m["cost_usd"] = float(m["cost_usd"])
    llm_cost = sum((Decimal(u.cost_usd) for u in llm), Decimal(0))
    compute_cost = sum((Decimal(u.cost_usd) for u in recs if u.source != "llm"), Decimal(0))
    return {"tokens": int(sum(u.quantity for u in llm)), "llm_calls": len(llm), "llm_cost_usd": float(llm_cost),
            "other_cost_usd": float(compute_cost), "cost_usd": float(llm_cost + compute_cost), "by_model": by_model}


def _physical(runs: list[Run], art: Path) -> tuple[dict | None, str | None]:
    """PPA, readiness and DFM from the latest run of the design whose folder has M0.7 reports."""
    if not any(set(r.stages or []) & set(PHYSICAL) for r in runs):
        return None, "M0.7 not run"
    for r in sorted(runs, key=lambda r: r.started_at, reverse=True):
        rep = art / "runs" / r.id / "reports"
        if any((rep / f).exists() for f in ("synth_tool.json", "pnr_iterations.json")):
            break
    else:
        return None, "M0.7 run has no reports yet"
    synth = _json(rep / "synth_tool.json")
    iters = _json(rep / "pnr_iterations.json")
    sta = _json(rep / "sta_tool.json")
    power = _json(rep / "power_tool.json")
    ready = _json(rep / "tapeout_readiness.json")
    dfm = _json(rep / "dfm_tool.json") or _json(rep / "dfm_scorecard.json")
    rows: list[dict] = []

    def row(metric: str, unit: str, default, final, source: str, default_why: str | None = None,
            final_why: str | None = None) -> None:
        rows.append({"metric": metric, "unit": unit, "default": default, "final": final, "source": source,
                     "default_why": default_why if default is None else None,
                     "final_why": final_why if final is None else None})

    no_synth = "synthesis not reported (synth_tool.json missing)"
    for metric, key, unit in (("Cells (synthesis; P&R iterations reuse this netlist)", "cells", "cells"),
                              ("Area (synthesis; P&R iterations reuse this netlist)", "area_um2", "um^2")):
        v = (synth or {}).get(key)
        row(metric, unit, v, v, "synth_tool.json", no_synth, no_synth)

    n_iter = len(iters) if isinstance(iters, list) else None
    first, last = (iters[0], iters[-1]) if n_iter else (None, None)
    if not n_iter:
        d_why = f_why = "P&R not reported (pnr_iterations.json missing)"
    elif n_iter == 1:
        d_why = ("no change from defaults (first iteration clean)" if not first.get("problems")
                 else "only one P&R iteration (stopped before a second)")
        f_why = "P&R iteration did not report this"
    else:
        d_why = f_why = "P&R iteration did not report this"
    ff = (last or {}).get("facts") or {}
    df = (first.get("facts") or {}) if n_iter and n_iter > 1 else {}
    for metric, unit, fn in (
            ("Worst setup slack, post-route (P&R)", "ns", lambda f: _worst(f.get("setup_ws_by_corner"))),
            ("Worst hold slack, post-route (P&R)", "ns", lambda f: _worst(f.get("hold_ws_by_corner"))),
            ("Utilization", "fraction", lambda f: f.get("utilization")),
            ("Wirelength", "um", lambda f: f.get("wirelength_um"))):
        row(metric, unit, fn(df) if df else None, fn(ff) if ff else None, "pnr_iterations.json", d_why, f_why)
    if n_iter:
        row("P&R problems", "count", len(first.get("problems") or []) if n_iter > 1 else None,
            len(last.get("problems") or []), "pnr_iterations.json", d_why)
    final_only = "runs only on the final layout (no default-flow value)"
    corners = (sta or {}).get("corners") or {}
    n_c = f" ({len(corners)} corners)" if corners else ""
    sta_why = "signoff STA not reported (sta_tool.json missing)" if sta is None else None
    row(f"Worst setup slack, signoff STA{n_c}", "ns", None, _worst(corners, "setup_ws_ns"),
        "sta_tool.json", final_only, sta_why or "no setup slack in sta_tool.json")
    row(f"Worst hold slack, signoff STA{n_c}", "ns", None, _worst(corners, "hold_ws_ns"),
        "sta_tool.json", final_only, sta_why or "no hold slack in sta_tool.json")
    tt = ((power or {}).get("power_w_by_corner") or {}).get(TT_CORNER) or {}
    row(f"Power ({TT_CORNER})", "W", None, tt.get("total_w"), "power_tool.json", final_only,
        "power not reported (power_tool.json missing)" if power is None else f"no {TT_CORNER} total in power_tool.json")
    return {
        "run_id": r.id, "reports_dir": str(rep), "pnr_iterations": n_iter,
        "params_default": (first or {}).get("params"), "params_final": (last or {}).get("params"),
        "ppa": rows,
        "readiness": {"baseline_A_pct": ready.get("baseline_A_pct"), "baseline_B_pct": ready.get("baseline_B_pct")}
        if ready else None,
        "readiness_why": None if ready else "tapeout_readiness.json missing (gdsii stage not reached)",
        "dfm_summary": (dfm or {}).get("summary"),
        "dfm_why": None if dfm else "dfm_tool.json missing (signoff DFM not reached)",
    }, None


def _design(s: Session, d: Design, art: Path) -> dict:
    runs = s.scalars(select(Run).where(Run.design_id == d.id).order_by(Run.started_at)).all()
    run_ids = [r.id for r in runs]
    tasks = s.scalars(select(Task).where(Task.run_id.in_(run_ids)).order_by(Task.id)).all()
    by_task = {t.id: t for t in tasks}
    checks = s.scalars(select(Check).where(Check.task_id.in_(list(by_task))).order_by(Check.id)).all()
    recs = s.scalars(select(UsageRecord).where(UsageRecord.run_id.in_(run_ids)).order_by(UsageRecord.id)).all()
    debug: dict[str, int] = {}
    for summary in s.scalars(select(Event.summary).where(Event.run_id.in_(run_ids),
                                                         Event.summary.like("Rex: regression %"))):
        m = REGRESSION.match(summary)
        if m:
            debug[m.group(1)] = max(debug.get(m.group(1), 0), int(m.group(2)))
    phys, phys_why = _physical(list(runs), art)

    stage_tasks: dict[str, list[Task]] = defaultdict(list)
    for t in tasks:
        stage_tasks[t.stage].append(t)
    stage_checks: dict[str, dict[str, Check]] = defaultdict(dict)
    for c in checks:  # ids are time-sortable: the last record per check name wins
        stage_checks[by_task[c.task_id].stage][c.check_name] = c
    stage_usage: dict[str, list[UsageRecord]] = defaultdict(list)
    for u in recs:
        stage_usage[by_task[u.task_id].stage if u.task_id in by_task else "(no task)"].append(u)

    stages = {}
    for name in STAGE_NAMES:
        ts = stage_tasks.get(name, [])
        if not ts:
            stages[name] = {"status": None, "why": "stage not in any run of this design"}
            continue
        latest = ts[-1]
        latest_checks = stage_checks.get(name, {})
        failed = sorted(n for n, c in latest_checks.items() if not c.passed)
        if latest.status == "completed" and not failed:
            verdict = "pass"
        elif latest.status in ("failed", "paused") or failed:
            verdict = "fail"
        else:
            verdict = latest.status
        times = [_seconds(t.started_at, t.ended_at) for t in ts]
        done = [x for x in times if x is not None]
        unfinished = sum(1 for t in ts if t.started_at and not t.ended_at)
        iterations: dict = {"attempts": sum(t.attempts for t in ts), "tasks": len(ts)}
        if name == "verification" and debug:
            iterations["debug_rounds"] = dict(debug)
        if name == "place_route" and phys and phys["pnr_iterations"]:
            iterations["pnr_iterations"] = phys["pnr_iterations"]
        stages[name] = {
            "status": latest.status, "verdict": verdict, "latest_run": latest.run_id,
            "checks_passed": sum(1 for c in latest_checks.values() if c.passed), "checks_failed": len(failed),
            "failed_checks": failed, "iterations": iterations,
            "wall_s": sum(done) if done else None,
            "wall_why": None if done else ("running" if unfinished else "not started"),
            "unfinished_tasks": unfinished,
            **{k: v for k, v in _usage(stage_usage.get(name, [])).items() if k in ("tokens", "llm_calls", "cost_usd")},
        }
    spans = [(t.started_at, t.ended_at) for t in tasks if t.started_at and t.ended_at]
    unattributed = stage_usage.get("(no task)", [])
    return {
        "design_id": d.id, "name": d.name,
        "runs": [{"id": r.id, "status": r.status, "stages": list(r.stages or []), "agent_kind": r.agent_kind,
                  "started_at": r.started_at.isoformat() if r.started_at else None,
                  "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                  "wall_s": _seconds(r.started_at, r.ended_at)} for r in runs],
        "stages": stages,
        "stages_passed": sum(1 for v in stages.values() if v.get("verdict") == "pass"),
        "checks_passed": sum(v.get("checks_passed", 0) for v in stages.values()),
        "checks_failed": sum(v.get("checks_failed", 0) for v in stages.values()),
        "wall_s": _union_seconds(spans) if spans else None,
        "wall_why": None if spans else "no finished task",
        "task_time_s": sum(_seconds(a, b) for a, b in spans) if spans else None,
        "usage": _usage(list(recs)),
        "usage_without_task": _usage(unattributed) if unattributed else None,
        "debug_rounds": debug,
        "physical": phys, "physical_why": phys_why,
    }


def build(session: Session, artifact_dir: Path | str, include_all: bool = False) -> dict:
    art = Path(artifact_dir)
    designs = []
    for d in session.scalars(select(Design).order_by(Design.created_at, Design.id)):
        if not include_all and any(fnmatch.fnmatch(d.name, p) for p in SKIP):
            continue
        if session.scalar(select(Run.id).where(Run.design_id == d.id).limit(1)) is None:
            continue
        designs.append(_design(session, d, art))
    return {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "artifact_dir": str(art), "stages": list(STAGE_NAMES), "designs": designs}


# --- markdown -------------------------------------------------------------------------------------------------
def _na(why: str | None) -> str:
    return f"– ({why})" if why else "–"


def _dur(s: float | None, why: str | None = None) -> str:
    if s is None:
        return _na(why)
    m, sec = divmod(int(round(s)), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{sec:02d}s" if h else f"{m}m{sec:02d}s"


def _num(v, why: str | None = None, fmt: str = "{}") -> str:
    return _na(why) if v is None else fmt.format(v)


def _usd(v: float) -> str:
    return f"${v:.4f}"


def _params(p: dict | None) -> str:
    return f"`{json.dumps(p)}`" if p else _na("no P&R report")


def _models(u: dict) -> str:
    if not u["by_model"]:
        return "– (no model calls recorded)"
    return "; ".join(f"{m} {v['tokens']:,} tok {_usd(v['cost_usd'])}"
                     + (" (estimated tokens, $0: coding-agent bridge)" if v["estimated_tokens"] else "")
                     for m, v in u["by_model"].items())


def _summary_row(d: dict) -> str:
    p = d["physical"]
    pnr = _num(p and p["pnr_iterations"], "M0.7 not run" if not p else "no P&R report")
    rd = p and p["readiness"]
    ready = f"A {rd['baseline_A_pct']}% / B {rd['baseline_B_pct']}%" if rd else \
        _na(d["physical_why"] or p["readiness_why"])
    setup = _na(d["physical_why"])
    if p:
        r = next(x for x in p["ppa"] if x["metric"].startswith("Worst setup slack, signoff"))
        setup = _num(r["final"], r["final_why"], "{:.4f} ns")
    u = d["usage"]
    return (f"| {d['name']} (`{d['design_id']}`) | {len(d['runs'])} | {d['stages_passed']}/{len(d['stages'])} | "
            f"{d['checks_passed']}/{d['checks_failed']} | {pnr} | {_dur(d['wall_s'], d['wall_why'])} | "
            f"{u['tokens']:,} | {_usd(u['cost_usd'])} | {setup} | {ready} |")


def summary_markdown(report: dict) -> str:
    lines = ["| Design | Runs | Stages passed | Checks pass/fail | P&R iterations | Wall time | Tokens | Cost | "
             "Final worst setup (signoff) | Readiness |", "|---|---|---|---|---|---|---|---|---|---|"]
    lines += [_summary_row(d) for d in report["designs"]]
    if not report["designs"]:
        lines.append("| – (no designs with runs) | | | | | | | | | |")
    return "\n".join(lines)


def _design_md(d: dict) -> list[str]:
    u = d["usage"]
    out = [f"## {d['name']} (`{d['design_id']}`)", "",
           "Runs: " + ", ".join(f"`{r['id']}` ({r['stages'][0] if r['stages'] else '?'}..{r['stages'][-1] if r['stages'] else '?'}, "
                                f"{r['status']})" for r in d["runs"]), "",
           "| Stage | Verdict | Status | Checks pass/fail | Failed checks | Iterations | Wall time | Tokens | Cost |",
           "|---|---|---|---|---|---|---|---|---|"]
    for name, st in d["stages"].items():
        if st["status"] is None:
            out.append(f"| {name} | {_na(st['why'])} | – | – | – | – | – | – | – |")
            continue
        it = st["iterations"]
        parts = [f"{it['attempts']} attempt(s) in {it['tasks']} task(s)"]
        if "debug_rounds" in it:
            parts.append("debug rounds: " + ", ".join(f"{k} {v}" for k, v in it["debug_rounds"].items()))
        if "pnr_iterations" in it:
            parts.append(f"{it['pnr_iterations']} P&R iteration(s)")
        wall = _dur(st["wall_s"], st["wall_why"])
        if st["wall_s"] is not None and st["unfinished_tasks"]:
            wall += f" (+{st['unfinished_tasks']} task(s) still running)"
        out.append(f"| {name} | {st['verdict']} | {st['status']} | {st['checks_passed']}/{st['checks_failed']} | "
                   f"{', '.join(st['failed_checks']) or '–'} | {'; '.join(parts)} | {wall} | "
                   f"{st['tokens']:,} | {_usd(st['cost_usd'])} |")
    out += ["", f"- Wall time: {_dur(d['wall_s'], d['wall_why'])} (union of task intervals; summed task time "
                f"{_dur(d['task_time_s'], d['wall_why'])})",
            f"- Tokens: {u['tokens']:,} in {u['llm_calls']} model call(s); cost {_usd(u['cost_usd'])} "
            f"(model {_usd(u['llm_cost_usd'])} + compute {_usd(u['other_cost_usd'])})",
            f"- Models: {_models(u)}"]
    if d["usage_without_task"]:
        w = d["usage_without_task"]
        out.append(f"- Of which not tied to a task: {w['tokens']:,} tokens, {_usd(w['cost_usd'])}")
    out.append("")
    p = d["physical"]
    if not p:
        out += [f"PPA vs default flow: {_na(d['physical_why'])}", ""]
        return out
    out += [f"### PPA vs default flow (run `{p['run_id']}`)", "",
            f"Default flow = P&R iteration 1 (config/pnr_ranges.yaml defaults: {_params(p['params_default'])}); "
            f"S2S final = iteration {_num(p['pnr_iterations'], 'no P&R report')} ({_params(p['params_final'])}).", "",
            "| Metric | Unit | Default flow | S2S final | Source |", "|---|---|---|---|---|"]
    for r in p["ppa"]:
        out.append(f"| {r['metric']} | {r['unit']} | {_num(r['default'], r['default_why'])} | "
                   f"{_num(r['final'], r['final_why'])} | {r['source']} |")
    rd = p["readiness"]
    out += ["", "- Tape-out readiness: " + (f"Baseline A {rd['baseline_A_pct']}%, Baseline B {rd['baseline_B_pct']}%"
                                            if rd else _na(p["readiness_why"])),
            "- DFM: " + (", ".join(f"{k} {v}" for k, v in p["dfm_summary"].items()) if p["dfm_summary"]
                         else _na(p["dfm_why"])), ""]
    return out


def markdown(report: dict) -> str:
    out = ["# S2S benchmark report", "",
           f"Generated {report['generated_at']} from the S2S database and the run reports in "
           f"`{report['artifact_dir']}`. Every number is a database record or a tool report; a value that "
           "was not recorded is shown as \"–\" with the reason.", "",
           "Verdict per stage: pass = latest task completed and the latest record of every check passed; fail = "
           "latest task failed/paused or a check's latest record failed; otherwise the task status. Tokens and "
           "cost are the metered usage records (model + compute). `claude-code-bridge` records are $0 with "
           "estimated tokens (~4 chars/token); their real cost is outside S2S's meter.", "",
           "## Summary", "", summary_markdown(report), ""]
    for d in report["designs"]:
        out += _design_md(d)
    return "\n".join(out).rstrip() + "\n"
