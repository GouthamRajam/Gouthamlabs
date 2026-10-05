"""Formal harness: a k-induction STEP failure is not a real failure, and the per-property PDR proof keeps
exactly one assertion. Logs are real SymbiYosys output (spi_master M0.6 prove run; a PDR run on RTL broken
on purpose, done reset to 1)."""
from pathlib import Path

from s2s.verify.formal import _pdr_sby, _real_failures

G = Path(__file__).parent / "golden" / "formal_harness"


def test_induction_step_counterexample_is_not_a_failure():
    log = (G / "prove_induction_step_fail.log").read_text()
    assert "engine_0.induction: ##   0:00:05  Assert failed in formal_top: ap_sck_edges_max" in log
    assert "basecase: pass" in log
    assert _real_failures(log) == set()


def test_basecase_or_pdr_counterexample_is_a_failure():
    log = (G / "pdr_basecase_fail.log").read_text()
    assert _real_failures(log) == {"reset_values"}


def test_pdr_sby_keeps_one_assertion_and_the_assumptions(tmp_path):
    rtl = [tmp_path / "a.v"]
    props = tmp_path / "formal_top.sv"
    text = _pdr_sby("irq_next", rtl, props)
    assert "abc pdr" in text and "mode prove" in text
    assert "chformal -cover -remove" in text
    assert "chformal -assert -remove c:ap_* c:ap_irq_next %d" in text
    assert "assume" not in text  # assumptions are never removed or added
