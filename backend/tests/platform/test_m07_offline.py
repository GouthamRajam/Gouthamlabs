"""M0.7 plumbing, offline: real Postgres and REAL OpenLane 2 / OpenROAD / Magic / KLayout / Netgen /
OpenSTA / eqy / Icarus (s2s-eda), SCRIPTED model answers (hand-written fixtures). Runs counter8 from
the G2-frozen RTL to a signed tape-out package, stage by stage, without spending money. The
real-model runs are scripts/run_m07.py.

The source run (G2 approved, RTL artifacts, M0.6 check records) is fabricated here as a fixture:
this test checks the M0.7 runtime, not M0.6's results."""
from __future__ import annotations

import json
import shutil
from collections import deque
from pathlib import Path

import pytest
from sqlalchemy import select

from tests.platform.conftest import new_design
from tests.platform.test_m05_offline import ans, checks_of, eda_available, events, files

F5 = Path(__file__).parent / "m05_fixtures"
F6 = Path(__file__).parent / "m06_fixtures"
F7 = Path(__file__).parent / "m07_fixtures"
REPORT = ans(report_markdown="# Report (fixture)\nNumbers as in the tool data.")
STAGES = ("synthesis", "dft", "floorplan", "place_route", "signoff", "gdsii")

pytestmark = [pytest.mark.skipif(not eda_available(), reason="s2s-eda image not built"), pytest.mark.slow]


def source_run(s, design, *, g2: bool = True) -> str:
    """A finished verification run of `design`: files on disk, RTL artifacts, M0.6 checks, G2."""
    from s2s.agents.runtime import artifact_dir
    from s2s.db.models import Artifact, Check, Gate, Run, Task
    from s2s.events.bus import utcnow
    from s2s.ids import new_id
    run = Run(id=new_id("run"), design_id=design.id, status="completed", stages=["verification"], agent_kind="s2s")
    s.add(run)
    s.flush()
    t = Task(id=new_id("task"), run_id=run.id, agent_id="Rex", stage="verification", status="completed",
             title="fixture verification", seq=0, team_id="regression_ops", inputs={"design_name": design.name})
    s.add(t)
    s.flush()
    root = artifact_dir() / "runs" / run.id
    shutil.rmtree(root, ignore_errors=True)
    for d in ("spec", "arch", "rtl", "tb"):
        (root / d).mkdir(parents=True)
    (root / "spec/spec.yaml").write_text((F5 / "counter8_spec.yaml").read_text())
    (root / "arch/arch.yaml").write_text((F5 / "counter8_arch.yaml").read_text())
    rtl = (F5 / "counter8.v").read_text()
    (root / "rtl/counter8.v").write_text(rtl)
    for f in ("test_counter8.py", "ref_model.py"):
        shutil.copy(F6 / f, root / "tb" / f)
    import hashlib
    s.add(Artifact(sha256=hashlib.sha256(rtl.encode()).hexdigest(), kind="rtl", path="rtl/counter8.v",
                   size=len(rtl), created_by_task=t.id))
    for name in ("regression_100pct", "coverage_line", "coverage_toggle", "coverage_functional", "formal_3_meaningful",
                 "formal_vacuity", "anti_cheat_final"):
        s.add(Check(id=new_id("chk"), task_id=t.id, check_name=name, tool="fixture", command="", passed=True, metrics={}))
    s.flush()
    if g2:
        s.add(Gate(id=new_id("gate"), run_id=run.id, gate="G2", status="approved", after_stage="verification",
                   decision="approved", reviewer="fixture", decided_at=utcnow()))
        s.add(Gate(id=new_id("gate"), run_id=run.id, gate="G1", status="approved", after_stage="architecture",
                   decision="approved", reviewer="fixture", decided_at=utcnow()))
    s.flush()
    return run.id


REPLIES = [
    files(("constraints/constraints.sdc", (F7 / "constraints.sdc").read_text())),  # Sienna
    ans(findings=[]),                                                                # Sentinel
    REPORT,                                                                          # Sienna synth report
    files(("dft/dft_plan.md", (F7 / "dft_plan.md").read_text())),                    # Tess
    files(("pnr/floorplan.json", (F7 / "floorplan.json").read_text()),               # Grid
          ("pnr/pin_order.cfg", (F7 / "pin_order.cfg").read_text())),
    REPORT, REPORT, REPORT,                                                          # Tick, Orion, Mason
    REPORT, REPORT,                                                                  # Chronos, Volta
    ans(ranked=[], scorecard_markdown="# DFM scorecard (fixture)"),                  # Fabian
    REPORT, REPORT,                                                                  # Gideon, Sloane
]


def run_m07(replies: list, g2: bool = True):
    from s2s.agents.m05 import DesignAgent
    from s2s.agents.runtime import run_task
    from s2s.db.models import Gate, Task
    from s2s.db.session import session
    from s2s.events.bus import utcnow
    from s2s.ids import new_id
    from s2s.models.gateway import ModelGateway, ScriptedProvider
    from s2s.orchestrator.engine import _stage_checks_ok, create_run
    import s2s.agents.m07  # noqa: F401
    provider = ScriptedProvider(deque(replies))
    with session() as s:
        d = new_design(s, "counter8")
        src = source_run(s, d, g2=g2)
        run_id = create_run(s, d, from_stage="synthesis", to_stage="gdsii", agent_kind="s2s",
                            inputs={"source_run": src}).id
    out = {}
    for st in STAGES:
        with session() as s:
            t = s.scalar(select(Task).where(Task.run_id == run_id, Task.stage == st))
            t.status = "running"
            tid = t.id
        out[st] = run_task(tid, DesignAgent(), ModelGateway(provider))
        if out[st].status != "completed":
            break
        if st == "signoff":  # what the engine does in gates.mode=auto
            with session() as s:
                ok = _stage_checks_ok(s, tid)
                s.add(Gate(id=new_id("gate"), run_id=run_id, gate="G3", status="approved" if ok else "pending",
                           after_stage="signoff", decided_at=utcnow() if ok else None))
    return run_id, out, provider


def test_counter8_physical_end_to_end(platform):
    from s2s.agents.runtime import artifact_dir
    run_id, out, provider = run_m07(list(REPLIES))
    print({k: (v.status, v.detail) for k, v in out.items()})
    latest = dict(checks_of(run_id))
    print(json.dumps(latest, indent=1))
    assert all(o.status == "completed" for o in out.values()), out
    assert len(out) == 6 and not provider.replies
    for name in ("rtl_frozen_at_g2", "sdc_guard", "sentinel_constraints_review", "config_guard_synthesis",
                 "openlane_synthesis", "sta_pre_layout", "eqy_rtl_vs_synth", "dft_plan_complete", "floorplan_plan",
                 "utilization_in_range", "pdn_connected", "pins_per_plan", "route_drc_zero", "antenna_clean_after_route",
                 "cts_skew_target", "post_route_timing_all_corners", "drv_clean", "openlane_signoff_steps",
                 "drc_magic_final_gds", "drc_klayout_final_gds", "drc_tools_agree", "lvs_final_gds", "antenna_final",
                 "density_rules", "sta_all_corners", "sta_matches_openlane", "power_estimated", "ir_drop_within_limit",
                 "dfm_no_high_severity", "eqy_rtl_vs_final", "gls_final_netlist", "gds_readback", "package_drc_magic",
                 "package_drc_klayout", "package_lvs", "pins_match_spec", "reproduce_clean_container",
                 "constraints_not_loosened", "no_waivers", "tests_not_weakened", "tapeout_checklist_complete",
                 "manifest_signed"):
        assert latest.get(name) is True, (name, latest.get(name))
    root = artifact_dir() / "runs" / run_id
    rep = json.loads((root / "reports/tapeout_readiness.json").read_text())
    # decision 2026-10-06: DFT deferred (0), IR/EM 0.5 -> A 90/97; the gate is the hard checks
    assert rep["baseline_A_pct"] == 92.7 and rep["baseline_B_pct"] == 64.1
    assert rep["hard_checks"]["verdict"] == "PASS" and rep["hard_checks"]["passed"] == 6
    items = json.loads((root / "reports/tapeout_checklist.json").read_text())
    assert all(i["done"] for i in items) and len(items) == 16
    man = (root / "tapeout/MANIFEST.sha256").read_text()
    assert "gds/counter8.gds" in man and "reproduce.sh" in man and "reports/tapeout_readiness.md" in man
    ev = events(run_id)
    assert any(e[0] == "handoff" and e[1] == "Mason" for e in ev) and any(e[0] == "handoff" and e[1] == "Sloane" for e in ev)
    assert any(e[0] == "tool_call" and e[1] == "Proof" for e in ev)


def test_no_g2_no_zone3(platform):
    run_id, out, _ = run_m07(list(REPLIES), g2=False)
    assert out["synthesis"].status == "paused"
    assert dict(checks_of(run_id))["rtl_frozen_at_g2"] is False
