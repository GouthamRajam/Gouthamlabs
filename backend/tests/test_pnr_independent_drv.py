"""Place-and-route DRV check is independent of OpenLane's metric (uart 2026-10-06: OpenLane's post-route STA reported
0 max-fanout violators; OpenSTA on the same routed netlist and SDC reported clkbuf_0_clk fanout 16 vs 10)."""
from pathlib import Path
from types import SimpleNamespace

from s2s.agents import m07
from s2s.tools.opensta import violator_pins

BLOCK = """max fanout

Pin                                   Limit Fanout  Slack
---------------------------------------------------------
clkbuf_0_clk/X                           10     16     -6 (VIOLATED)
clkbuf_4_15_0_clk/X                      10     11        (VIOLATED)
"""


def test_violator_rows_are_parsed():
    assert violator_pins(BLOCK) == [
        {"kind": "max fanout", "pin": "clkbuf_0_clk/X", "limit": 10.0, "value": 16.0},
        {"kind": "max fanout", "pin": "clkbuf_4_15_0_clk/X", "limit": 10.0, "value": 11.0}]
    assert violator_pins("max slew\n\nPin Limit Slew Slack\n") == []


def _ctx(tmp_path):
    return SimpleNamespace(workdir=tmp_path, emit=lambda *a, **k: None, beat=lambda *a, **k: None,
                           compute=lambda *a, **k: None)


NL = """  sky130_fd_sc_hd__clkbuf_16 clkbuf_0_clk (.A(clk), .X(clknet_0_clk));
  sky130_fd_sc_hd__clkbuf_8 clkbuf_4_15_0_clk (.A(clknet_0_clk), .X(clknet_4_15_0_clk));
  sky130_fd_sc_hd__dfxtp_1 _1_ (.CLK(clknet_4_15_0_clk), .D(a), .Q(b));
  sky130_fd_sc_hd__buf_2 fanout77 (.A(b), .X(net77));
  sky130_fd_sc_hd__nand2_1 _2_ (.A(net77), .B(c), .Y(d));
"""


def _drv(tmp_path, monkeypatch, status, pins, ol_count=None):
    nl = tmp_path / "x.nl.v"
    nl.write_text(NL)
    monkeypatch.setattr(m07, "run_opensta", lambda *a, **k: SimpleNamespace(
        status=status, metrics={"drv_violator_pins": pins}, log_path="l"))
    raw = sum(1 for v in pins or [] if v["kind"] == "max fanout") if ol_count is None else ol_count
    return m07._independent_drv(_ctx(tmp_path), {"views": {"nl": str(nl)},
                                                 "metrics": {"design__max_fanout_violation__count": raw}}, 1, "x")


def test_clock_tree_fanout_within_the_clock_rule_is_allowed(tmp_path, monkeypatch):
    p, f = _drv(tmp_path, monkeypatch, "FAIL", violator_pins(BLOCK))  # clock buffers at 16 and 11, rule 20
    assert p == [] and f["independent_drv_pins"] == []
    assert [v["pin"] for v in f["clock_rule_allowed"]] == ["clkbuf_0_clk/X", "clkbuf_4_15_0_clk/X"]


def test_clock_tree_fanout_above_the_clock_rule_and_data_fanout_are_problems(tmp_path, monkeypatch):
    pins = [{"kind": "max fanout", "pin": "clkbuf_0_clk/X", "limit": 10.0, "value": 21.0},
            {"kind": "max fanout", "pin": "fanout77/X", "limit": 10.0, "value": 11.0}]
    p, f = _drv(tmp_path, monkeypatch, "FAIL", pins)
    assert p == ["independent STA: max fanout clkbuf_0_clk/X 21 (limit 10)",
                 "independent STA: max fanout fanout77/X 11 (limit 10)"]


def test_openlane_and_s2s_fanout_counts_must_agree(tmp_path, monkeypatch):
    p, _ = _drv(tmp_path, monkeypatch, "FAIL", violator_pins(BLOCK), ol_count=0)
    assert any("counts disagree" in x for x in p)


def test_clean_run_adds_no_problem(tmp_path, monkeypatch):
    assert _drv(tmp_path, monkeypatch, "PASS", []) == ([], {"independent_drv_pins": [], "clock_rule_allowed": [],
                                                            "independent_drv_log": "l"})


def test_a_run_that_did_not_finish_is_a_problem_not_a_pass(tmp_path, monkeypatch):
    p, f = _drv(tmp_path, monkeypatch, "ERROR", None)
    assert p and f["independent_drv_pins"] is None


def test_missing_netlist_is_a_problem(tmp_path):
    p, _ = m07._independent_drv(_ctx(tmp_path), {"views": {}}, 1, "x")
    assert p == ["independent DRV check: routed netlist not found"]
