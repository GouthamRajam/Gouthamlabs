"""M0.3 demo against the docker compose stack (`docker compose up -d`):

  1. subscribe to /ws/events and time every event (event ts -> received here),
  2. create a project, a design and a dummy run through the API,
  3. part-way through, SIGKILL the orchestrator container (`docker compose kill`),
  4. show the task states left in the database, restart the container,
  5. wait for the run to finish and report how the interrupted task resumed.

    python backend/scripts/demo_m03.py [--api http://localhost:8000] [--step-delay 0.5]
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

import httpx
import websockets

REPO = Path(__file__).resolve().parents[2]


def compose(*args: str) -> str:
    return subprocess.run(["docker", "compose", *args], cwd=REPO, check=True, capture_output=True,
                          text=True).stdout


async def kill_and_restart(c: httpx.AsyncClient, run_id: str) -> None:
    await asyncio.to_thread(compose, "kill", "orchestrator")  # SIGKILL
    tasks = (await c.get(f"/runs/{run_id}/tasks")).json()
    print("\n*** docker compose kill orchestrator (SIGKILL) ***")
    for t in tasks:
        if t["status"] != "pending":
            print(f"   {t['stage']:13s} {t['agent_id']:7s} {t['status']:9s} checkpoint step "
                  f"{t['checkpoint_step']} attempts {t['attempts']}")
    await asyncio.sleep(2)
    await asyncio.to_thread(compose, "start", "orchestrator")
    print("*** docker compose start orchestrator ***\n")


async def main(api: str, step_delay: float) -> None:
    c = httpx.AsyncClient(base_url=api, timeout=10)
    ws_url = api.replace("http", "ws", 1) + "/ws/events"
    lat: list[float] = []
    types: set[str] = set()
    async with websockets.connect(ws_url) as ws:
        print("ws:", json.loads(await ws.recv()))
        p = (await c.post("/projects", json={"name": "M0.3 demo", "owner": "Goutham"})).json()
        d = (await c.post("/designs", json={"project_id": p["id"], "name": "counter8",
                                            "request_text": "8-bit up counter with enable"})).json()
        run = (await c.post(f"/designs/{d['id']}/runs", json={"dummy": {"step_delay_s": step_delay}})).json()
        run_id = run["id"]
        print(f"run {run_id}: {len(run['tasks'])} tasks created:",
              ", ".join(f"{t['stage']}->{t['agent_id']}" for t in run["tasks"]))

        killed = False
        victim = crash = None
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=60)
            ev = json.loads(raw)
            if ev.get("run_id") != run_id:
                continue
            lat.append((dt.datetime.now(dt.timezone.utc)
                        - dt.datetime.fromisoformat(ev["ts"].replace("Z", "+00:00"))).total_seconds())
            types.add(ev["type"])
            if not killed and ev["type"] == "task.heartbeat" and ev["stage"] == "rtl" and ev["detail"]["step"] == 2:
                victim = ev["task_id"]
                killed = True
                # kill + restart in the background so this loop keeps reading the WebSocket
                crash = asyncio.create_task(kill_and_restart(c, run_id))
            if ev["type"] == "task.started" and ev["task_id"] == victim and ev["detail"]["resumed_from_step"]:
                print(f"event: {ev['summary']}  detail={ev['detail']}")
            if ev["type"] == "stage.changed" and ev["detail"].get("to") == "done":
                break

        await crash
    final = (await c.get(f"/runs/{run_id}")).json()
    print(f"\nrun status: {final['status']}")
    for t in final["tasks"]:
        print(f"   {t['stage']:13s} {t['agent_id']:7s} {t['status']:9s} steps {t['checkpoint_step']} "
              f"attempts {t['attempts']}")
    logs = compose("logs", "orchestrator", "--no-log-prefix")
    print("\norchestrator log lines:")
    for line in logs.splitlines():
        if "started (pid" in line or "recovering" in line:
            print("  ", line)
    lat.sort()
    print(f"\nws: {len(lat)} events of {len(types)} types; latency median {lat[len(lat) // 2] * 1000:.1f} ms, "
          f"p95 {lat[int(len(lat) * .95)] * 1000:.1f} ms, max {lat[-1] * 1000:.1f} ms")
    fin = (await c.get("/finance/summary")).json()
    print(f"finance: run spend ${fin['by_run'].get(run_id, 0):.6f} from usage_records "
          f"({fin['by_source']})")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--api", default="http://localhost:8000")
    a.add_argument("--step-delay", type=float, default=0.5)
    args = a.parse_args()
    asyncio.run(main(args.api, args.step_delay))
