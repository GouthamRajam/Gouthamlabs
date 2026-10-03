"""Settings -> Model Access (MASTER_SPEC Part 28.2), thin Phase 0 version.

The provider choice, API key and on-prem endpoint are one encrypted secret (s2s.secrets,
name "model_access"). The key is write-only: `public_view()` returns only its last 4
characters, and nothing in this module logs it or puts it in an error message.

Providers:
- anthropic: the Anthropic API, official SDK.
- onprem: an endpoint inside the customer network that speaks the Anthropic Messages API
  (same SDK, base_url = the endpoint).
- bedrock: selectable and saved, but calls are not wired yet (Part 28.6: Bedrock comes with
  the hardened version); Test connection says so instead of pretending.

All agents use DEFAULT_MODEL.
"""
from __future__ import annotations

import datetime as dt
import time
from urllib.parse import urlparse

import anthropic

from s2s import secrets
from s2s.finance import meter
from s2s.ids import new_id

SECRET = "model_access"
PROVIDERS = ("anthropic", "onprem", "bedrock")
DEFAULT_MODEL = "claude-sonnet-5-5"


class NotConfigured(RuntimeError):
    pass


def load() -> dict:
    return secrets.get(SECRET) or {}


def _mask(key: str | None) -> str | None:
    return f"••••••••{key[-4:]}" if key else None


def public_view() -> dict:
    """What the UI may see: never the key, only whether one is set and its last 4 characters."""
    cfg = load()
    return {"provider": cfg.get("provider", "anthropic"), "endpoint": cfg.get("endpoint"),
            "model": cfg.get("model", DEFAULT_MODEL), "key_set": bool(cfg.get("api_key")),
            "key_masked": _mask(cfg.get("api_key")), "updated_at": cfg.get("updated_at")}


def save(provider: str, api_key: str | None, endpoint: str | None) -> dict:
    """Store the settings. api_key None/empty keeps the stored key (replace, never read back)."""
    if provider not in PROVIDERS:
        raise ValueError(f"provider must be one of {', '.join(PROVIDERS)}")
    cfg = load()
    key = (api_key or "").strip() or cfg.get("api_key")
    endpoint = (endpoint or "").strip() or None
    if provider == "anthropic" and not key:
        raise ValueError("an API key is required for the Anthropic API")
    if provider == "onprem":
        u = urlparse(endpoint or "")
        if u.scheme not in ("http", "https") or not u.netloc:
            raise ValueError("on-prem endpoint must be an http(s) URL inside your network")
    secrets.put(SECRET, {"provider": provider, "api_key": key, "endpoint": endpoint,
                         "model": cfg.get("model", DEFAULT_MODEL),
                         "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()})
    return public_view()


def client(timeout: float = 600.0, max_retries: int = 2) -> tuple[anthropic.Anthropic, str]:
    """An SDK client for the configured provider, and the model to use."""
    cfg = load()
    provider, model = cfg.get("provider", "anthropic"), cfg.get("model", DEFAULT_MODEL)
    if provider == "anthropic":
        if not cfg.get("api_key"):
            raise NotConfigured("no API key saved (Settings -> Model access)")
        return anthropic.Anthropic(api_key=cfg["api_key"], timeout=timeout, max_retries=max_retries), model
    if provider == "onprem":
        if not cfg.get("endpoint"):
            raise NotConfigured("no on-prem endpoint saved (Settings -> Model access)")
        return anthropic.Anthropic(api_key=cfg.get("api_key") or "unused", base_url=cfg["endpoint"],
                                   timeout=timeout, max_retries=max_retries), model
    raise NotConfigured(f"provider '{provider}' is not wired yet (Part 28.6: hardened version)")


def _redact(text: str) -> str:
    key = load().get("api_key")
    return text.replace(key, "••••") if key else text


def _api_error(e: anthropic.APIStatusError) -> str:
    body = e.body if isinstance(e.body, dict) else {}
    msg = (body.get("error") or {}).get("message") if isinstance(body.get("error"), dict) else None
    return f"HTTP {e.status_code} {getattr(e, 'type', None) or ''}: {msg or 'request failed'}".replace("  ", " ")


def test_connection() -> dict:
    """ONE small model call (no retries); returns pass/fail, latency and the model that answered.
    The call is metered like any other."""
    cfg = load()
    provider = cfg.get("provider", "anthropic")
    result = {"provider": provider, "ok": False, "latency_ms": None, "model": None, "error": None}
    try:
        c, model = client(timeout=30.0, max_retries=0)
    except NotConfigured as e:
        return {**result, "error": str(e)}
    extra = {"thinking": {"type": "between_tools"}} if provider == "anthropic" else {}  # no thinking: cheapest
    t0 = time.perf_counter()
    try:
        r = c.messages.create(model=model, max_tokens=16,
                              messages=[{"role": "user", "content": "Reply with the single word: OK"}], **extra)
    except anthropic.APIStatusError as e:  # 4xx/5xx from the provider (bad key, unknown model...)
        return {**result, "latency_ms": round((time.perf_counter() - t0) * 1000), "model": model,
                "error": _redact(_api_error(e))}
    except anthropic.APIConnectionError as e:  # includes timeouts: no response at all
        return {**result, "latency_ms": round((time.perf_counter() - t0) * 1000), "model": model,
                "error": _redact(f"could not reach the provider: {type(e).__name__}")}
    latency = round((time.perf_counter() - t0) * 1000)
    reply = "".join(b.text for b in r.content if getattr(b, "type", None) == "text").strip()
    try:
        meter.record_llm_untasked("settings", r.model, r.usage.input_tokens, r.usage.output_tokens,
                                  new_id("call"), purpose="test connection")
    except KeyError:  # an on-prem model with no price in finance.yaml: say so, never meter at $0
        result["warning"] = f"model '{r.model}' has no price in config/finance.yaml; call not metered"
    return {**result, "ok": True, "latency_ms": latency, "model": r.model, "reply": reply[:40],
            "stop_reason": r.stop_reason, "input_tokens": r.usage.input_tokens,
            "output_tokens": r.usage.output_tokens}
