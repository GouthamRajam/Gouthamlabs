"""Auto gates (gates.mode=auto) approve only if the LAST record of every check of the stage passed. This kept sync_fifo
change #2's G2 pending when a wrong resume skipped the mutation step after mutation_detection had failed
(2026-10-07, lesson s2s-ops-004)."""
from types import SimpleNamespace as NS

from s2s.orchestrator.engine import _stage_checks_ok


class _S:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self, _q):
        return NS(all=lambda: self.rows)


def _c(i, name, ok):
    return NS(id=f"chk_{i:03d}", check_name=name, passed=ok)


def test_a_failed_last_record_keeps_the_gate_pending():
    rows = [_c(1, "regression", True), _c(2, "mutation_detection", False), _c(3, "anti_cheat_final", True)]
    assert _stage_checks_ok(_S(rows), "t") is False


def test_a_rerun_that_passes_counts():
    rows = [_c(1, "mutation_detection", False), _c(2, "mutation_detection", True)]
    assert _stage_checks_ok(_S(rows), "t") is True


def test_no_checks_is_not_a_pass():
    assert _stage_checks_ok(_S([]), "t") is False
