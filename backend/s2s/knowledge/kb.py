"""Knowledge base (MASTER_SPEC Part 18.3), Phase 0: seed YAML + lessons written by Sage.

kb_search is keyword retrieval (no embeddings, no model call): it scores entries by how many
query words appear in their title, tags and symptom, so the same query always returns the
same entries. Sage owns it; each search is an event attributed to Sage.

Lessons Sage writes after a run are appended to <S2S_ARTIFACT_DIR>/knowledge/lessons.jsonl
("our own history") and are searched together with the seed.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from functools import lru_cache
from pathlib import Path

import yaml

SEED_DIR = Path(__file__).parent / "seed"
_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset("a an and the of to in on for with by is are be or at from as it this that".split())


@lru_cache(maxsize=1)
def seed_entries() -> tuple[dict, ...]:
    out: list[dict] = []
    for f in sorted(SEED_DIR.glob("*.yaml")):
        out.extend(yaml.safe_load(f.read_text())["entries"])
    return tuple(out)


def lessons_path() -> Path:
    from s2s.agents.runtime import artifact_dir
    return artifact_dir() / "knowledge" / "lessons.jsonl"


def lessons() -> list[dict]:
    p = lessons_path()
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def add_lessons(new: list[dict], run_id: str) -> list[dict]:
    p = lessons_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    rows = []
    with p.open("a") as f:
        for i, lesson in enumerate(new):
            row = {"id": f"kb-lesson-{run_id}-{i + 1}", "kind": "lesson", **lesson,
                   "source": {"title": f"S2S run {run_id}", "url": f"run:{run_id}"},
                   "date": today, "confidence": "medium", "owner": "Sage"}
            f.write(json.dumps(row) + "\n")
            rows.append(row)
    return rows


def _words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1}


def search(query: str, k: int = 4) -> list[dict]:
    q = _words(query)
    scored = []
    for e in (*seed_entries(), *lessons()):
        tags = {t.lower() for t in e.get("tags", [])}
        hay = _words(" ".join([e.get("title", ""), e.get("symptom", ""), " ".join(tags).replace("_", " ")]))
        score = len(q & hay) + 2 * len(q & tags)
        if score:
            scored.append((score, e["id"], e))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [e for _, _, e in scored[:k]]


def brief(entries: list[dict]) -> str:
    """Entries as the `relevant_knowledge` text of a task envelope."""
    if not entries:
        return "none found"
    return "\n".join(f"- [{e['id']}, confidence {e.get('confidence')}] {e['title']}: {e.get('lesson', e.get('fix', ''))} "
                     f"(source: {e['source'].get('title')}, {e['source'].get('url')})" for e in entries)
