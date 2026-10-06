"""uart 2026-10-06: an SDC comment containing 'set_propagated_clock' made OpenLane skip clock propagation, so every
OpenLane timing step and repair after CTS ran on an ideal clock (clock-net fanout unchecked, latency ignored). The
SDC guard refuses the word anywhere; the P&R loop fails an iteration whose post-route STA left a clock ideal."""
from types import SimpleNamespace

from s2s.agents import m07
from s2s.physical import flow as olf

SDC = """create_clock -name clk -period 20.000 [get_ports {clk}]
set_clock_uncertainty 0.25 [get_clocks {clk}]
set_max_fanout 10 [current_design]
"""


def _p(text):
    return [p for p in olf.sdc_problems(text, clocks=[{"name": "clk", "freq_mhz": 50}], inputs=[], outputs=[])[0]
            if "propagated_clock" in p]


def test_word_in_a_comment_is_refused():
    bad = _p(SDC + "# set_propagated_clock is intentionally not set (the flow propagates clocks after CTS).\n")
    assert bad and "line 4" in bad[0]
    assert _p(SDC + "# clocks become propagated after CTS (done by the flow)\n") == []


def test_unpropagated_clock_after_route_is_reported(tmp_path):
    d = tmp_path / "54-openroad-stapostpnr"
    for c, txt in (("nom_tt_025C_1v80", "clk\n"), ("nom_ss_100C_1v60", "clk\n"), ("nom_ff_n40C_1v95", "")):
        (d / c).mkdir(parents=True)
        (d / c / "unpropagated.rpt").write_text(txt)
    assert m07.unpropagated_clocks(tmp_path) == {"clk": ["nom_ss_100C_1v60", "nom_tt_025C_1v80"]}


def test_comment_only_rewrite_keeps_every_command(tmp_path, monkeypatch):
    (tmp_path / "constraints").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/sdc_before.sdc").write_text(SDC + "# set_propagated_clock note\n")
    ctx = SimpleNamespace(workdir=tmp_path, task=SimpleNamespace(inputs={"sdc_keep_commands_from": "reports/sdc_before.sdc"}))
    monkeypatch.setattr(m07, "_spec", lambda c: {})
    monkeypatch.setattr(m07, "_clocks", lambda c: [{"name": "clk", "freq_mhz": 50}])
    monkeypatch.setattr(m07.olf, "port_bits", lambda spec: (None, [], []))
    monkeypatch.setattr(m07, "_check", lambda *a, **k: None)
    (tmp_path / "constraints/constraints.sdc").write_text(SDC + "# clocks are propagated by the flow after CTS\n")
    assert m07.validate_sdc(ctx) == []
    (tmp_path / "constraints/constraints.sdc").write_text(SDC.replace("0.25", "0.30") + "# comment\n")
    assert any("only comments may change" in p for p in m07.validate_sdc(ctx))
