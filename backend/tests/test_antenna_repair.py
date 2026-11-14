"""Tests for the post-detailed-route antenna repair module (P1.0A).

Tests the Tcl script generator and the log/report parser. Actual OpenROAD runs require the
s2s-eda environment (pytest.mark.eda)."""
from __future__ import annotations

from pathlib import Path

import pytest

from s2s.physical import antenna_repair as ar
from s2s.physical import dfm


class TestRepairTcl:
    def test_tcl_contains_read_db(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/before.rpt"), Path("/tmp/after.rpt"))
        assert "read_db /tmp/test.odb" in tcl

    def test_tcl_contains_check_antennas(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "check_antennas -verbose" in tcl

    def test_tcl_contains_diode_cell(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert ar.DIODE_CELL in tcl

    def test_tcl_contains_done_marker(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "S2S_ANT_REPAIR_DONE" in tcl

    def test_tcl_max_iterations_configurable(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"),
                            max_iterations=5)
        assert "$iter < 5" in tcl

    def test_tcl_contains_incremental_route(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "detailed_route" in tcl

    def test_tcl_contains_legalize(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "detailed_placement" in tcl

    def test_tcl_skip_when_no_violations(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "S2S_ANT_REPAIR_SKIP" in tcl

    def test_tcl_writes_repaired_odb(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"),
                            repaired_odb=Path("/tmp/repaired.odb"))
        assert "write_db /tmp/repaired.odb" in tcl

    def test_tcl_no_write_db_when_none(self):
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "write_db" not in tcl

    def test_tcl_no_explicit_lef_reads(self):
        """ODB already contains library cell definitions; no LEF needed."""
        tcl = ar.repair_tcl(Path("/tmp/test.odb"), Path("/tmp/b.rpt"), Path("/tmp/a.rpt"))
        assert "read_lef" not in tcl


class TestParseRepairLog:
    def test_clean_design_skipped(self):
        log = """\
[INFO] check_antennas
Found 0 net violations
Found 0 pin violations
S2S_ANT_BEFORE nets=0
S2S_ANT_REPAIR_SKIP no violations in report
S2S_ANT_REPAIR_DONE
"""
        r = ar.parse_repair_log(log)
        assert r["completed"] is True
        assert r["skipped"] is True
        assert r["before"] == {"nets": 0, "pins": 0}
        assert r["after"] == {"nets": 0, "pins": 0}
        assert r["diodes_inserted"] == 0
        assert r["iterations"] == 0

    def test_successful_repair(self):
        log = """\
Found 3 net violations
Found 5 pin violations
S2S_ANT_BEFORE nets=3
S2S_ANT_REPAIR_ITER 0
S2S_ANT_VIOL_PINS 5
S2S_ANT_INSERTED 5 diodes (total 5)
S2S_ANT_LEGALIZE ok
S2S_ANT_ROUTE ok
Found 1 net violations
Found 1 pin violations
S2S_ANT_AFTER_ITER0 remaining_nets=1
S2S_ANT_REPAIR_ITER 1
S2S_ANT_VIOL_PINS 1
S2S_ANT_INSERTED 1 diodes (total 6)
S2S_ANT_LEGALIZE ok
S2S_ANT_ROUTE ok
Found 0 net violations
Found 0 pin violations
S2S_ANT_AFTER_ITER1 remaining_nets=0
S2S_ANT_TOTAL_DIODES 6
Found 0 net violations
Found 0 pin violations
S2S_ANT_FINAL_CHECK done
S2S_ANT_REPAIR_DONE
"""
        r = ar.parse_repair_log(log)
        assert r["completed"] is True
        assert r["skipped"] is False
        assert r["before"] == {"nets": 3, "pins": 5}
        assert r["after"] == {"nets": 0, "pins": 0}
        assert r["diodes_inserted"] == 6
        assert r["iterations"] == 2

    def test_partial_repair(self):
        log = """\
Found 5 net violations
Found 8 pin violations
S2S_ANT_BEFORE nets=5
S2S_ANT_REPAIR_ITER 0
S2S_ANT_VIOL_PINS 8
S2S_ANT_INSERTED 8 diodes (total 8)
S2S_ANT_LEGALIZE ok
S2S_ANT_ROUTE ok
Found 2 net violations
Found 3 pin violations
S2S_ANT_AFTER_ITER0 remaining_nets=2
S2S_ANT_REPAIR_ITER 1
S2S_ANT_VIOL_PINS 3
S2S_ANT_INSERTED 3 diodes (total 11)
S2S_ANT_LEGALIZE ok
S2S_ANT_ROUTE ok
Found 1 net violations
Found 1 pin violations
S2S_ANT_AFTER_ITER1 remaining_nets=1
S2S_ANT_REPAIR_ITER 2
S2S_ANT_VIOL_PINS 1
S2S_ANT_INSERTED 1 diodes (total 12)
S2S_ANT_LEGALIZE ok
S2S_ANT_ROUTE ok
Found 1 net violations
Found 1 pin violations
S2S_ANT_AFTER_ITER2 remaining_nets=1
S2S_ANT_TOTAL_DIODES 12
Found 1 net violations
Found 1 pin violations
S2S_ANT_FINAL_CHECK done
S2S_ANT_REPAIR_DONE
"""
        r = ar.parse_repair_log(log)
        assert r["completed"] is True
        assert r["skipped"] is False
        assert r["before"] == {"nets": 5, "pins": 8}
        assert r["after"] == {"nets": 1, "pins": 1}
        assert r["diodes_inserted"] == 12
        assert r["iterations"] == 3

    def test_incomplete_run(self):
        log = """\
Found 2 net violations
Found 3 pin violations
S2S_ANT_BEFORE nets=2
S2S_ANT_REPAIR_ITER 0
"""
        r = ar.parse_repair_log(log)
        assert r["completed"] is False
        assert r["before"] == {"nets": 2, "pins": 3}
        assert r["after"] is None
        assert r["iterations"] == 1

    def test_no_insertion_possible(self):
        log = """\
Found 1 net violations
Found 1 pin violations
S2S_ANT_BEFORE nets=1
S2S_ANT_REPAIR_ITER 0
S2S_ANT_VIOL_PINS 1
S2S_ANT_WARN could not create diode instance S2S_ant_123_A_0
S2S_ANT_INSERTED 0 diodes (total 0)
S2S_ANT_WARN no diodes could be inserted, stopping
S2S_ANT_TOTAL_DIODES 0
Found 1 net violations
Found 1 pin violations
S2S_ANT_FINAL_CHECK done
S2S_ANT_REPAIR_DONE
"""
        r = ar.parse_repair_log(log)
        assert r["completed"] is True
        assert r["diodes_inserted"] == 0
        assert r["after"] == {"nets": 1, "pins": 1}


class TestParseAntennaVerboseIntegration:
    """Verify that the before/after reports produced by the repair script are parseable by
    dfm.parse_antenna_verbose (the same parser used throughout signoff)."""

    SAMPLE_REPORT = """\
Net: net34
  Pin: _1234_/A
  Layer: met1
  Partial area ratio: 410.75
  Required ratio: 400 (Side area)
Net: clk
  Pin: _5678_/CLK
  Layer: met1
  Cumulative area ratio: 350.00
  Required ratio: 400 (Cumulative area)
"""

    def test_parse_violations(self):
        items = dfm.parse_antenna_verbose(self.SAMPLE_REPORT)
        assert len(items) == 2
        assert items[0]["net"] == "net34"
        assert items[0]["pct_of_limit"] == pytest.approx(102.69, abs=0.01)
        assert items[1]["net"] == "clk"
        assert items[1]["pct_of_limit"] == pytest.approx(87.5, abs=0.01)

    def test_only_over_limit_are_violations(self):
        items = dfm.parse_antenna_verbose(self.SAMPLE_REPORT)
        over = [i for i in items if i["pct_of_limit"] >= 100]
        assert len(over) == 1
        assert over[0]["net"] == "net34"
