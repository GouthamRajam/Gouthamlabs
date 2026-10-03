"""Live tests: run every adapter against the real tools in the s2s-eda image.

Needs docker + the s2s-eda image. Without them these tests are skipped, unless
S2S_REQUIRE_EDA=1 (set in CI), which turns a missing EDA environment into a failure.
The OpenLane full-flow cases take minutes each and run only with S2S_RUN_SLOW=1.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from s2s.tools import runner
from s2s.tools.base import ToolSpec
from s2s.tools.result import ParsedLog
from tests.cases import CASES

pytestmark = pytest.mark.eda


@pytest.fixture(scope="module", autouse=True)
def eda_available():
    try:
        runner.image_id()
    except runner.EdaUnavailable as e:
        if os.environ.get("S2S_REQUIRE_EDA") == "1":
            pytest.fail(f"S2S_REQUIRE_EDA=1 but the EDA environment is unavailable: {e}")
        pytest.skip(f"EDA environment unavailable: {e}")


def _slow_ok():
    return os.environ.get("S2S_RUN_SLOW") == "1"


@pytest.mark.parametrize(
    "case",
    [pytest.param(c, marks=[pytest.mark.slow] if c.slow else []) for c in CASES],
    ids=lambda c: c.id,
)
def test_live_case(case, tmp_path):
    if case.slow and not _slow_ok():
        pytest.skip("slow OpenLane run; set S2S_RUN_SLOW=1")
    r = case.run(tmp_path)
    assert r.passed is case.expect_pass, (r.status, r.reasons, r.log_path)
    assert r.log_path and Path(r.log_path).is_file()
    assert r.command and r.tool_version and r.env_hash.startswith("sha256:")


def test_acceptance_2_verilator_width_mismatch_live(tmp_path):
    """verilator_lint on a file with a known width mismatch: FAIL, correct file and line."""
    from s2s.tools.verilator_lint import run_verilator_lint
    from tests.cases import FIX
    src = tmp_path / "width_mismatch.v"
    src.write_text((FIX / "rtl" / "width_mismatch.v").read_text())
    r = run_verilator_lint([src], "width_mismatch", tmp_path)
    assert r.status == "FAIL" and not r.passed
    [w] = [i for i in r.warnings if i.rule == "WIDTHTRUNC"]
    assert w.file == str(src) and w.line == 9


@pytest.mark.slow
def test_acceptance_3_openlane_spm_metrics_live(tmp_path):
    """openlane_flow on spm returns final WNS, DRC counts and LVS status."""
    if not _slow_ok():
        pytest.skip("slow OpenLane run; set S2S_RUN_SLOW=1")
    from tests.cases import CASES as ALL
    [case] = [c for c in ALL if c.id == "openlane_flow/pass"]
    r = case.run(tmp_path)
    m = r.metrics
    assert r.passed, r.reasons
    assert isinstance(m["wns"], float)
    assert m["magic_drc"] == 0 and m["klayout_drc"] == 0 and m["lvs_status"] == "match"


def test_timeout_is_reported_not_hung(tmp_path):
    spec = ToolSpec("sleep", "openlane", lambda log, rep: ParsedLog(success_marker=None))
    rec = runner.run(["sleep", "60"], tmp_path, tmp_path / "logs" / "sleep.log", spec.version_key,
                     timeout_s=3)
    assert rec.timed_out and rec.exit_code is None and rec.duration_s < 30
    from s2s.tools.base import finish
    r = finish(spec, rec)
    assert r.status == "TIMEOUT" and not r.passed


def test_missing_image_is_an_error_not_a_pass(tmp_path, monkeypatch):
    from s2s.tools import verilator_lint
    monkeypatch.setattr(runner, "IMAGE", "s2s-eda-does-not-exist")
    runner.image_id.cache_clear()
    try:
        src = tmp_path / "a.v"
        src.write_text("module a; endmodule\n")
        r = verilator_lint.run_verilator_lint([src], "a", tmp_path)
        assert r.status == "ERROR" and not r.passed and "could not be run" in r.reasons[0]
    finally:
        runner.image_id.cache_clear()
