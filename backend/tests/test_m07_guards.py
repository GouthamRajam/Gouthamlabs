"""M0.7 deterministic guards, offline (no tools, no model): pnr_ranges enforcement, the OpenLane config
guard, Sienna's SDC guard, Grid's pin file checks, DEF/skew parsers and the Part 22 readiness score."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from s2s.physical import flow as olf, readiness

SPEC = {"clocks": [{"name": "clk", "freq_mhz": 100}],
        "interfaces": [{"name": "clk", "dir": "in", "width": 1}, {"name": "rst_n", "dir": "in", "width": 1},
                       {"name": "d", "dir": "in", "width": 2}, {"name": "q", "dir": "out", "width": 2}]}
GOOD_SDC = """create_clock -name clk -period 10.0 [get_ports {clk}]
set_clock_uncertainty 0.25 [get_clocks clk]
set_max_fanout 10 [current_design]
# DEFAULT: 30% of the period
set_input_delay 3.0 -clock clk [get_ports {rst_n}]
set_input_delay 3.0 -clock clk [get_ports {d[0] d[1]}]
set_output_delay 3.0 -clock clk [get_ports {q[*]}]
"""


def sdc(text):
    bits, ins, outs = olf.port_bits(SPEC)
    return olf.sdc_problems(text, clocks=SPEC["clocks"], inputs=ins, outputs=outs)[0]


def test_sdc_guard_accepts_the_contract():
    assert sdc(GOOD_SDC) == []


@pytest.mark.parametrize("change,expect", [
    (("-period 10.0", "-period 12.5"), "period 12.5 ns != spec 10.0"),            # loosened clock
    (("set_clock_uncertainty 0.25", "set_clock_uncertainty 0.05"), "outside pnr_ranges"),
    (("set_max_fanout 10", "set_max_fanout 40"), "max fanout 40"),
    (("set_output_delay 3.0 -clock clk [get_ports {q[*]}]\n", ""), "no output delay on port q"),
    (("set_input_delay 3.0 -clock clk [get_ports {rst_n}]", "set_input_delay 11.0 -clock clk [get_ports {rst_n}]"),
     "not within [0, clock period)"),
])
def test_sdc_guard_refuses_loosening(change, expect):
    p = sdc(GOOD_SDC.replace(*change))
    assert any(expect in x for x in p), p


def test_sdc_exception_needs_written_justification():
    assert any("JUSTIFICATION" in x for x in sdc(GOOD_SDC + "set_false_path -from [get_ports rst_n]\n"))
    assert sdc(GOOD_SDC + "# JUSTIFICATION: rst_n is a quasi-static test input\nset_false_path -from [get_ports rst_n]\n") == []


def test_params_must_stay_inside_pnr_ranges():
    assert olf.check_params(olf.default_params()) == []
    assert olf.default_params() == {"FP_CORE_UTIL": 45, "PL_TARGET_DENSITY_PCT": 55, "MAX_FANOUT_CONSTRAINT": 10,
                                    # repair-effort settings default to OpenLane's own defaults
                                    "CTS_SINK_CLUSTERING_SIZE": 25, "GRT_ANTENNA_ITERS": 3, "GRT_ANTENNA_MARGIN": 10,
                                    # clock-tree shape settings (D1) default to OpenLane 2.3.10's defaults
                                    "CTS_SINK_CLUSTERING_MAX_DIAMETER": 50, "CTS_DISTANCE_BETWEEN_BUFFERS": 0,
                                    "CTS_CLK_MAX_WIRE_LENGTH": 0}
    assert olf.check_params({"CTS_SINK_CLUSTERING_MAX_DIAMETER": 80})  # wider clusters than the default: refused
    assert olf.check_params({"CTS_DISTANCE_BETWEEN_BUFFERS": -5})
    assert olf.check_params({"CTS_CLK_MAX_WIRE_LENGTH": 900})
    assert olf.check_params({"CTS_SINK_CLUSTERING_SIZE": 30})  # larger clusters than OpenLane's default: refused
    assert olf.check_params({"GRT_ANTENNA_ITERS": 2})          # less repair effort than the default: refused
    assert olf.check_params({"GRT_ANTENNA_MARGIN": 5})
    assert olf.check_params({"GRT_ANTENNA_ITERS": 10.5})       # whole numbers only
    assert olf.check_params({"FP_CORE_UTIL": 70})          # above 65
    assert olf.check_params({"PL_TARGET_DENSITY_PCT": 30})  # below 0.40 x 100
    assert olf.check_params({"MAX_FANOUT_CONSTRAINT": 5})
    assert olf.check_params({"RUN_KLAYOUT_DRC": False})    # not a tunable at all


def _pnr(tmp_path: Path) -> tuple[Path, dict, str]:
    pnr = tmp_path / "pnr"
    pnr.mkdir()
    rtl = tmp_path / "top.v"
    rtl.write_text("module top(input clk); endmodule\n")
    s = tmp_path / "c.sdc"
    s.write_text(GOOD_SDC)
    olf.write_config(pnr, "top", [rtl], "clk", 10.0, s, olf.default_params(), None)
    return pnr, {"top.v": olf.sha(rtl)}, olf.sha(s)


def test_config_guard_passes_the_runtime_config(tmp_path):
    pnr, frozen, sdc_sha = _pnr(tmp_path)
    assert olf.config_guard(pnr, period_ns=10.0, reviewed_sdc_sha=sdc_sha, frozen_rtl=frozen) == []


@pytest.mark.parametrize("edit,expect", [
    (lambda c: c.update(RUN_KLAYOUT_DRC=False), "outside the allowed set"),           # switching a check off
    (lambda c: c.update(QUIT_ON_MAGIC_DRC=False), "outside the allowed set"),
    (lambda c: c.update(FP_CORE_UTIL=80), "outside config/pnr_ranges.yaml"),
    (lambda c: c.update(CLOCK_PERIOD=12.0), "spec period"),
    (lambda c: c.update(ERRORS_ON_UNMATCHED_IO="none"), "must stay 'both'"),
])
def test_config_guard_refuses(tmp_path, edit, expect):
    pnr, frozen, sdc_sha = _pnr(tmp_path)
    cfg = json.loads((pnr / "config.json").read_text())
    edit(cfg)
    (pnr / "config.json").write_text(json.dumps(cfg))
    p = olf.config_guard(pnr, period_ns=10.0, reviewed_sdc_sha=sdc_sha, frozen_rtl=frozen)
    assert any(expect in x for x in p), p


def test_config_guard_detects_changed_sdc_and_rtl(tmp_path):
    pnr, frozen, sdc_sha = _pnr(tmp_path)
    (pnr / "src/constraints.sdc").write_text(GOOD_SDC.replace("10.0", "20.0"))
    (pnr / "src/top.v").write_text("module top(input clk); wire x; endmodule\n")
    p = olf.config_guard(pnr, period_ns=10.0, reviewed_sdc_sha=sdc_sha, frozen_rtl=frozen)
    assert any("Sentinel reviewed" in x for x in p) and any("G2-frozen" in x for x in p), p


def test_pin_file_checks():
    bits, _, _ = olf.port_bits(SPEC)
    assert bits == ["clk", "rst_n", "d[0]", "d[1]", "q[0]", "q[1]"]
    good = "#W\nclk\nrst_n\nd.*\n#E\nq\\[[0-1]\\]\n"
    assert olf.pin_cfg_problems(good, bits) == []
    assert any("not matched" in x for x in olf.pin_cfg_problems("#W\nclk\n#E\nq.*\n", bits))
    assert any("several sides" in x for x in olf.pin_cfg_problems(good + "#N\nd\\[0\\]\n", bits))
    assert any("matches no pin" in x for x in olf.pin_cfg_problems(good + "#S\nnope\n", bits))
    assert olf.pin_side_of("q[1]", olf.pin_cfg_sides(good)) == ["E"]


def test_skew_excludes_sdc_uncertainty():
    rpt = "Clock clk\n0.297047 source latency _130_/CLK ^\n-0.295581 target latency _131_/CLK ^\n" \
          "0.250000 clock uncertainty\n0.000000 CRPR\n--------------\n0.251466 setup skew\n"
    assert olf.parse_skew(rpt)["tree_skew_ns"] == pytest.approx(0.001466)


def test_readiness_scores_follow_part22():
    clean = {k: {"result": "clean", "tool": "t", "evidence": "e"} for k in readiness.CAPS}
    for k in ("signal_integrity", "reliability", "foundry_signoff"):
        clean[k] = {"result": "not run", "tool": "-", "evidence": ""}
    clean["dft_atpg"] = {"result": "not run", "tool": "plan", "evidence": "dft_plan_complete"}
    r = readiness.score(clean)
    # weights sum to 106; A excludes the three n/a checks (9) -> 97; ir (4) earns ir_em 0.5 = 2, dft (5) is
    # deferred and earns 0 -> (97 - 2 - 5) / 97 = 92.78 -> 92.7 (floored, never rounded up)
    assert r["weights_total"] == 106 and r["weights_A_total"] == 97 and r["earned_A_total"] == 90
    assert r["baseline_A_pct"] == 92.7 and r["partial_credit"] == {"dft": 0.0, "ir_em": 0.5, "other": 0.5}
    # B over 106: full 44 (sim, cov, formal, antenna, density, gds) + partial drc 7 + lvs 7 + sta 6 + power 2 + ir 2
    # = 68 -> 64.15 -> 64.1
    assert r["weights_B_total"] == 106 and r["baseline_B_pct"] == 64.1
    scope = {x["check"]: x["scope"] for x in r["rows"]}
    assert scope["dft_atpg"] == readiness.DFT_DEFERRED and scope["ir_em_static"] == "measured: passed, tool-limited"
    assert scope["signal_integrity"].startswith("excluded from Baseline A") and scope["drc"] == "measured: passed"
    worse = dict(clean, drc={"result": "failed", "tool": "t", "evidence": "e"})
    assert readiness.score(worse)["baseline_A_pct"] < r["baseline_A_pct"]
    assert "ASSUMPTIONS" in readiness.markdown("x", r, {})
    assert any(g["check"].startswith("DRC") for g in r["gaps"])  # partial in B is listed as a gap
