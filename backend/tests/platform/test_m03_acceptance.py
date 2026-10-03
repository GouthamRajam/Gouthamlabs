"""M0.3 acceptance tests (MASTER_SPEC Part 13.2), against real Postgres, Redis, and real
orchestrator/API processes.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import time
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from tests.platform.conftest import new_design, wait_for


def _run_status(run_id):
    from s2s.db.models import Run
    from s2s.db.session import session
    with session() as s:
        return s.get(Run, run_id).status


def _events(run_id, **filters):
    from s2s.db.models import Event
    from s2s.db.session import session
    with session() as s:
        q = select(Event).where(Event.run_id == run_id).order_by(Event.id)
        for k, v in filters.items():
            q = q.where(getattr(Event, k) == v)
        return s.scalars(q).all()


# --- 1. creating a design and starting a run creates tasks in the DB -------------------------------
def test_1_create_design_and_run_creates_tasks(platform):
    from s2s.api.app import app
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.orchestrator.flow import STAGE_NAMES
    c = TestClient(app)
    p = c.post("/projects", json={"name": "acceptance", "owner": "goutham"})
    assert p.status_code == 201
    d = c.post("/designs", json={"project_id": p.json()["id"], "name": "counter8",
                                 "request_text": "8-bit up counter with enable"})
    assert d.status_code == 201
    r = c.post(f"/designs/{d.json()['id']}/runs", json={})
    assert r.status_code == 201
    run_id = r.json()["id"]

    with session() as s:  # straight from the database, not from the API response
        tasks = s.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.seq)).all()
    assert [t.stage for t in tasks] == list(STAGE_NAMES)
    assert all(t.status == "pending" for t in tasks)
    by = {t.stage: t for t in tasks}
    assert by["rtl"].depends_on == [by["architecture"].id] == by["test_build"].depends_on  # 2A || 2B
    assert sorted(by["verification"].depends_on) == sorted([by["rtl"].id, by["test_build"].id])
    assert by["rtl"].agent_id == "Ada" and by["verification"].agent_id == "Rex"
    assert by["test_build"].budget["max_tokens"] == 800000  # Vera's budget from budgets.yaml
    listed = c.get(f"/runs/{run_id}/tasks").json()
    assert [t["id"] for t in listed] == [t.id for t in tasks]

    partial = c.post(f"/designs/{d.json()['id']}/runs", json={"from_stage": "rtl", "to_stage": "signoff"})
    assert [t["stage"] for t in partial.json()["tasks"]] == ["rtl", "test_build", "verification",
                                                            "synthesis", "dft", "floorplan",
                                                            "place_route", "signoff"]


# --- 2. killing the orchestrator mid-run and restarting resumes from the last checkpoint ----------
def test_2_resume_after_crash(platform):
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    with session() as s:
        run_id = create_run(s, new_design(s), dummy={"step_delay_s": 0.4}).id

    orc = platform.start_orchestrator("orchestrator-1.log")

    def mid_task():
        with session() as s:
            done = s.scalar(select(func.count()).select_from(Task).where(
                Task.run_id == run_id, Task.status == "completed"))
            for t in s.scalars(select(Task).where(Task.run_id == run_id, Task.status == "running")):
                if done >= 1 and 2 <= (t.checkpoint or {}).get("step", 0) <= 3:
                    return t.id
        return None

    victim = wait_for(mid_task, 60, what="a task part-way through with an earlier task completed")
    platform.kill(orc)  # SIGKILL mid-run

    with session() as s:
        before = {t.id: (t.status, (t.checkpoint or {}).get("step", 0), t.attempts)
                  for t in s.scalars(select(Task).where(Task.run_id == run_id))}
    completed_before = {tid for tid, (st, _, _) in before.items() if st == "completed"}
    v_status, v_step, v_attempts = before[victim]
    assert v_status == "running" and v_attempts == 1  # left behind by the dead orchestrator
    print(f"\nkilled orchestrator: {len(completed_before)} task(s) completed, {victim} at checkpoint "
          f"step {v_step}")

    platform.start_orchestrator("orchestrator-2.log")
    wait_for(lambda: _run_status(run_id) == "completed", 120, every=0.2, what="run completion")
    log2 = platform.log("orchestrator-2.log")
    assert "recovered" in log2 and f"recovering {victim}" in log2, log2

    with session() as s:
        tasks = {t.id: t for t in s.scalars(select(Task).where(Task.run_id == run_id))}
    assert all(t.status == "completed" for t in tasks.values())
    # completed tasks were not redone
    for tid in completed_before:
        assert tasks[tid].attempts == 1
        assert len(_events(run_id, task_id=tid, type="task.started")) == 1
    # the interrupted task resumed from its checkpoint, not from the start
    v = tasks[victim]
    assert v.attempts == 2
    starts = _events(run_id, task_id=victim, type="task.started")
    assert [e.detail["resumed_from_step"] for e in starts] == [0, v_step]
    beats = [e.detail["step"] for e in _events(run_id, task_id=victim, type="task.heartbeat")]
    n = v.checkpoint["step"]
    assert beats == list(range(1, n + 1)), f"each step must commit exactly once, got {beats}"
    print(f"resumed {victim} from step {v_step}; heartbeat steps {beats}; attempts={v.attempts}")


# --- 3. /ws/events streams the dummy agent's events in under 1 second end to end -----------------
def test_3_ws_events_end_to_end_under_1s(platform):
    import websockets
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    _, port = platform.start_api()
    platform.start_orchestrator()

    async def collect() -> tuple[str, list[tuple[dict, float]], int]:
        received: list[tuple[dict, float]] = []
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws/events") as ws:
            hello = json.loads(await ws.recv())
            assert hello["type"] == "stream.subscribed"
            with session() as s:
                # 0.3 s of simulated work per step: latency must not depend on step duration
                run_id = create_run(s, new_design(s), dummy={"step_delay_s": 0.3}).id
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                now = dt.datetime.now(dt.timezone.utc)
                ev = json.loads(raw)
                if ev.get("run_id") != run_id:
                    continue
                emitted = dt.datetime.fromisoformat(ev["ts"].replace("Z", "+00:00"))
                received.append((ev, (now - emitted).total_seconds()))
                if ev["type"] == "stage.changed" and ev["detail"].get("to") == "done":
                    break
        return run_id, received, 0

    run_id, received, _ = asyncio.run(collect())
    lat = sorted(l for _, l in received)
    db_events = _events(run_id)
    got = [e["id"] for e, _ in received]
    # Every persisted event arrives exactly once. The stream is in COMMIT order; ids are assigned
    # at emit time, so events of tasks running in parallel (2A || 2B) may interleave differently.
    assert sorted(got) == sorted(e.id for e in db_events) and len(got) == len(set(got))
    steps: dict = {}
    for e, _ in received:  # each task's progress arrives in order: heartbeat steps 1, 2, ..., n
        if e["type"] == "task.heartbeat":
            steps.setdefault(e["task_id"], []).append(e["detail"]["step"])
    assert len(steps) == 11 and all(v == list(range(1, len(v) + 1)) for v in steps.values())
    print(f"\n{len(received)} events over WS; latency (event ts -> client receive): "
          f"min {lat[0] * 1000:.1f} ms, median {lat[len(lat) // 2] * 1000:.1f} ms, "
          f"p95 {lat[int(len(lat) * 0.95)] * 1000:.1f} ms, max {lat[-1] * 1000:.1f} ms")
    assert lat[-1] < 1.0


# --- 4. a dummy task that stops heartbeating is flagged task.stalled within the configured time ---
def test_4_stalled_task_is_flagged_within_configured_time(platform):
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    from s2s.orchestrator.watchdog import stall_threshold_s
    with session() as s:
        run = create_run(s, new_design(s), to_stage="architecture",
                         dummy={"step_delay_s": 0.05, "hang": {"stage": "spec", "at_step": 2, "seconds": 8}})
        run_id = run.id
    platform.start_orchestrator()
    wait_for(lambda: _run_status(run_id) == "completed", 60, every=0.2, what="run completion")

    with session() as s:
        spec = s.scalar(select(Task).where(Task.run_id == run_id, Task.stage == "spec"))
        threshold = stall_threshold_s(spec)
    [stalled] = _events(run_id, type="task.stalled")
    assert stalled.task_id == spec.id and stalled.to_agent_id == "Juno"  # Iris's manager chain: Juno
    beats = _events(run_id, task_id=spec.id, type="task.heartbeat")
    last_beat_before = max(e.ts for e in beats if e.ts < stalled.ts)
    flagged_after = (stalled.ts - last_beat_before).total_seconds()
    print(f"\nconfigured stall threshold {threshold:.1f}s; flagged {flagged_after:.2f}s after the last "
          f"heartbeat (watchdog runs every 0.5 s)")
    assert threshold < flagged_after <= threshold + 1.0
    [esc] = _events(run_id, type="escalation", task_id=spec.id)
    assert esc.detail["rule"] == "stall unresolved"
    assert _events(run_id, type="manager.checkin")
    with session() as s:
        assert s.get(Task, spec.id).stalled_at is None  # progress resumed and cleared the flag
    assert len(_events(run_id, type="task.stalled")) == 1  # healthy tasks are not flagged


# --- 5. every dummy model call creates a usage_records row with cost ------------------------------
def test_5_every_model_call_creates_a_usage_record_with_cost(platform):
    from s2s.db.models import UsageRecord
    from s2s.db.session import session
    from s2s.finance.meter import price
    from s2s.orchestrator.engine import create_run
    with session() as s:
        run_id = create_run(s, new_design(s), dummy={"step_delay_s": 0.02}).id
    platform.start_orchestrator()
    wait_for(lambda: _run_status(run_id) == "completed", 60, every=0.2, what="run completion")

    calls = [json.loads(l) for l in (platform.tmp / "model_calls.jsonl").read_text().splitlines()]
    with session() as s:
        rows = s.scalars(select(UsageRecord).where(UsageRecord.run_id == run_id,
                                                   UsageRecord.source == "llm")).all()
    assert len(calls) > 0
    assert sorted(c["call_id"] for c in calls) == sorted(r.detail["call_id"] for r in rows)
    p_in, p_out = price("dummy-model")
    for r in rows:
        expected = p_in * r.detail["input_tokens"] + p_out * r.detail["output_tokens"]
        assert Decimal(str(r.cost_usd)) == expected and expected > 0
        assert r.task_id and r.agent_id and r.model == "dummy-model"
    total = sum(Decimal(str(r.cost_usd)) for r in rows)
    print(f"\n{len(calls)} dummy model calls -> {len(rows)} usage_records rows, total ${total:.6f}")
