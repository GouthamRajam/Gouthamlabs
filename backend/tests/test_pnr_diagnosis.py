"""Diagnose before iterating (CEO 2026-10-06). uart iterations 2-3 changed CTS_SINK_CLUSTERING_SIZE although the CTS
log showed clustering was never applied (125 sinks) and the 11 loads were flip-flops; the loop now hands Orion those
facts and refuses changes the facts rule out. Log lines below are verbatim from the real runs."""
from s2s.agents import m07

UART_CTS = """[INFO CTS-0010]  Clock net "clk" has 125 sinks.
[INFO CTS-0028]  Total number of sinks: 125.
[INFO CTS-0029]  Sinks will be clustered in groups of up to 9 and with maximum cluster diameter of 15.0 um.
[INFO CTS-0032]  Stop criterion found. Max number of sinks is 15.
[INFO CTS-0017]     Max level of the clock tree: 4.
"""
SYNCFIFO_CTS = """[INFO CTS-0028]  Total number of sinks: 531.
[INFO CTS-0029]  Sinks will be clustered in groups of up to 9 and with maximum cluster diameter of 50.0 um.
[INFO CTS-0019]  Total number of sinks after clustering: 62.
"""
NL = """  sky130_fd_sc_hd__clkbuf_8 clkbuf_4_15_0_clk (.A(clknet_0_clk),
    .X(clknet_4_15_0_clk));
  sky130_fd_sc_hd__dfxtp_1 _1 (.CLK(clknet_4_15_0_clk), .D(a), .Q(b));
  sky130_fd_sc_hd__dfxtp_1 _2 (.CLK(clknet_4_15_0_clk), .D(c), .Q(d));
  sky130_fd_sc_hd__diode_2 ANT (.DIODE(clknet_4_15_0_clk));
"""
V = [{"kind": "max fanout", "pin": "clkbuf_4_15_0_clk/X", "limit": 10.0, "value": 11.0}]
DIAG = {"root_cause": "r", "evidence": ["e"], "why_this_parameter": "w"}


def _run(tmp_path, log):
    (tmp_path / "34-openroad-cts").mkdir()
    (tmp_path / "34-openroad-cts" / "openroad-cts.log").write_text(log)
    (tmp_path / "x.nl.v").write_text(NL)
    return m07.pnr_diagnosis(tmp_path, str(tmp_path / "x.nl.v"), V)


def test_facts_show_clustering_not_applied_and_what_the_buffer_drives(tmp_path):
    d = _run(tmp_path, UART_CTS)
    assert d["cts"] == {"sinks": 125, "clustering_applied": False, "sinks_after_clustering": None,
                        "htree_stop_max_sinks": 15, "levels": 4, "buffers": None}
    assert d["violators"][0]["clock_tree_level"] == 4
    assert d["violators"][0]["loads_by_cell"] == {"dfxtp_1": 2, "diode_2": 1}


def test_clustering_knob_refused_when_clustering_was_not_applied(tmp_path):
    d = _run(tmp_path, UART_CTS)
    bad = m07.diagnosis_refusals([{"param": "CTS_SINK_CLUSTERING_SIZE", "value": 9, "reason": "r"}], DIAG, d, [])
    assert bad and "NOT applied" in bad[0]
    assert m07.diagnosis_refusals([{"param": "PL_TARGET_DENSITY_PCT", "value": 60, "reason": "r"}], DIAG, d, []) == []


def test_clustering_knob_allowed_when_clustering_applied(tmp_path):
    d = _run(tmp_path, SYNCFIFO_CTS)
    assert d["cts"]["clustering_applied"] is True and d["cts"]["sinks_after_clustering"] == 62
    assert m07.diagnosis_refusals([{"param": "CTS_SINK_CLUSTERING_SIZE", "value": 9, "reason": "r"}], DIAG, d, []) == []


def test_change_without_a_diagnosis_is_refused():
    bad = m07.diagnosis_refusals([{"param": "FP_CORE_UTIL", "value": 40, "reason": "r"}],
                                 {"root_cause": "", "evidence": [], "why_this_parameter": ""}, {}, [])
    assert bad and "diagnose first" in bad[0]
    assert m07.diagnosis_refusals([], {"root_cause": "", "evidence": [], "why_this_parameter": ""}, {}, []) == []


def test_parameter_that_left_problems_identical_is_refused():
    table = [{"problems": ["p"], "changes": []},
             {"problems": ["p"], "changes": [{"param": "CTS_SINK_CLUSTERING_SIZE", "value": 10, "reason": "r"}]}]
    bad = m07.diagnosis_refusals([{"param": "CTS_SINK_CLUSTERING_SIZE", "value": 9, "reason": "r"}], DIAG, {}, table)
    assert bad and "identical" in bad[0]
