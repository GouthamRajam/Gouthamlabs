"""Formal harness parsing on real SymbiYosys logs (captured in the sync_fifo M0.6 run).

sby's end summary lists a few traces, then "and N further traces": per-property results must come
from the engine lines, or reachable covers look vacuous and design-dependent properties look like
tautologies (a harness bug found in the first real M0.6 runs)."""
from pathlib import Path

from s2s.verify.formal import _FAILED, _REACHED

G = Path(__file__).parent / "golden" / "formal_harness"


def test_every_reached_cover_is_found_despite_a_truncated_summary():
    log = (G / "cover_truncated_summary.log").read_text()
    assert "further traces" in log
    reached = set(_REACHED.findall(log))
    print(sorted(reached))
    assert len(reached) == log.count("Reached cover statement in step") and len(reached) >= 13
    assert {"full_decode", "count_le_16", "almost_full_decode"} <= reached


def test_every_failed_assertion_is_found_in_the_free_stub_run():
    log = (G / "free_truncated_summary.log").read_text()
    failed = set(_FAILED.findall(log))
    print(sorted(failed))
    engine = {ln.split("ap_")[1].split()[0] for ln in log.splitlines() if "Assert failed in formal_top: ap_" in ln}
    assert failed >= engine and len(engine) >= 5
