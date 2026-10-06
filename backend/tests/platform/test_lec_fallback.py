"""Equivalence when eqy cannot prove a design (sync_fifo: eqy's partitioning errors on the count/memory
partitions): the Yosys LEC fallback proves the real netlist and still rejects a changed RTL."""
import shutil
from pathlib import Path

import pytest

from s2s.physical import signoff
from s2s.tools.result import ToolResult
from tests.platform.test_m05_offline import eda_available

pytestmark = [pytest.mark.skipif(not eda_available(), reason="s2s-eda image not built"), pytest.mark.slow]
FIX = Path(__file__).parent / "lec_fixtures" / "sync_fifo"


def _setup(tmp_path):
    shutil.copytree(FIX, tmp_path / "d")
    (tmp_path / "d" / "logs").mkdir()
    return tmp_path / "d"


def test_lec_proves_the_synthesized_netlist(tmp_path):
    d = _setup(tmp_path)
    r = signoff.equivalence(sorted((d / "rtl").glob("*.v")), d / "sync_fifo.nl.v", "sync_fifo", d, "t")
    assert r.passed and r.metrics["lec_points_unproven"] == 0 and r.metrics["lec_points_proven"] > 500
    assert r.metrics["method"].startswith(("eqy", "yosys LEC"))


def test_lec_rejects_a_changed_rtl(tmp_path):
    d = _setup(tmp_path)
    ctrl = d / "rtl" / "fifo_ctrl.v"
    ctrl.write_text(ctrl.read_text().replace("count_q >= AF_TH", "count_q > AF_TH"))
    r = signoff.equivalence(sorted((d / "rtl").glob("*.v")), d / "sync_fifo.nl.v", "sync_fifo", d, "t")
    assert not r.passed and r.metrics["lec_points_unproven"] >= 1


UART = Path(__file__).parent / "lec_fixtures" / "uart"


def _uart_lec(tmp_path, mutant=None):
    """The LEC fallback directly on the uart fixture (eqy's own 1800 s attempt is not what is tested here)."""
    shutil.copytree(UART, tmp_path / "d")
    d = tmp_path / "d"
    (d / "logs").mkdir()
    if mutant:  # e.g. uart_tx_L153_stuck_bit_2.v replaces rtl/uart_tx.v
        shutil.copy2(d / "mutants" / mutant, d / "rtl" / (mutant.split("_L")[0] + ".v"))
    pdk = d / "formal_pdk.v"
    rec = signoff.runner.run(["eqy.formal_pdk_proc", "--output", str(pdk), *signoff.CELL_MODELS], d,
                             d / "logs" / "pdk.log", "eqy", 600)
    assert rec.exit_code == 0
    base = ToolResult(tool="eqy", passed=False, status="FAIL", exit_code=1, timed_out=False, error_count=0,
                      warning_count=0, errors=[], warnings=[], stage_failures=[],
                      metrics={"status": "FAIL", "partitions_proven": [], "partitions_failed": []},
                      reasons=["eqy not run"], safety_net_hits=[], log_path=None, report_paths={}, command=[],
                      tool_version=None, env_hash=None, duration_s=None)
    return signoff._lec_fallback(base, sorted((d / "rtl").glob("*.v")), pdk, d / "uart_top.nl.v", "uart_top", d,
                                 "t", d)


def test_lec_proves_a_recoded_fsm_with_the_synthesis_map(tmp_path):
    r = _uart_lec(tmp_path)
    assert r.passed and r.metrics["lec_points_unproven"] == 0 and r.metrics["lec_points_proven"] >= 125
    assert r.metrics["fsm_recoded"] == ["u_uart_tx.state_q"] and "encfile" in r.metrics["method"]


@pytest.mark.parametrize("mutant", ["uart_tx_L153_stuck_bit_2.v", "uart_tx_L56_dropped_handshake_3.v",
                                    "uart_rx_L113_swapped_condition_2.v"])
def test_lec_with_fsm_map_still_rejects_real_bugs(tmp_path, mutant):
    r = _uart_lec(tmp_path, mutant)
    assert not r.passed and r.metrics["lec_points_unproven"] >= 1
