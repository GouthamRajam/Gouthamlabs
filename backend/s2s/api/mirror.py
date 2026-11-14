"""Live mirror of a remote S2S run into this instance (personal use: watch a cloud run on a local dashboard).

POST /mirror upserts rows (FK order) and inserts events; each new event is re-published on this instance's
Redis stream, so /ws/events and the Live Office update the moment it arrives. Disabled unless
S2S_MIRROR_TOKEN is set; every request must carry that token in X-S2S-Mirror-Token.
"""
from __future__ import annotations

import hmac
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import insert

from s2s.db.models import Base
from s2s.db.session import session
from s2s.events.bus import publish

router = APIRouter()
TABLES = ["projects", "designs", "runs", "tasks", "gates", "checks", "findings", "usage_records"]  # FK order


def _coerce(table, row: dict) -> dict:
    out = {}
    for k, v in row.items():
        col = table.columns.get(k)
        if col is None:
            continue  # a column this instance does not have
        if isinstance(col.type, DateTime) and isinstance(v, str):
            v = datetime.fromisoformat(v)
        out[k] = v
    return out


@router.post("/mirror")
def mirror(body: dict[str, Any], x_s2s_mirror_token: str | None = Header(default=None)) -> dict:
    token = os.environ.get("S2S_MIRROR_TOKEN")
    if not token:
        raise HTTPException(404, "mirror disabled")
    if not x_s2s_mirror_token or not hmac.compare_digest(x_s2s_mirror_token, token):
        raise HTTPException(403, "bad mirror token")
    rows = body.get("rows") or {}
    counts: dict[str, int] = {}
    new_events: list[dict] = []
    with session() as s:
        for name in TABLES:
            items = rows.get(name) or []
            if not items:
                continue
            t = Base.metadata.tables[name]
            for r in items:
                vals = _coerce(t, r)
                stmt = insert(t).values(**vals)
                upd = {c: stmt.excluded[c] for c in vals if c != "id"}
                s.execute(stmt.on_conflict_do_update(index_elements=["id"], set_=upd) if upd
                          else stmt.on_conflict_do_nothing(index_elements=["id"]))
            counts[name] = len(items)
        et = Base.metadata.tables["events"]
        for ev in body.get("events") or []:
            res = s.execute(insert(et).values(**_coerce(et, ev)).on_conflict_do_nothing(index_elements=["id"])
                            .returning(et.c.id))
            if res.first() is not None:
                new_events.append(ev)
        s.commit()
    publish(new_events)  # live feed: only events this instance did not have yet
    return {"rows": counts, "events_new": len(new_events)}
