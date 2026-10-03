"""Settings (from the environment) and the YAML configs in config/."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(os.environ.get("S2S_CONFIG_DIR", REPO_ROOT / "config"))


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    event_stream: str
    event_stream_maxlen: int


def settings() -> Settings:
    return Settings(
        database_url=os.environ.get("S2S_DATABASE_URL",
                                    "postgresql+psycopg://s2s:s2s@localhost:5432/s2s"),
        redis_url=os.environ.get("S2S_REDIS_URL", "redis://localhost:6379/0"),
        event_stream=os.environ.get("S2S_EVENT_STREAM", "s2s:events"),
        event_stream_maxlen=int(os.environ.get("S2S_EVENT_STREAM_MAXLEN", "100000")),
    )


def _load(name: str, env_override: str) -> dict:
    path = Path(os.environ.get(env_override, CONFIG_DIR / name))
    return yaml.safe_load(path.read_text()) or {}


@lru_cache(maxsize=None)
def management() -> dict:
    """config/management.yaml (S2S_MANAGEMENT_CONFIG overrides the path, e.g. in tests)."""
    return _load("management.yaml", "S2S_MANAGEMENT_CONFIG")


@lru_cache(maxsize=None)
def budgets() -> dict:
    return _load("budgets.yaml", "S2S_BUDGETS_CONFIG")


@lru_cache(maxsize=None)
def finance() -> dict:
    return _load("finance.yaml", "S2S_FINANCE_CONFIG")


def sla_seconds(key: str) -> float:
    """An SLA from management.yaml `sla:` in seconds (config values are minutes)."""
    return float(management()["sla"][key]) * 60.0


def clear_caches() -> None:
    for f in (management, budgets, finance):
        f.cache_clear()
