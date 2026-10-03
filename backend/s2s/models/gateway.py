"""Model gateway (MASTER_SPEC Part 7.3), M0.3 skeleton.

Providers:
- DummyProvider (M0.3): no network call, deterministic text, token counts from text lengths
  (~4 characters per token). Used by the dummy agent.
- AnthropicProvider (Part 28): the provider, key and endpoint saved in Settings -> Model access
  (s2s.models.access, an encrypted server-side secret, read on every call so a replaced key
  applies at once). Every agent uses the default model (claude-sonnet-5-5).

Before every call the spend caps (finance.yaml spend_caps) are checked; a reached cap raises
meter.SpendCapReached and no call is made. Every call is metered (usage_records row with cost,
committed) before the response is returned.

The dummy provider also appends each call to its own JSONL log (S2S_DUMMY_MODEL_CALL_LOG),
independent of metering, so tests can check that every call was metered.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

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


def _tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class DummyProvider:
    model = "dummy-model"

    def complete(self, system: str, messages: list[dict], max_tokens: int) -> tuple[str, int, int]:
        prompt = system + "".join(str(m.get("content", "")) for m in messages)
        last = str(messages[-1].get("content", "")) if messages else ""
        text = f"[dummy-model] Acknowledged: {last[:160]}. Plan: read inputs, act, check, report."
        return text, _tokens(prompt), min(max_tokens, _tokens(text))


class AnthropicProvider:
    """Calls the model configured in Settings -> Model access (key from the encrypted secret)."""

    @property
    def model(self) -> str:
        return access.load().get("model", access.DEFAULT_MODEL)

    def complete(self, system: str, messages: list[dict], max_tokens: int) -> tuple[str, int, int]:
        c, model = access.client()
        r = c.messages.create(model=model, system=system, messages=messages, max_tokens=max_tokens)
        text = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
        return text, r.usage.input_tokens, r.usage.output_tokens


class ModelGateway:
    def __init__(self, provider: DummyProvider | AnthropicProvider | None = None):
        self.provider = provider or DummyProvider()

    @classmethod
    def from_settings(cls) -> "ModelGateway":
        """The gateway real agents use: the provider saved in Settings -> Model access."""
        return cls(AnthropicProvider())

    def complete(self, *, task: meter.TaskRef, system: str, messages: list[dict],
                 tools: list[dict] | None = None, max_tokens: int = 1024, temperature: float = 0.2,
                 model_hint: str = "default") -> ModelResponse:
        call_id = new_id("call")
        meter.check_spend_caps(task)  # a reached cap stops the run before any spend
        text, tin, tout = self.provider.complete(system, messages, max_tokens)
        log_path = os.environ.get("S2S_DUMMY_MODEL_CALL_LOG")
        if log_path:
            with open(log_path, "a") as f:
                f.write(json.dumps({"call_id": call_id, "task_id": task.id, "agent_id": task.agent_id,
                                    "model": self.provider.model, "input_tokens": tin,
                                    "output_tokens": tout}) + "\n")
        # Metered and committed now, in its own transaction (the call has happened and costs
        # money whatever happens next). May raise meter.BudgetExceeded (hard stop).
        meter.record_llm(task, self.provider.model, tin, tout, call_id)
        return ModelResponse(text, self.provider.model, tin, tout, call_id)
