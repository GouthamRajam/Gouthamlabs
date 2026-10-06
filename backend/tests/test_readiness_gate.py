"""Part 22 readiness after the 2026-10-06 decision: the Phase 0 gate is the hard checks (pass/fail) plus scope
labels; the percentages are derived and carry their partial-credit values. DFT never earns headline credit
unless a fault coverage was actually measured (a DFT plan is not a measurement)."""
import json

import pytest
import yaml

from s2s.config import CONFIG_DIR
from s2s.physical import readiness

HARD_OK = {k: True for k in ("drc", "lvs", "antenna", "timing", "equivalence")}


def _all_clean(**over):
    r = {k: {"result": "clean", "tool": "t", "evidence": "e"} for k in readiness.CAPS}
    for k in ("signal_integrity", "reliability", "foundry_signoff"):
        r[k] = {"result": "not run", "tool": "-", "evidence": ""}
    r.update(over)
    return r


def _dft(rep):
    return next(x for x in rep["rows"] if x["check"] == "dft_atpg")


@pytest.fixture
def dft_half(tmp_path, monkeypatch):
    """A config that would give DFT 0.5: the measurement rule must still hold."""
    cfg = yaml.safe_load((CONFIG_DIR / "readiness.yaml").read_text())
    cfg["partial_credit"]["dft"] = 0.5
    p = tmp_path / "readiness.yaml"
    p.write_text(yaml.safe_dump(cfg))
    monkeypatch.setenv("S2S_READINESS_CONFIG", str(p))


@pytest.mark.parametrize("claimed", ["clean", "partial", "not run"])
def test_dft_without_measured_fault_coverage_earns_nothing(claimed):
    rep = readiness.score(_all_clean(dft_atpg={"result": claimed, "tool": "plan", "evidence": "dft_plan_complete"}))
    d = _dft(rep)
    assert d["result"] == "deferred" and d["earned_A"] == 0 and d["earned_B"] == 0
    assert d["scope"] == readiness.DFT_DEFERRED
    assert rep["baseline_A_pct"] == 92.7  # 90 / 97: DFT stays in the denominator at 0


@pytest.mark.parametrize("claimed", ["clean", "partial"])
def test_dft_earns_nothing_unmeasured_even_if_config_allows_credit(dft_half, claimed):
    rep = readiness.score(_all_clean(dft_atpg={"result": claimed, "tool": "plan", "evidence": "e"}))
    assert _dft(rep)["earned_A"] == 0 and rep["baseline_A_pct"] == 92.7
    measured = readiness.score(_all_clean(dft_atpg={"result": "clean", "tool": "Fault", "evidence": "atpg",
                                                    "fault_coverage_pct": 96.0}))
    assert _dft(measured)["earned_A"] == 2.5  # credit only once a fault coverage exists


def _reports(tmp_path, allowed=()):
    pv = {"magic_drc": {"violations": 0}, "klayout_drc": {"violations": 0},
          "lvs": {"verdict": "Circuits match uniquely", "counts": {"devices": {"layout": 684}, "nets": {"layout": 723}}},
          "antenna": {"net_violations": 0, "pin_violations": 0, "nets_checked": 692}}
    corners = {c: {"setup_ws_ns": s, "setup_tns_ns": 0.0, "hold_ws_ns": h, "hold_tns_ns": 0.0, "passed": True,
                   "clock_rule_allowed": list(allowed)}
               for c, s, h in (("max_ss_100C_1v60", 8.9381, 0.8688), ("min_ff_n40C_1v95", 9.789, 0.104))}
    (tmp_path / "pv_signoff.json").write_text(json.dumps(pv))
    (tmp_path / "sta_signoff.json").write_text(json.dumps({"corners": corners}))
    return tmp_path


CLK = [{"kind": "max fanout", "pin": f"clkbuf_3_{i}__f_clk/X", "limit": 10.0, "value": v,
        "rule": "clock-tree net, limit 20"} for i, v in enumerate((17.0, 11.0))]


def test_hard_checks_are_the_gate(tmp_path):
    h = readiness.hard_checks(HARD_OK, {}, _reports(tmp_path))
    assert h["verdict"] == "PASS" and (h["passed"], h["of"]) == (5, 5) and not h["conditions"]
    t = next(i for i in h["items"] if i["check"].startswith("Timing"))
    assert "worst setup +8.9381 ns (max_ss_100C_1v60)" in t["detail"] and "worst hold +0.104 ns" in t["detail"]
    assert readiness.hard_checks(dict(HARD_OK, lvs=False), {}, _reports(tmp_path))["verdict"] == "FAIL"


def test_human_edits_is_never_an_automatic_pass(tmp_path):
    h = readiness.hard_checks(HARD_OK, {}, _reports(tmp_path))
    e = next(i for i in h["items"] if i["check"] == "No human edits to artifacts")
    assert e["status"] == "NOT CHECKED" and e["passed"] is None and "no automated edit-detection" in e["detail"]


def test_clock_rule_pass_is_conditional_and_says_what_a_flat_limit_does(tmp_path):
    h = readiness.hard_checks(HARD_OK, {}, _reports(tmp_path, CLK))
    assert h["verdict"] == "CONDITIONAL PASS"
    assert next(i for i in h["items"] if i["check"].startswith("Timing"))["status"] == "PASS (conditional)"
    c = h["conditions"][0]
    assert "limit of 20" in c and "2 clock-tree buffer outputs have fanout 11-17" in c
    assert "Under a flat SDC max-fanout limit of 10 this design FAILS" in c


def test_report_leads_with_hard_checks_and_discloses_partial_values(tmp_path):
    rep = readiness.score(_all_clean(), readiness.hard_checks(HARD_OK, {}, _reports(tmp_path, CLK)))
    md = readiness.markdown("x", rep, {})
    assert md.index("Hard checks: CONDITIONAL PASS") < md.index("Baseline A (open shuttle): 92.7%")
    assert "dft=0 / ir_em=0.5" in md and "A = 90 / 97" in md and "weights total 106" in md
    assert md.index("FAILS") < md.index("## Derived score")
    assert readiness.DFT_DEFERRED in md and "measured: passed, tool-limited" in md
