"""Tool-specific facts each parser must extract from the real golden logs."""
from __future__ import annotations

from tests.golden_util import load


def _by_rule(issues, rule):
    return [i for i in issues if i.rule == rule]


# --- verilator_lint ---------------------------------------------------------------------
def test_verilator_width_mismatch_reports_file_and_line():
    """Acceptance test 2 (on the recorded log): FAIL with the correct file and line."""
    r = load("verilator_lint", "fail_width_mismatch").evaluate()
    assert r.status == "FAIL"
    [w] = _by_rule(r.warnings, "WIDTHTRUNC")
    assert w.file.endswith("width_mismatch.v") and w.line == 9
    assert "expects 8 bits" in w.message and "generates 9 bits" in w.message


def test_verilator_syntax_error_location():
    r = load("verilator_lint", "fail_syntax_error").evaluate()
    located = [e for e in r.errors if e.file]
    assert located[0].file.endswith("syntax_error.v") and located[0].line == 7


def test_verilator_clean_lint():
    r = load("verilator_lint", "pass").evaluate()
    assert r.passed and r.metrics == {"errors": 0, "warnings": 0}


# --- yosys_elab ---------------------------------------------------------------------------
def test_yosys_latch_is_a_failure_even_though_yosys_exits_0():
    g = load("yosys_elab", "fail_latch")
    assert g.meta["exit_code"] == 0
    r = g.evaluate()
    assert not r.passed and r.metrics["latches"] == 1
    [latch] = _by_rule(r.warnings, "latch")
    assert latch.file.endswith("/latch.v") and latch.line == 7


def test_yosys_logic_loop():
    r = load("yosys_elab", "fail_comb_loop").evaluate()
    assert r.metrics["logic_loops"] == 1 and any("Found 1 problems" in e.message for e in r.errors)


def test_yosys_syntax_error_location():
    r = load("yosys_elab", "fail_syntax_error").evaluate()
    assert r.errors[0].file.endswith("/syntax_error.v") and r.errors[0].line == 7


def test_yosys_clean():
    r = load("yosys_elab", "pass").evaluate()
    assert r.metrics == {"latches": 0, "logic_loops": 0, "check_problems": 0}


# --- cocotb_sim ---------------------------------------------------------------------------
def test_cocotb_verilator_pass_with_seed_and_coverage():
    r = load("cocotb_sim", "pass_verilator").evaluate()
    m = r.metrics
    assert (m["tests"], m["passed"], m["failed"], m["seed"]) == (1, 1, 0, 1234)
    assert m["lines_found"] > 0 and 0 < m["line_coverage"] <= 1


def test_cocotb_failures_name_the_test():
    for case in ("fail_verilator", "fail_icarus"):
        r = load("cocotb_sim", case).evaluate()
        assert r.metrics["failed"] == 1 and r.metrics["seed"] == 1234
        [e] = r.errors
        assert "counts_up_wrong_expectation" in e.message and "count=5" in e.message


def test_cocotb_icarus_pass():
    r = load("cocotb_sim", "pass_icarus").evaluate()
    assert r.passed and r.metrics["tests"] == 1 and r.metrics["line_coverage"] is None


# --- sby_formal ---------------------------------------------------------------------------
def test_sby_pass_lists_proven_property():
    m = load("sby_formal", "pass").evaluate().metrics
    assert m["status"] == "PASS" and m["proven"] == 1 and m["failed"] == 0
    assert m["counterexample_vcd"] == []


def test_sby_fail_gives_property_location_and_counterexample():
    r = load("sby_formal", "fail_assertion").evaluate()
    m = r.metrics
    assert m["status"] == "FAIL" and m["failed"] == 1
    assert m["properties"][0]["location"].startswith("counter_formal.v:18")
    assert m["counterexample_vcd"] == ["counter_fail/engine_0/trace.vcd"]
    assert m["induction_trace_vcd"] == ["counter_fail/engine_0/trace_induct.vcd"]
    [e] = r.errors  # the same assertion is not double-counted for the induction trace
    assert e.file == "counter_formal.v" and e.line == 18


# --- eqy ----------------------------------------------------------------------------------
def test_eqy_pass_and_fail():
    ok = load("eqy", "pass").evaluate().metrics
    bad = load("eqy", "fail_not_equivalent").evaluate().metrics
    assert ok["equivalent"] is True and ok["partitions_proven"] == ["adder.s"]
    assert bad["equivalent"] is False and bad["partitions_failed"] == ["adder.s"]


# --- opensta ------------------------------------------------------------------------------
def test_opensta_met_timing():
    m = load("opensta", "pass").evaluate().metrics
    assert m["corner"] == "tt_025C_1v80"
    assert m["wns"] == 0.0 and m["setup_worst_slack"] > 0 and m["hold_worst_slack"] > 0
    assert m["worst_paths"] and all(p["state"] == "MET" for p in m["worst_paths"])


def test_opensta_setup_violation():
    r = load("opensta", "fail_setup").evaluate()
    m = r.metrics
    assert m["wns"] == m["setup_worst_slack"] < 0 and m["tns"] < 0
    assert m["violated_paths_reported"] > 0
    assert _by_rule(r.errors, "setup_violation")


# --- magic_drc / klayout_drc ---------------------------------------------------------------
def test_magic_drc_counts_by_rule():
    assert load("magic_drc", "pass").evaluate().metrics == {"drc_violations": 0, "by_rule": {}}
    m = load("magic_drc", "fail_met1_width").evaluate().metrics
    assert m["drc_violations"] == 3
    assert m["by_rule"] == {"Metal1 width < 0.14um (met1.1)": 2,
                            "Metal1 minimum area < 0.083um^2 (met1.6)": 1}


def test_klayout_drc_counts_by_rule():
    assert load("klayout_drc", "pass").evaluate().metrics == {"drc_violations": 0, "by_rule": {}}
    m = load("klayout_drc", "fail_met1_width").evaluate().metrics
    assert m == {"drc_violations": 3, "by_rule": {"m1.1": 2, "m1.6": 1}}


# --- netgen_lvs ---------------------------------------------------------------------------
def test_netgen_lvs_match():
    m = load("netgen_lvs", "pass").evaluate().metrics
    assert m["lvs_status"] == "match" and m["verdict"] == "Circuits match uniquely"
    assert m["counts"] == {"devices": {"layout": 330, "schematic": 330},
                           "nets": {"layout": 359, "schematic": 359}}


def test_netgen_lvs_mismatch():
    r = load("netgen_lvs", "fail_miswired").evaluate()
    assert r.metrics["lvs_status"] == "mismatch"
    assert r.metrics["verdict"] == "Netlists do not match"
    assert _by_rule(r.errors, "lvs_mismatch")


# --- openlane_flow ------------------------------------------------------------------------
def test_openlane_spm_pass_metrics():
    """Acceptance test 3 (on the recorded run): final WNS, DRC counts and LVS status."""
    r = load("openlane_flow", "pass").evaluate()
    m = r.metrics
    assert r.passed
    assert isinstance(m["wns"], float) and m["wns"] >= 0
    assert m["magic_drc"] == 0 and m["klayout_drc"] == 0 and m["route_drc"] == 0
    assert m["lvs_errors"] == 0 and m["lvs_status"] == "match"
    assert m["steps_run"] > 50 and all(s["status"] == "ran" for s in m["steps"])


def test_openlane_timing_failure():
    r = load("openlane_flow", "fail_timing").evaluate()
    m = r.metrics
    assert r.exit_code != 0 and m["wns"] < 0 and m["hold_wns"] < 0
    assert any(s["step"] == "Checker.SetupViolations" and s["status"] == "failed" for s in m["steps"])
    assert any("Setup violations" in e.message for e in r.errors)
