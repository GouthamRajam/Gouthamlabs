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


@dataclass
class ProviderReply:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None = None
    model: str | None = None  # the model that answered (defaults to the provider's model)


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


class ModelGateway:
    def __init__(self, provider: DummyProvider | ScriptedProvider | AnthropicProvider | None = None):
        self.provider = provider or DummyProvider()

    @classmethod
    def from_settings(cls) -> "ModelGateway":
        """The gateway real agents use: the provider saved in Settings -> Model access."""
        return cls(AnthropicProvider())

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
                             float(rec.cost_usd))
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
