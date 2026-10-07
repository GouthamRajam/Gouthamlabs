"""Phase 1 harness #4: resume points are named steps; ambiguous or unknown names are refused."""
import pytest

from s2s.ops.jobs import ResumeRefused, resolve_step

NAMES = ["setup", "change_requests", "stop_if_blocked", "regress_debug", "stop_if_blocked", "cora", "stop_if_blocked",
         "myra", "stop_if_blocked", "anticheat", "report"]  # M0.6 verification


def test_unique_names_resolve():
    assert resolve_step(NAMES, "myra") == 7


def test_repeated_names_need_an_occurrence():
    with pytest.raises(ResumeRefused, match="4 steps are named 'stop_if_blocked'"):
        resolve_step(NAMES, "stop_if_blocked")
    assert resolve_step(NAMES, "stop_if_blocked#4") == 8
    with pytest.raises(ResumeRefused):
        resolve_step(NAMES, "stop_if_blocked#5")


def test_unknown_names_are_refused():
    with pytest.raises(ResumeRefused, match="no step named 'mutation'"):
        resolve_step(NAMES, "mutation")
