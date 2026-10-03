"""The failure-string safety net (MASTER_SPEC 8.2 #2).

M0.2 acceptance test 4: a deliberately corrupted log (error string present, exit code 0)
is reported as FAIL. The corruption is injected into every adapter's real PASSING log, in
a form that tool's parser does not count, so only the safety net can catch it.
"""
from __future__ import annotations

import pytest

from s2s.tools.result import ParsedLog
from s2s.trust.safety_net import decide
from tests.golden_util import all_goldens

PASSING = [g for g in all_goldens() if g.expect_pass]

# One failure string per tool that the tool's own parser does NOT count (it is in the wrong
# place or shape for the parser's grammar), plus a generic crash string for every tool.
UNCOUNTED = {
    "verilator_lint": "Internal Error: V3Ast.cpp:123: Broken link in node",
    "yosys_elab": "  abc: ERROR: Assert `cell != nullptr' failed",
    "cocotb_sim": "child process ERROR in simulator, results may be incomplete",
    "sby_formal": "SBY 8:00:00 [x] engine_1: DONE (ERROR, rc=16)",
    "eqy": "EQY 8:00:00 [x] Failed to prove equivalence (partition list truncated)",
    "opensta": "read_spef: cannot open 'spm.nom.spef', continuing without parasitics",
    "magic_drc": "Error while reading cell \"sky130_fd_sc_hd__dfrtp_1\" (byte offset 1234)",
    "klayout_drc": "ERROR: Layer 68/20 could not be evaluated",
    "netgen_lvs": "Subcircuit pins do not match for cell spm",
    "openlane_flow": "One or more deferred errors were encountered (flow aborted)",
}
GENERIC = "Segmentation fault (core dumped)"


def inject(log: str, line: str) -> str:
    """Insert `line` in the middle of the log (where a mid-run failure would appear)."""
    lines = log.splitlines()
    return "\n".join(lines[: len(lines) // 2] + [line] + lines[len(lines) // 2:])


@pytest.mark.parametrize("g", PASSING, ids=lambda g: g.id)
@pytest.mark.parametrize("which", ["tool_specific", "generic_crash"])
def test_corrupted_passing_log_with_exit_0_is_FAIL(g, which):
    injected = UNCOUNTED[g.tool] if which == "tool_specific" else GENERIC
    corrupted = inject(g.log, injected)

    clean = g.evaluate()
    assert clean.passed, "precondition: the untouched golden log passes"

    r = g.evaluate(log=corrupted, exit_code=0)
    assert r.passed is False and r.status == "FAIL"
    assert any(injected.strip() in h for h in r.safety_net_hits)
    if r.error_count == clean.error_count:  # parser did not count it: the safety net caught it
        assert any("parser did not count" in reason for reason in r.reasons), r.reasons


def test_tool_specific_injections_really_are_uncounted_by_their_parsers():
    """Guard for the test above: every injected string really slips past its tool's parser,
    so the FAIL comes from the safety net alone (the case the spec worries about)."""
    counted_by_parser = []
    for g in PASSING:
        r = g.evaluate(log=inject(g.log, UNCOUNTED[g.tool]), exit_code=0)
        if r.error_count == g.evaluate().error_count:
            assert any("parser did not count" in reason for reason in r.reasons)
        else:
            counted_by_parser.append(g.id)
    assert counted_by_parser == []


@pytest.mark.parametrize("g", [g for g in PASSING if g.spec.parse(g.log, g.reports).success_marker],
                         ids=lambda g: g.id)
def test_truncated_log_without_success_marker_is_FAIL(g):
    """A run that died half-way (exit 0, no error string) fails on the missing success marker."""
    lines = g.log.splitlines()
    for keep in (len(lines) // 2, len(lines) // 4):
        truncated = "\n".join(lines[:keep])
        if not g.spec.parse(truncated, g.reports).success_marker:
            r = g.evaluate(log=truncated, exit_code=0)
            assert not r.passed and any("success marker" in x for x in r.reasons)
            return
    pytest.skip("success marker is not in the log body for this tool (comes from a report)")


# --- decide() rules in isolation ------------------------------------------------------------
def test_all_clean_passes():
    d = decide(0, False, ParsedLog(success_marker=True), "all good\n")
    assert d.passed and d.status == "PASS" and d.reasons == []


def test_nonzero_exit_fails_even_with_clean_parse():
    d = decide(1, False, ParsedLog(success_marker=True), "all good\n")
    assert not d.passed and d.reasons == ["tool exit code 1 (must be 0)"]


def test_parser_errors_fail_even_with_exit_0():
    from s2s.tools.result import Issue
    d = decide(0, False, ParsedLog(errors=[Issue("error", "x")], success_marker=True), "x\n")
    assert not d.passed and "parser counted 1 error(s)" in d.reasons


def test_stage_rule_fails():
    d = decide(0, False, ParsedLog(stage_failures=["latch inferred"], success_marker=True), "")
    assert not d.passed and d.reasons == ["stage rule: latch inferred"]


def test_timeout_is_its_own_status():
    d = decide(None, True, ParsedLog(), "")
    assert not d.passed and d.status == "TIMEOUT"


def test_failure_string_uncounted_by_parser_fails():
    d = decide(0, False, ParsedLog(success_marker=True), "ok\nTraceback (most recent call last):\n")
    assert not d.passed and "parser did not count" in d.reasons[0]


def test_tool_specific_pattern():
    d = decide(0, False, ParsedLog(success_marker=None), "x\n%Error: boom\n", [r"(?m)^%Error"])
    assert not d.passed and d.hits == ["%Error: boom"]
