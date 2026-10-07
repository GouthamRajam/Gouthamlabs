"""Agent definitions and one model call per agent action (MASTER_SPEC Part 7.4, Appendix A.0/A.20).

Each agent is `agents/defs/<name>.yaml` + a prompt in `agents/prompts/`. The system prompt is
the shared preamble (A.0, with the A3 additions for design-organization engineers) followed by
the role prompt; the task envelope (A.20) and the input files go in the user message.

The runtime enforces the definition:
- reads_from: an agent is only given input files whose paths match its reads_from globs;
- writes_to: a file the agent returns outside its writes_to globs is rejected (never written);
- effort / max_tokens / model_hint: passed to the model gateway, which meters every call under
  the agent's name and checks the spend caps first.

Every call emits events: agent.status (thinking), tool_call (the model call), tool_result
(tokens, cost, latency) and the agent's own plan.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from s2s.org import load_org

DEFS_DIR = Path(__file__).parent / "defs"
PROMPTS_DIR = Path(__file__).parent / "prompts"


class OutsideAllowedPaths(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentDef:
    id: str
    name: str
    role: str
    prompt: str
    preamble: str = "design"
    stages: tuple = ()
    model_hint: str = "default"
    effort: str | None = None
    max_tokens: int = 16000
    tools: tuple = ()
    budget: dict = field(default_factory=dict)
    writes_to: tuple = ()
    reads_from: tuple = ()
    team_focus: str | None = None
    runtime: str | None = None
    prompt_vars: dict = field(default_factory=dict)  # fills a template prompt (director/manager templates)

    @property
    def team(self) -> str | None:
        u = load_org().team_of_agent(self.name)
        return u.id if u else None


@lru_cache(maxsize=None)
def agent(name: str) -> AgentDef:
    d = yaml.safe_load((DEFS_DIR / f"{name}.yaml").read_text())
    for k in ("stages", "tools", "writes_to", "reads_from"):
        d[k] = tuple(d.get(k) or ())
    return AgentDef(**d)


def _prompt(name: str) -> str:
    text = (PROMPTS_DIR / name).read_text()
    return "\n".join(ln for ln in text.splitlines() if not ln.startswith("<!--")).strip()


def system_prompt(a: AgentDef) -> str:
    parts = []
    if a.preamble == "design":
        parts.append(_prompt("A.0_preamble.md").replace("{name}", a.name).replace("{role}", a.role))
        parts.append("ADDITIONAL RULES (Appendix A3)\n" + _prompt("A3_preamble_additions.md"))
    text = _prompt(a.prompt)
    for k, v in a.prompt_vars.items():
        text = text.replace("{" + k + "}", v)
    parts.append(text)
    return "\n\n".join(parts)


def path_allowed(path: str, globs: tuple) -> bool:
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts:
        return False
    return any(fnmatch.fnmatchcase(path, g) or fnmatch.fnmatchcase(path, g.replace("/**", "/*/**"))
               for g in globs)


def envelope(*, task_id: str, stage: str, design: str, goal: str, inputs: dict[str, str],
             constraints: str, exit_criteria: list[str], budget: dict, allowed_write_paths: tuple,
             previous_attempts: str, relevant_knowledge: str) -> str:
    """Appendix A.20, filled in."""
    import hashlib
    listed = ", ".join(f"{p} (sha256:{hashlib.sha256(t.encode()).hexdigest()[:12]})" for p, t in inputs.items())
    return _prompt("A.20_task_envelope.md").format_map({
        "task_id": task_id, "stage": stage, "design_name": design, "goal": goal,
        "list of artifact paths and hashes": listed or "none",
        "constraints": constraints, "list": "; ".join(exit_criteria),
        "max_tokens": budget.get("max_tokens"), "max_minutes": budget.get("max_minutes"),
        "max_tool_runs": budget.get("max_tool_runs"), "paths": ", ".join(allowed_write_paths) or "none",
        "summary of earlier attempts and failures, if any": previous_attempts or "none",
        "top kb entries": relevant_knowledge,
    })


ANSWER_NOTE = (
    "ANSWER FORMAT\n"
    "Answer with one JSON object in the required schema. Its fields are your task.result (Appendix B.6): "
    "`plan` (your short plan, 1-3 sentences), `status`, `summary`, `assumptions`, `open_issues`, "
    "`self_assessment`. The runtime adds task_id, output hashes and the checks it ran. "
    "{extra}You cannot run tools yourself in this task: after you answer, the runtime runs the real "
    "checks and gives you their exact output if anything fails. Never claim a check passed."
)


def ask(ctx, a: AgentDef | str, *, goal: str, inputs: dict[str, str], exit_criteria: list[str],
        schema: dict, constraints: str = "", previous_attempts: str = "",
        relevant_knowledge: str = "none found", extra_note: str = "") -> dict[str, Any]:
    """One model call as agent `a` inside the current task step. Returns the parsed answer."""
    a = agent(a) if isinstance(a, str) else a
    for path in inputs:
        if not path_allowed(path, a.reads_from):
            raise OutsideAllowedPaths(f"{a.name} may not read {path} (reads_from: {list(a.reads_from)})")
    t = ctx.task
    env = envelope(task_id=t.id, stage=t.stage, design=t.inputs.get("design_name", ""), goal=goal,
                   inputs=inputs, constraints=constraints, exit_criteria=exit_criteria,
                   budget=a.budget, allowed_write_paths=a.writes_to,
                   previous_attempts=previous_attempts, relevant_knowledge=relevant_knowledge)
    if a.team_focus:
        env += f"\nteam_focus: {a.team_focus}"
    files = "\n\n".join(f"=== {p} ===\n{text}" for p, text in inputs.items())
    user = f"{env}\n\nINPUT FILES\n{files or '(none)'}\n\n{ANSWER_NOTE.format(extra=extra_note)}"
    who = dict(agent_id=a.name, team=a.team)
    ctx.emit("agent.status", f"{a.name} is thinking", status="thinking", **who)
    ctx.emit("tool_call", f"{a.name}: model call ({a.effort or 'default'} effort) - {goal[:120]}",
             status="thinking", detail={"tool": "model", "model_hint": a.model_hint, "effort": a.effort,
                                        "inputs": list(inputs)}, **who)
    system = system_prompt(a)
    goal_sha = hashlib.sha256(goal.encode()).hexdigest()[:16]
    attempt = 1 + sum(1 for c in ctx.state.get("model_calls", []) if c.get("agent") == a.name
                      and c.get("goal_sha") == goal_sha)
    r = ctx.gateway.complete(task=ctx.ref, system=system, messages=[{"role": "user", "content": user}],
                             max_tokens=a.max_tokens, model_hint=a.model_hint, output_schema=schema,
                             effort=a.effort, agent_id=a.name)
    ctx.emit("tool_result", f"{a.name}: model answered ({r.input_tokens} in / {r.output_tokens} out tokens, "
             f"${r.cost_usd:.4f}, {r.latency_ms} ms)", status="working",
             detail={"tool": "model", "model": r.model, "call_id": r.call_id, "input_tokens": r.input_tokens,
                     "output_tokens": r.output_tokens, "cost_usd": round(r.cost_usd, 6),
                     "latency_ms": r.latency_ms, "stop_reason": r.stop_reason, "attempt": attempt,
                     "answered_by": (r.provenance or {}).get("answered_by", r.model),
                     "operator_influenced": bool((r.provenance or {}).get("operator_influenced"))}, **who)
    data = r.data
    if data.get("plan"):
        ctx.emit("plan", f"{a.name}: {data['plan'][:300]}", detail={"plan": data["plan"]}, **who)
    ctx.state.setdefault("model_calls", []).append({"agent": a.name, "call_id": r.call_id, "cost_usd": r.cost_usd,
                                                     "goal_sha": goal_sha})
    _transcript(ctx, a, user, r, system=system, goal=goal, attempt=attempt, prior_feedback=previous_attempts)
    return data


TRANSCRIPT_SCHEMA = 2  # 1 = {task_id, agent, prompt, answer} (Phase 0); 2 adds the provenance below


def _transcript(ctx, a: AgentDef, prompt: str, r, *, system: str, goal: str, attempt: int,
                prior_feedback: str) -> None:
    """One model call, kept in the run folder (logs/model_calls.jsonl) as a training-grade record: the exact
    system prompt (stored once by hash in logs/system_prompts/), the user prompt, the answer, the model asked for and
    the model that actually answered, the attempt number and the feedback the earlier attempt got, and whether an
    operator note influenced it (Phase 1 trajectory item 3/4)."""
    logs = ctx.workdir / "logs"
    sp = logs / "system_prompts"
    sp.mkdir(parents=True, exist_ok=True)
    sys_sha = hashlib.sha256(system.encode()).hexdigest()
    if not (sp / f"{sys_sha}.txt").exists():
        (sp / f"{sys_sha}.txt").write_text(system)
    prov = dict(r.provenance or {})
    rec = {"schema": TRANSCRIPT_SCHEMA, "ts": dt.datetime.now(dt.timezone.utc).isoformat(), "call_id": r.call_id,
           "task_id": ctx.task.id, "run_id": ctx.task.run_id, "step_index": ctx.step_index, "agent": a.name,
           "goal": goal, "attempt": attempt, "prior_feedback": prior_feedback or None,
           "model_hint": a.model_hint, "effort": a.effort, "model": r.model,
           "answered_by": prov.get("answered_by", r.model), "operator_influenced": bool(prov.get("operator_influenced")),
           "provenance": prov, "system_sha256": sys_sha, "input_tokens": r.input_tokens,
           "output_tokens": r.output_tokens, "latency_ms": r.latency_ms, "stop_reason": r.stop_reason,
           "prompt": prompt, "answer": r.text}
    with (logs / "model_calls.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")
