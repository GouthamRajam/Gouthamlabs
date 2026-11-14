"""Operator records for coding-agent bridge requests (Phase 1 trajectory items 3 and 4).

In bridge mode a model call is answered outside S2S, so S2S cannot see which model answered or whether the operator
told the answerer anything. Phase 0 answers were sometimes given with operator notes added to the answering prompt,
outside the logged request, so the record no longer explained the answer. Now, BEFORE a request is answered:

    python -m s2s.ops.bridge assign <request_id> --model claude-opus-5-5 [--via "coding-agent subagent"]
                                    [--note "<fact the answerer needs>"]

- the answering model is written to requests/<id>.assign.json and recorded with the call (answered_by);
- a note is written INTO the request (field operator_note), so the answerer reads it there, the call's record
  carries it, and the call is flagged operator_influenced. A note given any other way is not allowed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from s2s.models.gateway import BridgeProvider


def assign(request_id: str, model: str, via: str = "coding-agent subagent", note: str | None = None,
           actor: str = "operator", root: Path | None = None) -> dict:
    root = Path(root or BridgeProvider().root)
    rq = root / "requests" / f"{request_id}.json"
    if not rq.exists():
        raise FileNotFoundError(f"no bridge request {request_id}")
    if (root / "responses" / f"{request_id}.json").exists():
        raise RuntimeError(f"{request_id} is already answered: its provenance can no longer be assigned")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    rec = {"request_id": request_id, "answered_by": {"model": model, "via": via}, "assigned_by": actor, "ts": now}
    if note:
        req = json.loads(rq.read_text())
        notes = list(req.get("operator_note") or [])
        notes.append({"text": note, "by": actor, "ts": now})
        req["operator_note"] = notes
        tmp = rq.with_name(f".{rq.name}.tmp")
        tmp.write_text(json.dumps(req, indent=1))
        os.replace(tmp, rq)  # atomic: an answerer never reads half a request
        rec["operator_note"] = note
    (root / "requests" / f"{request_id}.assign.json").write_text(json.dumps(rec, indent=1))
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.ops.bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assign", help="record the answering model (and an operator note) before answering")
    a.add_argument("request_id")
    a.add_argument("--model", required=True)
    a.add_argument("--via", default="coding-agent subagent")
    a.add_argument("--note")
    args = ap.parse_args(argv)
    print(json.dumps(assign(args.request_id, args.model, args.via, args.note)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
