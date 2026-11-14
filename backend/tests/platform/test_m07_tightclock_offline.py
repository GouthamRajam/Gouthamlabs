"""M0.7 acceptance 2 plumbing, offline: the tight-clock EXPERIMENT path (task input clock_override_mhz) with
REAL OpenLane 2 / OpenROAD / OpenSTA / eqy (s2s-eda) and SCRIPTED model answers (hand-written fixtures).

counter8 (spec 100 MHz) runs synthesis..place_route at an intentionally tight clock. Orion's scripted
answer makes one parameter change set within pnr_ranges.yaml; the tools decide what it does to timing.
This test checks that the override is recorded, that the SDC guard checks the override clock exactly,
that the iterations and changes are recorded, and that scripts/m07_tightclock.py reports the tool numbers
honestly. It does NOT assert that WNS improves: that is the tools' result, reported as it is. The real
model run is scripts/m07_tightclock.py."""
from __future__ import annotations

import json
from collections import deque

import yaml
from sqlalchemy import select

from tests.platform.conftest import new_design
from tests.platform.test_m05_offline import ans, checks_of, events, files
from tests.platform.test_m07_offline import F7, REPORT, pytestmark, source_run  # noqa: F401

# Chosen with the real tools. counter8's worst path with 30% I/O delays is input -> register; after CTS
# the capture clock latency and the resizer's repairs give it MORE slack than pre-layout STA (160 MHz:
# pre-layout +0.368 ns, post-route +0.688 ns; 200 MHz fails pre-layout, which blocks synthesis by
# design). So with the 30%/30% I/O split we found no clock that passes pre-layout and fails iteration 1.
# Register -> output paths lose slack after layout (launch clock latency, output buffer and wire: about
# 0.77 ns at ss), so this fixture also tightens the output budget: at 170 MHz with output delay 75% of
# the period, pre-layout is met (+0.110 ns) and iteration 1 (default parameters) misses setup on the
# output paths (-0.186 ns at max_ss_100C_1v60), measured with the real tools.
MHZ = 170.0
OUT_FRAC = 0.75
PERIOD = round(1000.0 / MHZ, 6)
STAGES = ("synthesis", "dft", "floorplan", "place_route")


def tight_sdc(period: float) -> str:
    io, oo = round(0.3 * period, 4), round(OUT_FRAC * period, 4)
    return f"""# Hand-written test fixture (scripted model answer for the offline tight-clock test). Not agent output.
create_clock -name clk -period {period} [get_ports {{clk}}]
set_clock_uncertainty 0.25 [get_clocks {{clk}}]
set_max_fanout 10 [current_design]
# DEFAULT: input delay 30% of the {period} ns period
set_input_delay {io} -clock [get_clocks {{clk}}] [get_ports {{rst_n en up load load_value[*]}}]
# EXPERIMENT: output delay {OUT_FRAC:.0%} of the period (a tight output budget; tighter than the 30% default)
set_output_delay {oo} -clock [get_clocks {{clk}}] [get_ports {{count[*]}}]
# DEFAULT: driving cell and load
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_2 -pin Y [get_ports {{rst_n en up load load_value[*]}}]
set_load 0.0334 [get_ports {{count[*]}}]
"""


ORION_CHANGE = ans(changes=[
    {"param": "FP_CORE_UTIL", "value": 55,
     "reason": "fixture: a smaller core shortens the I/O-to-register wires on the failing setup paths"},
    {"param": "PL_TARGET_DENSITY_PCT", "value": 75,
     "reason": "fixture: denser placement shortens the nets of the worst paths (kept 20 points above the core utilization)"}],
    diagnosis={"root_cause": "fixture: setup fails at the ss corners on I/O-to-register paths (wire delay)",
               "evidence": ["iteration 1 setup slack < 0 at the ss corners"],
               "why_this_parameter": "fixture: core size and density set the wire lengths on those paths"},
    escalate={"needed": False, "why": ""}, report_markdown="# Orion (fixture)")
ORION_STOP = ans(changes=[], diagnosis={"root_cause": "fixture", "evidence": [], "why_this_parameter": ""},
                 escalate={"needed": True, "why": "fixture: one change set per experiment; results "
                                       "reported as the tools give them"}, report_markdown="# Orion (fixture)")


class Replies:
    """Scripted answers in call order; Orion's change request is recognised by its goal text, because
    whether it is asked a second time depends on the tool results."""

    def __init__(self):
        self.fixed = deque([
            files(("constraints/constraints.sdc", tight_sdc(PERIOD))),   # Sienna
            ans(findings=[]),                                           # Sentinel
            REPORT,                                                     # Sienna synth report
            files(("dft/dft_plan.md", (F7 / "dft_plan.md").read_text())),  # Tess
            files(("pnr/floorplan.json", (F7 / "floorplan.json").read_text()),  # Grid
                  ("pnr/pin_order.cfg", (F7 / "pin_order.cfg").read_text())),
        ])
        self.orion = deque([ORION_CHANGE])
        self.orion_calls = 0

    def __call__(self, system, messages):
        text = system + "".join(str(m.get("content", "")) for m in messages)
        if self.fixed:
            return self.fixed.popleft()
        if "has problems:" in text and "change at most two parameters" in text.lower():
            self.orion_calls += 1
            return self.orion.popleft() if self.orion else ORION_STOP
        return REPORT                                                   # Tick, Orion, Mason reports


def run_tight(replies: Replies):
    from s2s.agents.m05 import DesignAgent
    from s2s.agents.runtime import run_task
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.models.gateway import ModelGateway, ScriptedProvider
    from s2s.orchestrator.engine import create_run
    import s2s.agents.m07  # noqa: F401
    provider = ScriptedProvider(deque([replies] * 40))
    with session() as s:
        d = new_design(s, "counter8")
        src = source_run(s, d)
        run_id = create_run(s, d, from_stage="synthesis", to_stage="place_route", agent_kind="s2s",
                            inputs={"source_run": src, "clock_override_mhz": MHZ}).id
    out = {}
    for st in STAGES:
        with session() as s:
            t = s.scalar(select(Task).where(Task.run_id == run_id, Task.stage == st))
            t.status = "running"
            tid = t.id
        out[st] = run_task(tid, DesignAgent(), ModelGateway(provider))
        if out[st].status != "completed":
            break
    return run_id, out


def test_counter8_tight_clock_experiment(platform):
    from s2s.agents.runtime import artifact_dir
    from s2s.db.models import Check, Task
    from s2s.db.session import session
    from s2s.physical import flow as olf
    from scripts.m07_tightclock import compare, markdown, write_result
    replies = Replies()
    run_id, out = run_tight(replies)
    print({k: (v.status, v.detail) for k, v in out.items()})
    root = artifact_dir() / "runs" / run_id
    with session() as s:
        recs = {c.check_name: c for c in s.scalars(select(Check).join(Task, Task.id == Check.task_id)
                                                     .where(Task.run_id == run_id).order_by(Check.id))}
        ov, guard = recs["clock_override_recorded"], recs["sdc_guard"]
        ov_m, guard_m = dict(ov.metrics), dict(guard.metrics)
        ov_ok, guard_ok = ov.passed, guard.passed
    latest = dict(checks_of(run_id))
    print(json.dumps(latest, indent=1))
    pre = json.loads((root / "reports/synth_tool.json").read_text())["pre_layout_setup_ws_by_corner"]
    print(f"{MHZ} MHz: pre-layout worst setup slack {min(pre.values())} ns at {min(pre, key=pre.get)}")
    # the override is recorded, with the spec clock beside it
    assert ov_ok and ov_m["spec_mhz"] == 100 and ov_m["override_mhz"] == MHZ and ov_m["override_period_ns"] == PERIOD
    assert ov_m["reason"] == "acceptance experiment: intentionally tight clock"
    assert any(e[0] == "plan" and e[1] == "Mason" and f"{MHZ} MHz" in e[2] and "EXPERIMENT" in e[2]
               for e in events(run_id))
    # the SDC guard checked the SDC against the override clock exactly (and the flow used that period)
    assert guard_ok and guard_m["found"]["clocks"] == {"clk": PERIOD}
    spec = yaml.safe_load((root / "spec/spec.yaml").read_text())
    assert spec["clocks"] == [{"name": "clk", "freq_mhz": 100}]
    _, ins, outs = olf.port_bits(spec)
    assert olf.sdc_problems((root / "constraints/constraints.sdc").read_text(), clocks=spec["clocks"], inputs=ins,
                            outputs=outs)[0], "the experiment SDC must NOT pass against the spec clock"
    assert json.loads((root / "pnr/config.json").read_text())["CLOCK_PERIOD"] == PERIOD
    assert json.loads((root / "pnr/s2s_physical.json").read_text())["period_ns"] == PERIOD
    assert latest["config_guard_synthesis"] is True and latest["config_guard_floorplan"] is True
    assert latest["sta_pre_layout"] is True, "pre-layout timing must meet for this experiment clock"
    assert out["floorplan"].status == "completed" and "place_route" in out

    # iterations recorded, with Orion's change and reason
    table = json.loads((root / "reports/pnr_iterations.json").read_text())
    first = json.loads((root / "reports/pnr_iteration_1.json").read_text())
    print("iteration 1 setup WS by corner:", first["facts"]["setup_ws_by_corner"])
    assert first["params"] == olf.default_params() | {"FP_CORE_UTIL": 45}
    assert min(first["facts"]["setup_ws_by_corner"].values()) < 0, \
        f"{MHZ} MHz is not tight for counter8: iteration 1 met setup (pick a tighter clock)"
    assert len(table) >= 2 and replies.orion_calls >= 1
    assert table[1]["changes"] == ORION_CHANGE["changes"]
    assert table[1]["params"]["FP_CORE_UTIL"] == 55 and table[1]["params"]["PL_TARGET_DENSITY_PCT"] == 75
    assert latest["orion_change_in_range"] is True and latest["pnr_params_in_range"] is True

    # the result script reports the tool numbers exactly, and its verdict follows them
    r = write_result(root, run_id, f"Clock: spec 100 MHz, experiment override {MHZ} MHz")
    print(markdown(r, run_id))
    assert r["iterations"] == len(table)
    for side, k in (("first", 1), ("final", table[-1]["iteration"])):
        it = json.loads((root / f"reports/pnr_iteration_{k}.json").read_text())
        setup = it["facts"]["setup_ws_by_corner"]
        assert len(setup) == 9 and r[side]["setup_ws_by_corner"] == setup
        assert r[side]["hold_ws_by_corner"] == it["facts"]["hold_ws_by_corner"]
        assert r[side]["wns_ns"] == min(setup.values()) and r[side]["params"] == it["params"]
        sta = olf.step_dir(root / "pnr/runs" / it["tag"], "OpenROAD.STAPostPNR")
        tns = olf.corners(json.loads((sta / "state_out.json").read_text())["metrics"], "timing__setup__tns")
        assert len(tns) == 9 and r[side]["setup_tns_by_corner"] == tns and r[side]["tns_ns"] == min(tns.values())
    assert [{k: v for k, v in c.items() if k != "applied_in_iteration"} for c in r["orion_changes"]][:2] == \
        ORION_CHANGE["changes"]
    assert r["wns_improved"] == (r["final"]["wns_ns"] > r["first"]["wns_ns"])
    assert r["wns_delta_ns"] == round(r["final"]["wns_ns"] - r["first"]["wns_ns"], 6)
    assert r["verdict"].startswith("WNS improved" if r["wns_improved"] else "WNS did not improve")
    assert compare(root) == {k: v for k, v in r.items() if k not in ("run_id", "clock")}
    assert json.loads((root / "reports/tightclock_result.json").read_text())["verdict"] == r["verdict"]
    md = (root / "reports/tightclock_result.md").read_text()
    assert r["verdict"] in md and "OpenSTA via OpenLane" in md and ORION_CHANGE["changes"][0]["reason"] in md
    print(f"TIGHTCLOCK {MHZ} MHz: iteration 1 WNS {r['first']['wns_ns']} ns TNS {r['first']['tns_ns']} ns -> "
          f"iteration {r['final']['iteration']} WNS {r['final']['wns_ns']} ns TNS {r['final']['tns_ns']} ns: {r['verdict']}")
