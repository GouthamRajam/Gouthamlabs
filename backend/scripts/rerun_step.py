"""Re-run ONE named step of a finished M0.7 task in the orchestrator's step context (events, checks and artifacts are
recorded on that task as in a normal run). Used when a new permanent check is added to an existing step, e.g. the
OCV-derated STA in signoff/chronos (CEO decision 2026-10-07). No other step runs; the signed tape-out package
(tapeout/) is not touched. Model calls go through the Claude Code bridge.

Usage: S2S_ARTIFACT_DIR=<...>/var/artifacts python -m scripts.rerun_step <run_id> <stage> <step_name>
"""
from __future__ import annotations

import json
import sys

from sqlalchemy import select

from s2s.agents import m07
from s2s.agents.runtime import StepContext
from s2s.db.models import Task
from s2s.db.session import session
from s2s.models.gateway import BridgeProvider, ModelGateway

STAGES = {"signoff": m07.signoff_steps, "gdsii": m07.gdsii_steps, "place_route": m07.place_route_steps}


def rerun(run_id: str, stage: str, step: str) -> dict:
    steps = STAGES[stage]()
    idx = next(i for i, f in enumerate(steps) if f.__name__ == step)
    with session() as s:
        task = s.scalars(select(Task).where(Task.run_id == run_id, Task.stage == stage)).one()
        assert task.status == "completed", f"{stage} task {task.id} is {task.status}"
        ctx = StepContext(session=s, task=task, state={}, gateway=ModelGateway(BridgeProvider()), step_index=idx,
                          step_count=len(steps))
        ctx.emit("plan", f"{task.agent_id}: re-run of step '{step}' only (new permanent check, decision 2026-10-07); "
                 "no other step runs and the signed package is not touched", agent_id=task.agent_id)
        steps[idx](ctx)
        return {"run": run_id, "stage": stage, "step": step, "blocked": ctx.state.get("blocked"),
                "checks": len(ctx.state.get("checks_run", []))}


if __name__ == "__main__":
    print(json.dumps(rerun(*sys.argv[1:4])))
