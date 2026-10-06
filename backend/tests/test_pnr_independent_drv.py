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


def _drv(tmp_path, monkeypatch, status, pins):
    nl = tmp_path / "x.nl.v"
    nl.write_text("module x; endmodule\n")
    monkeypatch.setattr(m07, "run_opensta", lambda *a, **k: SimpleNamespace(
        status=status, metrics={"drv_violator_pins": pins}, log_path="l"))
    return m07._independent_drv(_ctx(tmp_path), {"views": {"nl": str(nl)}}, 1, "x")


def test_violators_from_the_independent_run_are_problems(tmp_path, monkeypatch):
    p, f = _drv(tmp_path, monkeypatch, "FAIL", violator_pins(BLOCK))
    assert p == ["independent STA: max fanout clkbuf_0_clk/X 16 (limit 10)",
                 "independent STA: max fanout clkbuf_4_15_0_clk/X 11 (limit 10)"]
    assert len(f["independent_drv_pins"]) == 2


def test_clean_run_adds_no_problem(tmp_path, monkeypatch):
    assert _drv(tmp_path, monkeypatch, "PASS", []) == ([], {"independent_drv_pins": [], "independent_drv_log": "l"})


def test_a_run_that_did_not_finish_is_a_problem_not_a_pass(tmp_path, monkeypatch):
    p, f = _drv(tmp_path, monkeypatch, "ERROR", None)
    assert p and f["independent_drv_pins"] is None


def test_missing_netlist_is_a_problem(tmp_path):
    p, _ = m07._independent_drv(_ctx(tmp_path), {"views": {}}, 1, "x")
    assert p == ["independent DRV check: routed netlist not found"]
