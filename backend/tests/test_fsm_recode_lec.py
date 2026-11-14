"""Re-encoded FSMs in the LEC fallback (uart 2026-10-06: Yosys fsm_recode turned u_uart_tx.state_q from 3-bit binary
into 5-bit one-hot, so name correspondence left 19 points unproven). The map is read from the real synthesis log;
the IDLE bit was merged with the FSM output tx_ready."""
from pathlib import Path

from s2s.physical import signoff

FIX = Path(__file__).parent / "platform" / "lec_fixtures" / "uart"


def test_recoding_is_read_from_the_synthesis_log():
    recs = signoff.fsm_recodings((FIX / "yosys-synthesis.log").read_text())
    assert [(r["signal"], r["module"], r["width"]) for r in recs] == [("u_uart_tx.state_q", "uart_top", 5)]
    assert recs[0]["map"] == [("000", "00001"), ("100", "00010"), ("010", "00100"), ("001", "01000"), ("011", "10000")]
    assert recs[0]["outputs"] == ["tx_ready"]


def test_alias_uses_named_bits_and_the_merged_output():
    recs = signoff.fsm_recodings((FIX / "yosys-synthesis.log").read_text())
    alias, problems = signoff.fsm_state_aliases((FIX / "uart_top.nl.v").read_text(), recs)
    assert problems == []
    assert "{ \\u_uart_tx.state_q[4]  , \\u_uart_tx.state_q[3]  , \\u_uart_tx.state_q[2]  , \\u_uart_tx.state_q[1]  , tx_ready }" in alias


def test_unresolvable_bit_is_reported_not_guessed():
    recs = [{"signal": "s", "module": "m", "width": 2, "map": [("0", "01"), ("1", "10")], "outputs": ["a", "b"]}]
    nl = "  wire \\s[1] ;\n  dfxtp x (.Q(a));\n  dfxtp y (.Q(b));\n"
    alias, problems = signoff.fsm_state_aliases(nl, recs)
    assert alias == "" and problems and "s[0]" in problems[0]


def test_no_synthesis_log_means_no_recoding(tmp_path):
    (tmp_path / "x.nl.v").write_text("module x; endmodule\n")
    assert signoff.find_synth_log(tmp_path / "x.nl.v") is None
    assert signoff.find_synth_log(FIX / "uart_top.nl.v") == (FIX / "yosys-synthesis.log").resolve()


def test_merged_bit_is_found_through_output_buffers():
    """Routed netlist: dfxtp _1288_ .Q(net42) -> buf_1 output42 .X(tx_ready)."""
    recs = signoff.fsm_recodings((FIX / "yosys-synthesis.log").read_text())
    alias, problems = signoff.fsm_state_aliases((FIX / "uart_top.final.nl.v").read_text(), recs)
    assert problems == [] and alias.rstrip().endswith(", net42 };")


def test_inverting_cell_is_not_followed():
    nl = "  dfxtp f (.Q(n1));\n  sky130_fd_sc_hd__inv_1 i (.A(n1), .Y(o));\n  sky130_fd_sc_hd__buf_1 b (.A(n2), .X(p));\n  dfxtp g (.Q(n2));\n"
    assert signoff._flop_q_through_buffers(nl, "o") is None
    assert signoff._flop_q_through_buffers(nl, "p") == "n2"
