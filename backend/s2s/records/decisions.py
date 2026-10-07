"""Structured decision log (Phase 1 trajectory item 2).

New decisions are JSON lines in docs/decisions/decisions.jsonl, validated against SCHEMA, with ids linking each
decision to the runs, tasks, checks, events, analyses and bridge requests it rests on. docs/DECISIONS.md stays the
human-readable log: `add` appends a rendered line there carrying the decision id.

The prose entries written before this schema are converted once into docs/decisions/legacy.jsonl
(legacy=true, structured=false): the date, scope and full text, plus every id found in the text. Nothing is inferred
beyond what the text says.

    python -m s2s.records.decisions add --actor CEO --kind decision --scope "M0.7" --title "..." --decision "..." \\
        [--rationale ...] [--source URL]... [--run ID]... [--task ID]... [--check ID]... [--outcome pass|fail|...]
    python -m s2s.records.decisions legacy        # (re)build legacy.jsonl from DECISIONS.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DIR = REPO / "docs" / "decisions"
LOG, LEGACY, MD = DIR / "decisions.jsonl", DIR / "legacy.jsonl", REPO / "docs" / "DECISIONS.md"
KINDS = ("decision", "policy", "outcome", "correction", "budget", "gate")
OUTCOMES = ("pass", "fail", "conditional", "pending", "n/a")
ID_PATTERNS = {"runs": r"run_[0-9A-Z]{26}", "tasks": r"task_[0-9A-Z]{26}", "checks": r"chk_[0-9A-Z]{26}",
               "events": r"evt_[0-9A-Z]{26}", "gates": r"gate_[0-9A-Z]{26}", "bridge_requests": r"br_[0-9A-Z]{26}",
               "analyses": r"ana_[0-9A-Z]{26}", "commits": r"\b[0-9a-f]{7,40}\b(?=\))|commit [0-9a-f]{7,40}"}
LINKS = {"type": "object", "additionalProperties": False,
         "properties": {k: {"type": "array", "items": {"type": "string"}} for k in ID_PATTERNS}}
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["schema", "id", "date", "ts", "actor", "kind", "scope", "title", "decision", "links", "outcome",
                 "operator_influenced", "legacy"],
    "properties": {
        "schema": {"const": 1}, "id": {"type": "string", "pattern": r"^D-\d{8}-\d{3}$"},
        "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}, "ts": {"type": "string"},
        "actor": {"type": "string", "minLength": 1}, "kind": {"enum": list(KINDS)},
        "scope": {"type": "string"}, "title": {"type": "string", "minLength": 1},
        "decision": {"type": "string", "minLength": 1}, "rationale": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "string"}}, "links": LINKS,
        "outcome": {"enum": list(OUTCOMES)}, "operator_influenced": {"type": "boolean"},
        "supersedes": {"type": "array", "items": {"type": "string"}}, "legacy": {"const": False},
    },
}
LEGACY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["schema", "id", "date", "scope", "text", "links", "legacy", "structured"],
    "properties": {"schema": {"const": 1}, "id": {"type": "string", "pattern": r"^L-\d{4}$"},
                   "date": {"type": "string"}, "scope": {"type": "string"}, "text": {"type": "string"},
                   "links": LINKS, "legacy": {"const": True}, "structured": {"const": False}},
}


def extract_links(text: str) -> dict[str, list[str]]:
    out = {}
    for k, rx in ID_PATTERNS.items():
        if k == "commits":
            continue
        found = list(dict.fromkeys(re.findall(rx, text)))
        if found:
            out[k] = found
    return out


def legacy_from_markdown(md: str) -> list[dict]:
    """Every '- YYYY-MM-DD (scope) — text' entry of DECISIONS.md, in order, as an unstructured legacy record."""
    out = []
    for line in md.splitlines():
        m = re.match(r"^- (\d{4}-\d{2}-\d{2})(?: \(([^)]*)\))?\s*(?:[—-]+)\s*(.*)$", line)
        if not m or re.search(r"\[D-\d{8}-\d{3}\]", line):  # structured entries are rendered with their id
            continue
        out.append({"schema": 1, "id": f"L-{len(out) + 1:04d}", "date": m[1], "scope": m[2] or "", "text": m[3],
                    "links": extract_links(m[3]), "legacy": True, "structured": False})
    return out


def validate(rec: dict, schema: dict = SCHEMA) -> list[str]:
    import jsonschema
    return [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}"
            for e in jsonschema.Draft202012Validator(schema).iter_errors(rec)]


def load(path: Path = LOG) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []


def all_decisions() -> list[dict]:
    return load(LEGACY) + load(LOG)


def add(*, actor: str, kind: str, scope: str, title: str, decision: str, rationale: str = "",
        sources: list[str] | None = None, links: dict | None = None, outcome: str = "n/a",
        operator_influenced: bool = False, supersedes: list[str] | None = None, log: Path = LOG,
        md: Path | None = MD, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    day = now.strftime("%Y%m%d")
    n = 1 + sum(1 for r in load(log) if r["id"].startswith(f"D-{day}-"))
    rec = {"schema": 1, "id": f"D-{day}-{n:03d}", "date": now.strftime("%Y-%m-%d"), "ts": now.isoformat(),
           "actor": actor, "kind": kind, "scope": scope, "title": title, "decision": decision,
           "rationale": rationale, "sources": list(sources or []), "links": {k: v for k, v in (links or {}).items() if v},
           "outcome": outcome, "operator_influenced": operator_influenced, "supersedes": list(supersedes or []),
           "legacy": False}
    problems = validate(rec)
    if problems:
        raise ValueError(f"decision does not match the schema: {problems}")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    if md is not None:
        with md.open("a") as f:
            f.write(f"- {rec['date']} ({scope}) [{rec['id']}] — {title}: {decision}"
                    + (f" Rationale: {rationale}" if rationale else "") + "\n")
    return rec


def write_legacy(md: Path = MD, out: Path = LEGACY) -> int:
    recs = legacy_from_markdown(md.read_text())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in recs))
    return len(recs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.records.decisions")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("legacy")
    a = sub.add_parser("add")
    for k in ("actor", "kind", "scope", "title", "decision"):
        a.add_argument(f"--{k}", required=True)
    a.add_argument("--rationale", default="")
    a.add_argument("--outcome", default="n/a", choices=OUTCOMES)
    a.add_argument("--operator-influenced", action="store_true")
    a.add_argument("--source", action="append", default=[])
    for k in ID_PATTERNS:
        a.add_argument(f"--{k[:-1] if k.endswith('s') else k}", dest=k, action="append", default=[])
    args = ap.parse_args(argv)
    if args.cmd == "legacy":
        print(f"{write_legacy()} legacy entries -> {LEGACY}")
        return 0
    rec = add(actor=args.actor, kind=args.kind, scope=args.scope, title=args.title, decision=args.decision,
              rationale=args.rationale, sources=args.source, outcome=args.outcome,
              operator_influenced=args.operator_influenced, links={k: getattr(args, k) for k in ID_PATTERNS})
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
