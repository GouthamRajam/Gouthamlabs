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


def _finance_path() -> Path:
    return Path(os.environ.get("S2S_FINANCE_CONFIG", CONFIG_DIR / "finance.yaml"))


def spend_caps() -> dict:
    """finance.yaml `spend_caps` (Part 28.3), read fresh on every call (not cached) so a cap
    changed in Settings applies to the next model call in every process."""
    return dict((yaml.safe_load(_finance_path().read_text()) or {}).get("spend_caps") or {})


def save_spend_caps(per_design_usd: float, daily_usd: float) -> dict:
    """Rewrite only the `spend_caps` entry of finance.yaml (its comments and layout are kept)."""
    path = _finance_path()
    lines = path.read_text().splitlines(keepends=True)
    def num(v: float) -> str:  # exact: never round a cap (0.004 must not become 0.00)
        return f"{v:.2f}" if round(v, 2) == v else repr(float(v))
    new = f"spend_caps: {{per_design_usd: {num(per_design_usd)}, daily_usd: {num(daily_usd)}}}\n"
    idx = [i for i, ln in enumerate(lines) if ln.startswith("spend_caps:")]
    if len(idx) != 1:
        raise ValueError(f"{path} must contain exactly one 'spend_caps:' entry")
    end = idx[0] + 1  # a block-style entry continues on the indented lines below it
    while end < len(lines) and lines[end].startswith((" ", "\t")):
        end += 1
    lines[idx[0]:end] = [new]
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text("".join(lines))
    os.replace(tmp, path)
    finance.cache_clear()
    return spend_caps()


def sla_seconds(key: str) -> float:
    """An SLA from management.yaml `sla:` in seconds (config values are minutes)."""
    return float(management()["sla"][key]) * 60.0


def clear_caches() -> None:
    for f in (management, budgets, finance):
        f.cache_clear()
