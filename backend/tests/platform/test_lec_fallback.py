"""Equivalence when eqy cannot prove a design (sync_fifo: eqy's partitioning errors on the count/memory
partitions): the Yosys LEC fallback proves the real netlist and still rejects a changed RTL."""
import shutil
from pathlib import Path

import pytest

from s2s.physical import signoff
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
