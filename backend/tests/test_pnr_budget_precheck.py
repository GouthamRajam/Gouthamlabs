"""Phase 1 harness #1: a P&R iteration starts only if all of its tool runs can finish and be evaluated before the
tool-run hard stop (sync_fifo 2026-10-07: 14 of 16 used could not fit a 4-run placement iteration; 18 of 20 could not
fit a 2-run routing iteration)."""
import json
from types import SimpleNamespace as NS

import pytest

from s2s.agents import m07
from s2s.finance import meter


def test_runs_per_iteration():
    assert m07.pnr_iteration_runs("placement") == 4   # placement, cts, routing + independent DRV check
    assert m07.pnr_iteration_runs("cts") == 3
    assert m07.pnr_iteration_runs("routing") == 2


@pytest.mark.parametrize("used,limit,need,fits", [
    (14, 16, 4, False),   # sync_fifo it5 as first proposed: would stop after CTS
    (14, 16, 2, False),   # even routing-only: the DRV check reaches 16 and is stopped before evaluation
    (18, 20, 2, False),   # after it5
    (14, 20, 4, True),    # the raise to 20 that ran it5
    (0, 16, 4, True),
])
def test_iteration_fits_matches_the_hard_stop(used, limit, need, fits):
    assert meter.iteration_fits(used, limit, need) is fits


class _Ctx:
    def __init__(self, workdir):
        self.workdir = workdir
        self.task = NS(id="task_x", budget={"max_tool_runs": 16}, agent_id="Orion")
        self.state, self.checks, self.events = {}, [], []

    def check(self, name, tool, passed, metrics, command="", **kw):
        self.checks.append((name, passed, metrics))
        return passed

    def emit(self, type, summary, **kw):
        self.events.append((type, summary, kw.get("detail")))


def test_loop_refuses_an_iteration_that_cannot_finish(tmp_path, monkeypatch):
    (tmp_path / "pnr").mkdir()
    (tmp_path / "pnr/s2s_physical.json").write_text(json.dumps(
        {"iteration": 5, "tag": "it5", "start_stage": "placement", "params": {}}))
    monkeypatch.setattr(meter, "tool_runs_left", lambda tid, budget: (14, 16))
    monkeypatch.setattr(m07.olf, "run_stage", lambda *a, **k: pytest.fail("a tool was started"))
    monkeypatch.setattr(m07, "_who", lambda name: {"agent_id": name})
    ctx = _Ctx(tmp_path)
    pnr_loop = m07.place_route_steps()[0]
    pnr_loop(ctx)
    assert ctx.checks == [("pnr_iteration_fits_budget", False, {
        "iteration": 5, "start_stage": "placement", "runs_needed": 4, "tool_runs_used": 14, "tool_runs_limit": 16})]
    assert ctx.events[0][0] == "escalation" and ctx.events[0][2]["rule"] == "budget pre-check"
    assert "budget pre-check" in ctx.state["blocked"]
