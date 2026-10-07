"""Model gateway (MASTER_SPEC Part 7.3).

Providers:
- DummyProvider (M0.3): no network call, deterministic text, token counts from text lengths
  (~4 characters per token). Used by the dummy agent.
- ScriptedProvider (tests): returns queued responses; no network call. Used to test the M0.5
  agent plumbing offline without spending money. Never used by a real run.
- AnthropicProvider (Part 28, M0.5): the provider, key and endpoint saved in Settings -> Model
  access (s2s.models.access, an encrypted server-side secret, read on every call so a replaced key
  applies at once). Every agent uses the default model (claude-sonnet-5-5).

M0.5 additions:
- `output_schema`: the response must be one JSON object matching a JSON Schema (Messages API
  structured outputs, `output_config.format`). The gateway parses it and returns `.data`.
- `effort`: thinking depth (`output_config.effort`), set per agent in agents/defs.
- `agent_id`: the agent the call is charged to when one task uses several agents (e.g. Sentinel
  reviewing inside Iris's spec task): metered under that agent, on the same task and run.
- A refusal (`stop_reason == "refusal"`) or a truncated structured answer (`max_tokens`) raises
  ModelOutputError after the call is metered; the task fails visibly. No server-side fallback to
  another model is configured (see docs/DECISIONS.md, M0.5).

Before every call the spend caps (finance.yaml spend_caps) are checked; a reached cap raises
meter.SpendCapReached and no call is made. Every call is metered (usage_records row with cost,
committed) before the response is returned.

The dummy provider also appends each call to its own JSONL log (S2S_DUMMY_MODEL_CALL_LOG),
independent of metering, so tests can check that every call was metered.
"""
from __future__ import annotations

import dataclasses
import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from s2s.finance import meter
from s2s.models import access
from s2s.ids import new_id


@dataclass
class ModelResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    call_id: str
    data: Any = None  # the parsed JSON object when an output_schema was given
    stop_reason: str | None = None
    latency_ms: int = 0
    cost_usd: float = 0.0
    provenance: dict = field(default_factory=dict)  # who/what actually answered, attempts, operator influence


@dataclass
class ProviderReply:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None = None
    model: str | None = None  # the model that answered (defaults to the provider's model)
    provenance: dict = field(default_factory=dict)


class ModelOutputError(RuntimeError):
    """The model answered but the answer is unusable (refusal, cut off, not the schema)."""


def _tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class DummyProvider:
    model = "dummy-model"

    def complete(self, system: str, messages: list[dict], max_tokens: int, output_schema: dict | None = None,
                 effort: str | None = None) -> ProviderReply:
        prompt = system + "".join(str(m.get("content", "")) for m in messages)
        last = str(messages[-1].get("content", "")) if messages else ""
        text = f"[dummy-model] Acknowledged: {last[:160]}. Plan: read inputs, act, check, report."
        return ProviderReply(text, _tokens(prompt), min(max_tokens, _tokens(text)), "end_turn")


@dataclass
class ScriptedProvider:
    """Offline test double: each call pops the next queued reply (a dict is sent as JSON text,
    a callable is called with (system, messages) first). Priced like dummy-model."""
    replies: deque = field(default_factory=deque)
    calls: list = field(default_factory=list)
    model: str = "dummy-model"

    def complete(self, system: str, messages: list[dict], max_tokens: int, output_schema: dict | None = None,
                 effort: str | None = None) -> ProviderReply:
        self.calls.append({"system": system, "messages": messages, "schema": output_schema, "effort": effort})
        if not self.replies:
            raise AssertionError("ScriptedProvider: no reply queued for this call")
        r = self.replies.popleft()
        if callable(r):
            r = r(system, messages)
        text = r if isinstance(r, str) else json.dumps(r)
        prompt = system + "".join(str(m.get("content", "")) for m in messages)
        return ProviderReply(text, _tokens(prompt), _tokens(text), "end_turn")


class AnthropicProvider:
    """Calls the model configured in Settings -> Model access (key from the encrypted secret)."""

    @property
    def model(self) -> str:
        return access.load().get("model", access.DEFAULT_MODEL)

    def complete(self, system: str, messages: list[dict], max_tokens: int, output_schema: dict | None = None,
                 effort: str | None = None) -> ProviderReply:
        c, model = access.client()
        output_config: dict[str, Any] = {}
        if output_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": output_schema}
        if effort:
            output_config["effort"] = effort
        extra = {"output_config": output_config} if output_config else {}
        # Streamed so a long answer never hits the SDK's non-streaming timeout guard.
        with c.messages.stream(model=model, system=system, messages=messages, max_tokens=max_tokens,
                               **extra) as stream:
            r = stream.get_final_message()
        text = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
        return ProviderReply(text, r.usage.input_tokens, r.usage.output_tokens, r.stop_reason, r.model)


@dataclass
class BridgeProvider:
    """PERSONAL / LOCALHOST DEV MODE, approved by the CEO 2026-10-04 (env S2S_MODEL_PROVIDER=bridge;
    never a production path).

    Each call is handed to a Claude Code session instead of the API: the request is written to
    <bridge>/requests/<id>.json and this call waits for <bridge>/responses/<id>.json, written by a
    Claude Code subagent. The answer is checked against the schema here (one retry with the exact
    error). Metered with ESTIMATED tokens (~4 chars/token) under model "claude-code-bridge" at $0:
    the real cost is the Claude Code session's usage, which S2S cannot see, so the S2S spend caps do
    not limit bridge calls. Limits (docs/DECISIONS.md): a subagent has filesystem access, so the
    reads_from isolation is an instruction, not enforced.
    """
    root: str = field(default_factory=lambda: os.environ.get(
        "S2S_BRIDGE_DIR", str(Path(__file__).resolve().parents[3] / "var" / "bridge")))
    timeout_s: float = field(default_factory=lambda: float(os.environ.get("S2S_BRIDGE_TIMEOUT_S", "5400")))
    model: str = "claude-code-bridge"

    def complete(self, system: str, messages: list[dict], max_tokens: int, output_schema: dict | None = None,
                 effort: str | None = None) -> ProviderReply:
        root = Path(self.root)
        (root / "requests").mkdir(parents=True, exist_ok=True)
        (root / "responses").mkdir(parents=True, exist_ok=True)
        rid = new_id("br")
        prompt = system + "".join(str(m.get("content", "")) for m in messages)
        feedback, problem, attempts = "", None, []
        for attempt in (1, 2):
            req_id = rid if attempt == 1 else f"{rid}_retry"
            out = root / "responses" / f"{req_id}.json"
            req = {"id": req_id, "system": system, "messages": messages, "output_schema": output_schema,
                   "max_tokens": max_tokens, "effort": effort, "feedback": feedback, "response_path": str(out)}
            tmp = root / "requests" / f".{req_id}.tmp"
            tmp.write_text(json.dumps(req, indent=1))
            tmp.rename(root / "requests" / f"{req_id}.json")  # atomic: the watcher never sees half a file
            end = time.monotonic() + self.timeout_s
            while not out.exists():
                if time.monotonic() > end:
                    raise ModelOutputError(f"bridge: no answer for {req_id} within {self.timeout_s:.0f} s")
                time.sleep(2)
            time.sleep(0.5)
            text = out.read_text()
            problem = bridge_problem(text, output_schema)
            attempts.append({"request_id": req_id, "feedback_given": feedback or None, "rejected_because": problem})
            if not problem:
                return ProviderReply(text, _tokens(prompt), _tokens(text), "end_turn", self.model,
                                     provenance=bridge_provenance(root, attempts))
            feedback = f"Your previous answer was rejected: {problem}. Answer again, exactly in the schema."
        raise ModelOutputError(f"bridge: answer for {rid} still invalid after a retry: {problem}")


def bridge_provenance(root: Path, attempts: list[dict]) -> dict:
    """What actually answered a bridge call and whether an operator influenced it. The operator records the
    answering model (and any note, which is written INTO the request so the answerer and the log both see it) with
    `python -m s2s.ops.bridge assign`; without it the answering model is "unrecorded", never guessed."""
    assigned, notes = {}, []
    for a in attempts:
        rq = root / "requests" / f"{a['request_id']}.json"
        try:
            note = json.loads(rq.read_text()).get("operator_note")
        except (OSError, ValueError):
            note = None
        if note:
            notes.append({"request_id": a["request_id"], "note": note})
        try:
            assigned = json.loads((root / "requests" / f"{a['request_id']}.assign.json").read_text()) or assigned
        except (OSError, ValueError):
            pass
    return {"provider": "bridge", "attempts": attempts,
            "answered_by": assigned.get("answered_by") or "unrecorded",
            "operator_notes": notes, "operator_influenced": bool(notes)}


def bridge_problem(text: str, schema: dict | None) -> str | None:
    """None if `text` is a valid answer for `schema`, else the exact problems."""
    if schema is None:
        return None if text.strip() else "empty answer"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return f"not valid JSON ({e})"
    import jsonschema
    errs = sorted(jsonschema.Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    return "; ".join(f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message[:200]}" for e in errs[:5]) or None


class ModelGateway:
    def __init__(self, provider: DummyProvider | ScriptedProvider | AnthropicProvider | None = None):
        self.provider = provider or DummyProvider()

    @classmethod
    def from_settings(cls) -> "ModelGateway":
        """The gateway real agents use: config/finance.yaml `model_provider` (S2S_MODEL_PROVIDER
        overrides it): "bridge" = Claude Code subagents (personal localhost mode, no API usage),
        "anthropic" = the provider saved in Settings -> Model access."""
        from s2s.config import finance
        name = os.environ.get("S2S_MODEL_PROVIDER") or finance().get("model_provider") or "anthropic"
        if name == "bridge":
            return cls(BridgeProvider())
        if name == "anthropic":
            return cls(AnthropicProvider())
        raise ValueError(f"unknown model provider {name!r} (config/finance.yaml model_provider)")

    def complete(self, *, task: meter.TaskRef, system: str, messages: list[dict],
                 tools: list[dict] | None = None, max_tokens: int = 1024, temperature: float = 0.2,
                 model_hint: str = "default", output_schema: dict | None = None,
                 effort: str | None = None, agent_id: str | None = None) -> ModelResponse:
        # temperature is not sent: current models reject non-default sampling parameters.
        call_id = new_id("call")
        if agent_id and agent_id != task.agent_id:
            task = dataclasses.replace(task, agent_id=agent_id)
        meter.check_spend_caps(task)  # a reached cap stops the run before any spend
        t0 = time.perf_counter()
        reply = self.provider.complete(system, messages, max_tokens, output_schema, effort)
        latency_ms = round((time.perf_counter() - t0) * 1000)
        model = reply.model or self.provider.model
        tin, tout = reply.input_tokens, reply.output_tokens
        log_path = os.environ.get("S2S_DUMMY_MODEL_CALL_LOG")
        if log_path:
            with open(log_path, "a") as f:
                f.write(json.dumps({"call_id": call_id, "task_id": task.id, "agent_id": task.agent_id,
                                    "model": model, "input_tokens": tin, "output_tokens": tout}) + "\n")
        # Metered and committed now, in its own transaction (the call has happened and costs
        # money whatever happens next). May raise meter.BudgetExceeded (hard stop).
        rec = meter.record_llm(task, model, tin, tout, call_id)
        resp = ModelResponse(reply.text, model, tin, tout, call_id, None, reply.stop_reason, latency_ms,
                             float(rec.cost_usd),
                             provenance={"provider": type(self.provider).__name__, "model_answered": model,
                                         "model_hint": model_hint, "effort": effort,
                                         "operator_influenced": False, **reply.provenance})
        if reply.stop_reason == "refusal":
            raise ModelOutputError(f"{task.agent_id}: the model declined the request (stop_reason=refusal)")
        if output_schema is not None:
            if reply.stop_reason == "max_tokens":
                raise ModelOutputError(f"{task.agent_id}: answer cut off at max_tokens={max_tokens}")
            try:
                resp.data = json.loads(reply.text)
            except json.JSONDecodeError as e:
                raise ModelOutputError(f"{task.agent_id}: answer is not valid JSON ({e})") from None
        return resp
