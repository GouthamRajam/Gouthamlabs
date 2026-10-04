"""M0.7 acceptance 2 experiment: one design at an intentionally tight clock; do Orion's parameter changes
improve WNS versus the default settings (iteration 1)?

    cd backend && python scripts/m07_tightclock.py <m06_run_id> <clock_mhz>   # synthesis -> place_route
    cd backend && python scripts/m07_tightclock.py --resume <m07_run_id>      # watch/resume, then report

An EXPERIMENT run, not the product path: the new run of the same design carries the task input
`clock_override_mhz` (recorded by the check clock_override_recorded; the SDC guard and config guard
check against the override clock). Stages synthesis..place_route only. When the run stops, the
comparison is written to reports/tightclock_result.json and .md in the run folder: iteration 1
(default parameters) vs the final iteration, worst setup slack (WNS) and TNS over the 9 corners,
every Orion change with its reason, and a per-corner table. Every number comes from the tool:
OpenSTA via OpenLane (OpenROAD.STAPostPNR) as recorded in reports/pnr_iteration_<k>.json (WNS,
per-corner worst slack) and in that iteration's STAPostPNR state (TNS). Chronos's independent
9-corner STA runs in the signoff stage, which this experiment does not run.

Verdict "WNS improved" only if the final WNS is greater than iteration 1's by the tool numbers.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
os.environ.setdefault("S2S_SECRETS_DIR", str(REPO / "var" / "secrets"))
os.environ.setdefault("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))
sys.path.insert(0, str(BACKEND))

from s2s.physical import flow as olf  # noqa: E402

SOURCE = "OpenSTA via OpenLane (OpenROAD.STAPostPNR), as recorded in reports/pnr_iteration_<k>.json"


def _tns_by_corner(run_dir: Path) -> dict[str, float]:
    """Per-corner setup TNS from the iteration's post-route STA state (the same OpenLane step whose
    worst slacks pnr_iteration_<k>.json records)."""
    d = olf.step_dir(run_dir, "OpenROAD.STAPostPNR") if run_dir.exists() else None
    st = d / "state_out.json" if d else None
    if not st or not st.exists():
        return {}
    return olf.corners(json.loads(st.read_text()).get("metrics", {}), "timing__setup__tns")


def _iteration(root: Path, k: int) -> dict:
    d = json.loads((root / f"reports/pnr_iteration_{k}.json").read_text())
    f = d.get("facts") or {}
    setup, hold = f.get("setup_ws_by_corner") or {}, f.get("hold_ws_by_corner") or {}
    tns = _tns_by_corner(root / "pnr" / "runs" / d["tag"])
    worst = min(setup, key=setup.get) if setup else None
    return {"iteration": k, "tag": d["tag"], "params": d["params"], "problems": d["problems"],
            "changes_applied": d.get("changes", []),
            "wns_ns": setup[worst] if worst else None, "wns_corner": worst,
            "tns_ns": min(tns.values()) if tns else None,
            "worst_hold_ns": min(hold.values()) if hold else None,
            "setup_ws_by_corner": setup, "hold_ws_by_corner": hold, "setup_tns_by_corner": tns,
            "timing_met": bool(setup) and bool(hold) and min(setup.values()) >= 0 and min(hold.values()) >= 0}


def compare(root: Path) -> dict:
    """Iteration 1 (default parameters) vs the final iteration, from the recorded tool numbers only."""
    table = json.loads((root / "reports/pnr_iterations.json").read_text())
    its = [_iteration(root, row["iteration"]) for row in table]
    first, last = its[0], its[-1]
    changes = [{"applied_in_iteration": it["iteration"], **c} for it in its[1:] for c in it["changes_applied"]]
    if len(its) == 1 and not first["problems"]:
        verdict = "no comparison: iteration 1 (default parameters) was already clean - the clock is not tight enough"
    elif len(its) == 1:
        verdict = "no comparison: the loop stopped after iteration 1 without trying a change"
    elif first["wns_ns"] is None or last["wns_ns"] is None:
        verdict = "no comparison: WNS was not reported for iteration 1 or the final iteration"
    elif last["wns_ns"] > first["wns_ns"]:
        verdict = "WNS improved"
    elif last["wns_ns"] == first["wns_ns"]:
        verdict = "WNS did not improve (unchanged)"
    else:
        verdict = "WNS did not improve (worse)"
    delta = None if first["wns_ns"] is None or last["wns_ns"] is None else round(last["wns_ns"] - first["wns_ns"], 6)
    return {"source": SOURCE, "iterations": len(its), "first": first, "final": last, "orion_changes": changes,
            "wns_delta_ns": delta, "wns_improved": verdict == "WNS improved", "verdict": verdict,
            "final_clean": not last["problems"], "all_iterations": [
                {k: it[k] for k in ("iteration", "params", "wns_ns", "wns_corner", "tns_ns", "worst_hold_ns",
                                    "problems")} for it in its]}


def _n(v) -> str:
    return "n/a" if v is None else f"{v:.4f}"


def markdown(r: dict, run_id: str = "", clock: str = "") -> str:
    a, b = r["first"], r["final"]
    out = [f"# Tight-clock experiment (M0.7 acceptance 2){' - run ' + run_id if run_id else ''}", ""]
    if clock:
        out += [clock, ""]
    out += [f"**Verdict: {r['verdict']}.**", "",
            f"Numbers: {r['source']}; TNS from the same step's per-corner metrics. Chronos's independent 9-corner "
            "STA is in the signoff stage, which this experiment does not run.", "",
            "| | iteration | WNS (ns) | worst corner | TNS (ns, worst corner) | worst hold (ns) | problems |",
            "|---|---|---|---|---|---|---|",
            f"| default parameters | {a['iteration']} | {_n(a['wns_ns'])} | {a['wns_corner']} | {_n(a['tns_ns'])} | "
            f"{_n(a['worst_hold_ns'])} | {len(a['problems'])} |",
            f"| final | {b['iteration']} | {_n(b['wns_ns'])} | {b['wns_corner']} | {_n(b['tns_ns'])} | "
            f"{_n(b['worst_hold_ns'])} | {len(b['problems'])} |", "",
            f"WNS change: {_n(r['wns_delta_ns'])} ns over {r['iterations']} iteration(s); final iteration "
            f"{'clean' if r['final_clean'] else 'not clean: ' + '; '.join(b['problems'][:5])}.", "",
            "## Orion's changes (each with its reason)", ""]
    out += [f"- iteration {c['applied_in_iteration']}: {c['param']} -> {c['value']}: {c['reason']}"
            for c in r["orion_changes"]] or ["- none"]
    out += ["", "## Parameters per iteration", "", "| iteration | parameters | WNS (ns) | TNS (ns) |", "|---|---|---|---|"]
    out += [f"| {it['iteration']} | {json.dumps(it['params'])} | {_n(it['wns_ns'])} | {_n(it['tns_ns'])} |"
            for it in r["all_iterations"]]
    out += ["", f"## Per corner, iteration {a['iteration']} vs iteration {b['iteration']} ({SOURCE.split(',')[0]})", "",
            "| corner | setup WS first | setup WS final | setup TNS first | setup TNS final | hold WS first | hold WS final |",
            "|---|---|---|---|---|---|---|"]
    for c in sorted(set(a["setup_ws_by_corner"]) | set(b["setup_ws_by_corner"])):
        out.append(f"| {c} | {_n(a['setup_ws_by_corner'].get(c))} | {_n(b['setup_ws_by_corner'].get(c))} | "
                   f"{_n(a['setup_tns_by_corner'].get(c))} | {_n(b['setup_tns_by_corner'].get(c))} | "
                   f"{_n(a['hold_ws_by_corner'].get(c))} | {_n(b['hold_ws_by_corner'].get(c))} |")
    return "\n".join(out) + "\n"


def write_result(root: Path, run_id: str = "", clock: str = "") -> dict:
    r = compare(root)
    r["run_id"], r["clock"] = run_id, clock
    (root / "reports/tightclock_result.json").write_text(json.dumps(r, indent=2, default=str) + "\n")
    (root / "reports/tightclock_result.md").write_text(markdown(r, run_id, clock))
    return r


def main() -> int:
    from sqlalchemy import select

    from s2s.agents.runtime import artifact_dir
    from s2s.db.models import Check, Design, Event, Run, Task
    from s2s.db.session import session
    from s2s.models import access
    from s2s.orchestrator.engine import create_run

    def fmt(e: Event) -> str:
        to = f" -> {e.to_agent_id}" if e.to_agent_id else ""
        return f"{e.ts:%H:%M:%S}  {e.type:<15} {(e.agent_id or '-'):<9}{to:<12} {e.summary}"

    resume = sys.argv[1] == "--resume"
    src = sys.argv[2] if resume else sys.argv[1]
    timeout_min = float(os.environ.get("S2S_M07_TIMEOUT_MIN", "240"))
    view = access.public_view()
    print(f"model access: provider={view['provider']} model={view['model']} key_saved={view['key_set']}")
    with session() as s:
        srun = s.get(Run, src)
        design = s.get(Design, srun.design_id)
        if resume:
            run_id = src
        else:
            mhz = float(sys.argv[2])
            run_id = create_run(s, design, from_stage="synthesis", to_stage="place_route", agent_kind="s2s",
                                inputs={"source_run": src, "clock_override_mhz": mhz}).id
    print(f"design {design.name}: tight-clock experiment run {run_id} (synthesis -> place_route)\n")
    logs = REPO / "var" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    evlog = open(logs / f"events_{run_id}.txt", "a" if resume else "w")
    # Starts an orchestrator; if one is already running (one per database), this one exits at once and
    # the running one does the work.
    orc = None if os.environ.get("S2S_NO_ORCHESTRATOR") == "1" else subprocess.Popen(
        [sys.executable, "-m", "s2s.orchestrator", "--poll", "0.2"], cwd=BACKEND, env=os.environ.copy(),
        stdout=open(logs / f"orchestrator_{run_id}.log", "ab"), stderr=subprocess.STDOUT, start_new_session=True)
    quiet = {"task.heartbeat", "manager.checkin", "agent.status", "artifact.created"}
    seen, t0 = 0, time.monotonic()
    try:
        while True:
            with session() as s:
                evs = s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()
                for e in evs[seen:]:
                    evlog.write(fmt(e) + "\n")
                    if e.type not in quiet:
                        print(fmt(e)[:220], flush=True)
                evlog.flush()
                seen = len(evs)
                run = s.get(Run, run_id)
                tasks = s.scalars(select(Task).where(Task.run_id == run_id)).all()
                stopped = [t for t in tasks if t.status in ("paused", "failed")]
                all_done = tasks and all(t.status == "completed" for t in tasks)
            if run.status in ("completed", "failed") or stopped or (all_done and time.monotonic() - t0 > 5) \
                    or time.monotonic() - t0 > timeout_min * 60:
                break
            time.sleep(2.0)
        time.sleep(2)
        with session() as s:
            for e in s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()[seen:]:
                evlog.write(fmt(e) + "\n")
                print(fmt(e)[:220])
    finally:
        if orc is not None:
            os.killpg(orc.pid, signal.SIGTERM)
            orc.wait(timeout=60)
        evlog.close()
    with session() as s:
        run = s.get(Run, run_id)
        tasks = s.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.seq)).all()
        print(f"\n=== run {run_id}: {run.status} in {(time.monotonic() - t0) / 60:.1f} min ===")
        for t in tasks:
            print(f"  {t.stage:<13} {t.agent_id:<6} {t.status}")
        ov = [c for t in tasks for c in s.scalars(select(Check).where(Check.task_id == t.id,
                                                                     Check.check_name == "clock_override_recorded"))]
        clock = (f"Clock: spec {ov[-1].metrics['spec_mhz']} MHz, experiment override {ov[-1].metrics['override_mhz']} "
                 f"MHz ({ov[-1].metrics['override_period_ns']} ns) - {ov[-1].metrics['reason']}.") if ov else ""
    root = artifact_dir() / "runs" / run_id
    if not (root / "reports/pnr_iterations.json").exists():
        print("\nno place-and-route iteration was recorded (the run stopped before place_route); no comparison")
        return 1
    r = write_result(root, run_id, clock)
    print("\n" + markdown(r, run_id, clock))
    print(f"written: {root / 'reports/tightclock_result.json'} and .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
