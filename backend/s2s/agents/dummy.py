"""Dummy agent (M0.3): exercises the platform with realistic event sequences, no real work.

Nothing it reports is a real tool result: every tool_result/check carries
`"simulated": true` and every summary it writes starts with "[dummy]" (MASTER_SPEC Part 12:
demo output is clearly labeled and never presented as real). Its model calls go through the
real gateway + meter (to the dummy model), so metering is exercised for real.

Behavior knobs come from task.inputs["dummy"] (set when the run is created):
  step_delay_s      seconds each step "works" (default 0.2)
  hang              {"stage": <name>, "at_step": <i>, "seconds": <s>}: that step goes silent
                    (no heartbeat) for s seconds, to exercise the stall watchdog
  regression_failures  how many times verification's regression check fails before it
                    passes (default 3, which triggers the "same failure 3 times" escalation)
"""
from __future__ import annotations

import time

from s2s.agents.runtime import Agent, Step, StepContext
from s2s.db.models import Finding, Message, ResearchBrief, Task
from s2s.ids import new_id

TOOLS = {
    "spec": "kb_search", "architecture": "yosys_elab", "rtl": "verilator_lint",
    "test_build": "cocotb_sim", "verification": "cocotb_sim", "synthesis": "openlane_flow",
    "dft": "openlane_flow", "floorplan": "openlane_flow", "place_route": "openlane_flow",
    "signoff": "opensta", "gdsii": "klayout_drc",
}


def _opts(ctx: StepContext) -> dict:
    return (ctx.task.inputs or {}).get("dummy", {})


def _work(ctx: StepContext) -> None:
    o = _opts(ctx)
    hang = o.get("hang") or {}
    if hang.get("stage") == ctx.task.stage and int(hang.get("at_step", -1)) == ctx.step_index:
        time.sleep(float(hang["seconds"]))  # silent: no heartbeat until this step commits
    time.sleep(float(o.get("step_delay_s", 0.2)))


def plan(ctx: StepContext) -> None:
    t = ctx.task
    ctx.emit("agent.status", f"{t.agent_id} is thinking", status="thinking")
    text = ctx.model(f"Plan the task: {t.title}. Inputs: {sorted((t.inputs or {}).keys())}")
    _work(ctx)
    ctx.emit("plan", f"[dummy] {t.agent_id} plan: read inputs, {t.title.lower()}, run checks, report",
             detail={"model_reply": text, "simulated": True})


def research(ctx: StepContext) -> None:
    t = ctx.task
    _work(ctx)
    topic = f"Prior art for {(t.inputs or {}).get('design_name', 'this design')}"
    brief = ResearchBrief(id=new_id("brf"), author_agent="Lyra", topic=topic,
                          summary="[dummy] Two open designs with similar interfaces found; no IP conflicts.",
                          sources=[{"title": "[dummy] example source", "url": None}], confidence=0.5)
    ctx.session.add(brief)
    ctx.emit("research.brief", f"[dummy] Lyra: research brief '{topic}'", agent_id="Lyra",
             team="technical_research", detail={"brief_id": brief.id, "simulated": True})


def act(ctx: StepContext) -> None:
    t = ctx.task
    tool = TOOLS[t.stage]
    ctx.emit("agent.status", f"{t.agent_id} is working", status="working")
    ctx.emit("tool_call", f"[dummy] {t.agent_id} runs {tool}", detail={"tool": tool, "simulated": True})
    _work(ctx)
    ctx.compute(tool, cpu_seconds=1.5)
    ctx.emit("tool_result", f"[dummy] {tool} finished: 0 errors (simulated)",
             detail={"tool": tool, "metrics": {"errors": 0}, "simulated": True})
    ctx.evidence = f"{tool} ran: 0 errors (simulated)"


def write_artifact(ctx: StepContext) -> None:
    t = ctx.task
    _work(ctx)
    content = (f"# [dummy] {t.stage} output for run {t.run_id}\n"
               f"# written by {t.agent_id}; not a real design artifact\n").encode()
    ctx.state["artifact"] = ctx.artifact(f"{t.stage}_output", f"{t.stage}/output.txt", content)


def check(ctx: StepContext) -> None:
    t = ctx.task
    _work(ctx)
    ctx.check(f"{t.stage}_checks", TOOLS[t.stage], True, {"errors": 0, "simulated": True},
              command=f"[dummy] {TOOLS[t.stage]}")
    ctx.evidence = f"{t.stage}_checks passed (simulated)"


def regression(ctx: StepContext) -> None:
    """Verification closure: the regression fails N times (debugged in between), then passes."""
    attempt = ctx.state.get("regression_attempt", 0) + 1
    ctx.state["regression_attempt"] = attempt
    fails = int(_opts(ctx).get("regression_failures", 3))
    passed = attempt > fails
    _work(ctx)
    ctx.emit("tool_call", f"[dummy] regression attempt {attempt}", detail={"tool": "cocotb_sim",
                                                                           "simulated": True})
    ctx.compute("cocotb_sim", cpu_seconds=3.0)
    metrics = {"tests": 42, "failed": 0 if passed else 1, "seed": 7731, "simulated": True}
    ctx.emit("tool_result", f"[dummy] regression: {42 - metrics['failed']}/42 pass", detail={
        "tool": "cocotb_sim", "metrics": metrics, "simulated": True})
    ctx.check("regression", "cocotb_sim", passed, metrics, command="[dummy] cocotb regression")
    ctx.evidence = f"regression attempt {attempt}: {42 - metrics['failed']}/42 tests pass (simulated)"


def review_and_handoff(ctx: StepContext) -> None:
    t = ctx.task
    _work(ctx)
    f = Finding(id=new_id("fnd"), run_id=t.run_id, from_agent="Sentinel", severity="minor",
                target_artifact=ctx.state.get("artifact"), location="rtl/output.txt:1",
                text="[dummy] Reset polarity not documented in header comment")
    ctx.session.add(f)
    ctx.emit("finding", "[dummy] Sentinel: reset polarity not documented", agent_id="Sentinel",
             team="independent_review", to_agent_id=t.agent_id,
             detail={"finding_id": f.id, "severity": "minor", "simulated": True})
    ctx.session.add(Message(id=new_id("msg"), run_id=t.run_id, type="handoff", from_agent=t.agent_id,
                            to_agent="Vera", payload={"artifact": ctx.state.get("artifact")}))
    ctx.emit("handoff", f"[dummy] {t.agent_id} hands RTL interface notes to Vera", to_agent_id="Vera",
             detail={"artifact": ctx.state.get("artifact"), "simulated": True})


def report(ctx: StepContext) -> None:
    t = ctx.task
    ctx.emit("agent.status", f"{t.agent_id} is reviewing", status="reviewing")
    ctx.model(f"Summarize the results of: {t.title}")
    _work(ctx)
    ctx.evidence = "report written"


class DummyAgent(Agent):
    def steps(self, task: Task) -> list[Step]:
        steps: list[Step] = [plan]
        if task.stage == "spec":
            steps.append(research)
        steps += [act, write_artifact]
        if task.stage == "verification":
            fails = int((task.inputs or {}).get("dummy", {}).get("regression_failures", 3))
            steps += [regression] * (fails + 1)
        else:
            steps.append(check)
        if task.stage == "rtl":
            steps.append(review_and_handoff)
        steps.append(report)
        return steps
