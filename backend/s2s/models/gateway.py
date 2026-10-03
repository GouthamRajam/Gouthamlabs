"""Model gateway (MASTER_SPEC Part 7.3), M0.3 skeleton.

Only a dummy provider exists in M0.3: it makes no network call and returns deterministic
text, with token counts derived from the text lengths (~4 characters per token). Every call
is metered (usage_records row with cost, committed) before the response is returned. Real providers
(and `model_hint` routing to them) arrive in M0.5.

The dummy provider also appends each call to its own JSONL log (S2S_DUMMY_MODEL_CALL_LOG),
independent of metering, so tests can check that every call was metered.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from s2s.finance import meter
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


class ModelGateway:
    def __init__(self, provider: DummyProvider | None = None):
        self.provider = provider or DummyProvider()

    def complete(self, *, task: meter.TaskRef, system: str, messages: list[dict],
                 tools: list[dict] | None = None, max_tokens: int = 1024, temperature: float = 0.2,
                 model_hint: str = "default") -> ModelResponse:
        call_id = new_id("call")
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
