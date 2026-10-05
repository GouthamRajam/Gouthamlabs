"""Relay this instance's S2S state to a remote S2S API in near real time (personal use).

    cd backend && S2S_MIRROR_URL=https://<host> S2S_MIRROR_TOKEN=<token> python scripts/mirror_relay.py

Every 2 s: new events (ids are ULIDs, so they sort by time). Every 10 s: the small state tables (projects,
designs, runs, tasks, gates) in full, plus new checks / findings / usage records. Rows go in FK order.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import httpx
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s2s.db.models import Base  # noqa: E402
from s2s.db.session import session  # noqa: E402

URL = os.environ["S2S_MIRROR_URL"].rstrip("/") + "/mirror"
HEAD = {"X-S2S-Mirror-Token": os.environ["S2S_MIRROR_TOKEN"], "ngrok-skip-browser-warning": "true",
        "Content-Type": "application/json"}
FULL = ["projects", "designs", "runs", "tasks", "gates"]
APPEND = ["checks", "findings", "usage_records"]


def _j(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    raise TypeError(type(v))


def _rows(s, name, after=None, limit=None):
    t = Base.metadata.tables[name]
    q = select(t).order_by(t.c.id)
    if after:
        q = q.where(t.c.id > after)
    if limit:
        q = q.limit(limit)
    return [dict(r._mapping) for r in s.execute(q)]


def send(rows=None, events=None):
    body = json.dumps({"rows": rows or {}, "events": events or []}, default=_j)
    for i in range(4):
        try:
            r = httpx.post(URL, content=body, headers=HEAD, timeout=30)
            if r.status_code == 200:
                return r.json()
            print(f"mirror HTTP {r.status_code}: {r.text[:200]}", flush=True)
        except httpx.HTTPError as e:
            print(f"mirror error: {e}", flush=True)
        time.sleep(2 ** i)
    return None


def main():
    last_ev, last = None, {n: None for n in APPEND}
    t_full = 0.0
    while True:
        with session() as s:
            if time.monotonic() - t_full >= 10:
                rows = {n: _rows(s, n) for n in FULL}
                for n in APPEND:
                    new = _rows(s, n, last[n])
                    if new:
                        rows[n] = new
                if send(rows=rows) is not None:
                    for n in APPEND:
                        if rows.get(n):
                            last[n] = rows[n][-1]["id"]
                    t_full = time.monotonic()
            while True:
                evs = _rows(s, "events", last_ev, 500)
                if not evs:
                    break
                res = send(events=evs)
                if res is None:
                    break
                last_ev = evs[-1]["id"]
                print(f"{time.strftime('%H:%M:%S')} events +{len(evs)} (new on remote: {res['events_new']})", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
