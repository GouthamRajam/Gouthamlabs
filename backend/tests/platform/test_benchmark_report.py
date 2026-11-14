"""M0.8 acceptance 2, offline: the benchmark report's numbers are exactly the inserted DB records and run
reports, and missing data renders as "–" with a reason. Needs Postgres (the platform fixture's fresh DB)."""
from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal

from s2s.db.models import Check, Event, Run, Task, UsageRecord
from s2s.db.session import session
from s2s.ids import new_id
from s2s.reports import benchmark
from tests.platform.conftest import new_design

T0 = dt.datetime(2026, 10, 1, 8, 0, tzinfo=dt.timezone.utc)


def _task(s, run, stage, status, attempts, start_min, end_min):
    t = Task(id=new_id("task"), run_id=run.id, agent_id="a1", stage=stage, status=status, attempts=attempts,
             started_at=T0 + dt.timedelta(minutes=start_min) if start_min is not None else None,
             ended_at=T0 + dt.timedelta(minutes=end_min) if end_min is not None else None,
             inputs={"source_run": "run_x"} if stage != "spec" else {})
    s.add(t)
    s.flush()
    return t


def _check(s, task, name, passed):
    s.add(Check(id=new_id("chk"), task_id=task.id, check_name=name, tool="tool", passed=passed))
    s.flush()


def _usage(s, task, source, qty, cost, model=None):
    s.add(UsageRecord(id=new_id("use"), task_id=task.id, run_id=task.run_id, agent_id="a1", source=source,
                      quantity=qty, unit="tokens" if source == "llm" else "cpu_seconds", unit_cost=Decimal(0),
                      cost_usd=Decimal(cost), model=model))


def _event(s, run, summary):
    s.add(Event(id=new_id("evt"), ts=T0, run_id=run.id, type="tool_call", summary=summary))


def test_benchmark_report(platform, tmp_path, monkeypatch):
    art = tmp_path / "art"
    monkeypatch.setenv("S2S_ARTIFACT_DIR", str(art))
    with session() as s:
        d = new_design(s, "counter8")
        r1 = Run(id=new_id("run"), design_id=d.id, status="completed", stages=["spec", "verification"],
                 started_at=T0, agent_kind="s2s")
        r2 = Run(id=new_id("run"), design_id=d.id, status="completed", stages=["place_route", "signoff"],
                 started_at=T0 + dt.timedelta(hours=1), agent_kind="s2s")
        s.add_all([r1, r2])
        s.flush()
        spec = _task(s, r1, "spec", "completed", 1, 0, 10)               # 10 min
        ver = _task(s, r1, "verification", "completed", 2, 5, 35)        # 30 min, overlaps spec by 5
        pnr = _task(s, r2, "place_route", "completed", 1, 60, 80)        # 20 min
        sig = _task(s, r2, "signoff", "failed", 3, 80, 90)               # 10 min
        _check(s, spec, "spec_schema", True)
        _check(s, spec, "spec_consistency", True)
        _check(s, ver, "regression", False)   # superseded by the later record below
        _check(s, ver, "regression", True)
        _check(s, ver, "formal", True)
        _check(s, pnr, "openlane_routing", True)
        _check(s, sig, "sta_all_corners", False)
        _usage(s, spec, "llm", 1000, "0.01", "claude-sonnet-5-5")
        _usage(s, ver, "llm", 2500, "0.03", "claude-sonnet-5-5")
        _usage(s, ver, "llm", 400, "0", "claude-code-bridge")
        _usage(s, pnr, "compute", 120, "0.002")
        for summary in ("Rex: regression main_r1: t x seeds [1] (verilator)",
                        "Rex: regression main_r2: t x seeds [1] (verilator)",
                        "Rex: regression main_r2_rerun: t x seeds [1] (verilator)",
                        "Rex: regression main_r2 started"):
            _event(s, r1, summary)
        # a design with only a front-end run, and a test-suite design that must be skipped
        d2 = new_design(s, "uart")
        r3 = Run(id=new_id("run"), design_id=d2.id, status="running", stages=["spec"], started_at=T0, agent_kind="s2s")
        s.add(r3)
        s.flush()
        _task(s, r3, "spec", "running", 1, 0, None)
        d3 = new_design(s, "dex_triage_suite")
        s.add(Run(id=new_id("run"), design_id=d3.id, status="running", stages=["verification"], agent_kind="s2s"))
        ids = (d.id, d2.id, r2.id)

    rep = art / "runs" / ids[2] / "reports"
    rep.mkdir(parents=True)
    corners = [f"{p}_{t}" for p in ("min", "nom", "max") for t in ("tt_025C_1v80", "ss_100C_1v60", "ff_n40C_1v95")]
    it1 = {"iteration": 1, "params": {"FP_CORE_UTIL": 45}, "problems": ["hold slack -0.0500 ns at x"],
           "facts": {"setup_ws_by_corner": {"a": 1.5, "b": 0.9}, "hold_ws_by_corner": {"a": -0.05, "b": 0.1},
                     "utilization": 0.45, "wirelength_um": 1200}}
    it2 = {"iteration": 2, "params": {"FP_CORE_UTIL": 40}, "problems": [],
           "facts": {"setup_ws_by_corner": {"a": 1.4, "b": 0.8}, "hold_ws_by_corner": {"a": 0.02, "b": 0.12},
                     "utilization": 0.40, "wirelength_um": 1300}}
    (rep / "pnr_iterations.json").write_text(json.dumps([it1, it2]))
    (rep / "sta_tool.json").write_text(json.dumps({"corners": {
        c: {"setup_ws_ns": 2.0 + i / 10, "hold_ws_ns": 0.3 + i / 100} for i, c in enumerate(corners)}}))

    with session() as s:
        report = benchmark.build(s, art)
    by_name = {x["name"]: x for x in report["designs"]}
    assert set(by_name) == {"counter8", "uart"}  # *_suite skipped
    with session() as s:
        assert {x["name"] for x in benchmark.build(s, art, include_all=True)["designs"]} == \
            {"counter8", "uart", "dex_triage_suite"}

    c8 = by_name["counter8"]
    st = c8["stages"]
    assert (st["spec"]["verdict"], st["spec"]["checks_passed"], st["spec"]["checks_failed"]) == ("pass", 2, 0)
    assert (st["verification"]["verdict"], st["verification"]["checks_passed"]) == ("pass", 2)  # latest record wins
    assert st["verification"]["iterations"] == {"attempts": 2, "tasks": 1, "debug_rounds": {"main": 2}}
    assert st["place_route"]["iterations"] == {"attempts": 1, "tasks": 1, "pnr_iterations": 2}
    assert (st["signoff"]["verdict"], st["signoff"]["failed_checks"]) == ("fail", ["sta_all_corners"])
    assert st["rtl"] == {"status": None, "why": "stage not in any run of this design"}
    assert [st[k]["wall_s"] for k in ("spec", "verification", "place_route", "signoff")] == [600, 1800, 1200, 600]
    assert c8["wall_s"] == 35 * 60 + 30 * 60  # union: 08:00-08:35 and 09:00-09:30
    assert c8["task_time_s"] == 600 + 1800 + 1200 + 600
    assert (st["spec"]["tokens"], st["verification"]["tokens"]) == (1000, 2900)
    assert st["verification"]["cost_usd"] == 0.03 and st["place_route"]["cost_usd"] == 0.002
    u = c8["usage"]
    assert (u["tokens"], u["llm_calls"], u["llm_cost_usd"], u["other_cost_usd"]) == (3900, 3, 0.04, 0.002)
    assert u["cost_usd"] == 0.042
    assert u["by_model"]["claude-code-bridge"] == {"records": 1, "tokens": 400, "cost_usd": 0.0,
                                                   "estimated_tokens": True}
    assert u["by_model"]["claude-sonnet-5-5"]["tokens"] == 3500
    assert (c8["stages_passed"], c8["checks_passed"], c8["checks_failed"]) == (3, 5, 1)

    p = c8["physical"]
    assert p["run_id"] == ids[2] and p["pnr_iterations"] == 2
    assert (p["params_default"], p["params_final"]) == ({"FP_CORE_UTIL": 45}, {"FP_CORE_UTIL": 40})
    ppa = {r["metric"]: r for r in p["ppa"]}
    assert (ppa["Worst setup slack, post-route (P&R)"]["default"], ppa["Worst setup slack, post-route (P&R)"]["final"]) == (0.9, 0.8)
    assert (ppa["Worst hold slack, post-route (P&R)"]["default"], ppa["Worst hold slack, post-route (P&R)"]["final"]) == (-0.05, 0.02)
    assert (ppa["Utilization"]["default"], ppa["Wirelength"]["final"]) == (0.45, 1300)
    assert (ppa["P&R problems"]["default"], ppa["P&R problems"]["final"]) == (1, 0)
    assert ppa["Worst setup slack, signoff STA (9 corners)"]["final"] == 2.0
    assert ppa["Worst hold slack, signoff STA (9 corners)"]["final"] == 0.3
    assert ppa["Worst setup slack, signoff STA (9 corners)"]["default"] is None
    power = ppa["Power (tt_025C_1v80)"]
    assert power["final"] is None and power["final_why"] == "power not reported (power_tool.json missing)"
    assert p["readiness"] is None

    md = benchmark.markdown(report)
    assert "| rtl | – (stage not in any run of this design) |" in md
    assert "– (power not reported (power_tool.json missing))" in md
    assert "– (synthesis not reported (synth_tool.json missing))" in md
    assert "Tape-out readiness: – (tapeout_readiness.json missing" in md
    assert "claude-code-bridge 400 tok $0.0000 (estimated tokens, $0: coding-agent bridge)" in md
    assert "| Worst hold slack, post-route (P&R) | ns | -0.05 | 0.02 | pnr_iterations.json |" in md
    assert "debug rounds: main 2" in md and "2 P&R iteration(s)" in md
    assert "$0.0420" in md and "3,900" in md

    uart = by_name["uart"]
    assert uart["physical"] is None and uart["physical_why"] == "M0.7 not run"
    assert uart["stages"]["spec"]["wall_why"] == "running" and uart["wall_why"] == "no finished task"
    assert "PPA vs default flow: – (M0.7 not run)" in md
    assert "| uart (`" in md and "| – (M0.7 not run) | – (no finished task) | 0 | $0.0000 |" in md


def test_single_clean_iteration_is_not_a_comparison(platform, tmp_path, monkeypatch):
    art = tmp_path / "art"
    monkeypatch.setenv("S2S_ARTIFACT_DIR", str(art))
    with session() as s:
        d = new_design(s, "alu8")
        r = Run(id=new_id("run"), design_id=d.id, status="completed", stages=["place_route"], agent_kind="s2s")
        s.add(r)
        s.flush()
        rid = r.id
    rep = art / "runs" / rid / "reports"
    rep.mkdir(parents=True)
    (rep / "pnr_iterations.json").write_text(json.dumps([{"iteration": 1, "params": {}, "problems": [],
                                                          "facts": {"setup_ws_by_corner": {"a": 1.0}}}]))
    with session() as s:
        report = benchmark.build(s, art)
    row = next(x for x in report["designs"][0]["physical"]["ppa"] if x["metric"].startswith("Worst setup slack, post"))
    assert (row["default"], row["final"]) == (None, 1.0)
    assert row["default_why"] == "no change from defaults (first iteration clean)"
    assert "| – (no change from defaults (first iteration clean)) | 1.0 |" in benchmark.markdown(report)
