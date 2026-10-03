"""Every adapter's parser + pass/fail decision, checked against real recorded tool logs.

M0.2 acceptance test 1: each adapter has unit tests on at least one passing and one
failing golden log.
"""
from __future__ import annotations

import pytest

from tests.golden_util import TOOLS, all_goldens

GOLDENS = all_goldens()


def test_every_adapter_has_a_real_passing_and_failing_golden():
    for tool in TOOLS:
        cases = [g for g in GOLDENS if g.tool == tool]
        assert any(g.expect_pass for g in cases), f"{tool}: no passing golden log"
        assert any(not g.expect_pass for g in cases), f"{tool}: no failing golden log"


@pytest.mark.parametrize("g", GOLDENS, ids=lambda g: g.id)
def test_golden_verdict(g):
    r = g.evaluate()
    assert r.passed is g.expect_pass, r.reasons
    if g.expect_pass:
        assert r.reasons == [] and r.error_count == 0 and r.safety_net_hits == []
    else:
        assert r.reasons, "a failing golden must say why it failed"


@pytest.mark.parametrize("g", GOLDENS, ids=lambda g: g.id)
def test_golden_matches_the_live_run(g):
    """Parsing the stored log gives exactly what the live adapter reported when captured."""
    r = g.evaluate()
    live = g.meta["live_result"]
    assert r.status == live["status"]
    assert r.reasons == live["reasons"]
    assert r.error_count == live["error_count"]
    assert r.warning_count == live["warning_count"]


@pytest.mark.parametrize("g", GOLDENS, ids=lambda g: g.id)
def test_golden_records_how_it_was_produced(g):
    m = g.meta
    assert m["command"] and m["tool_version"] and m["env_hash"].startswith("sha256:")
    assert isinstance(m["exit_code"], int) and m["timed_out"] is False
