"""Orchestrator (MASTER_SPEC Parts 6.6, 7.4, 9), M0.3 skeleton: a resumable state machine.

Run:  pending -> running -> completed | failed
Task: pending -> ready -> running -> completed | failed | paused

All state lives in Postgres, so the orchestrator can be killed at any moment. On start it
  1. takes a Postgres advisory lock (only one orchestrator may run),
  2. syncs the org structure from config/management.yaml into org_units,
  3. recovers tasks a previous (dead) orchestrator left `running`: they go back to `ready`
     and keep their checkpoint, so the agent resumes from its last committed step.
Then it loops: promote pending tasks whose dependencies are done and whose gates are
approved, assign ready tasks to workers, open/decide gates, finish runs, and run the
heartbeat watchdog.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import signal
import threading
import time
from pathlib import Path
from concurrent.futures import Future, ThreadPoolExecutor

from sqlalchemy import select, text

from s2s.agents import management as mgmt
from s2s.agents.dummy import DummyAgent
from s2s.agents.m05 import DesignAgent
from s2s.agents import m06  # noqa: F401  (registers test_build/verification)
from s2s.agents import m07  # noqa: F401  (registers synthesis..gdsii)
from s2s.agents.runtime import Agent, run_task
from s2s.config import management
from s2s.db.models import Design, Gate, Run, Task
from s2s.db.session import engine, session as db_session
from s2s.events.bus import emit, utcnow
from s2s.ids import new_id
from s2s.models.gateway import ModelGateway
from s2s.orchestrator import flow, watchdog
from s2s.org import sync_org

log = logging.getLogger("s2s.orchestrator")

ADVISORY_LOCK_KEY = 0x5325_0003  # one orchestrator per database
AGENTS: dict[str, type[Agent]] = {"dummy": DummyAgent, "s2s": DesignAgent}
# The gateway each agent kind uses: the dummy agent never makes a real call; the M0.5 design
# agents use the model saved in Settings -> Model access.
GATEWAYS = {"dummy": ModelGateway, "s2s": ModelGateway.from_settings}


SRC = Path(__file__).resolve().parents[1]  # backend/s2s
STALE_CHECK_S = 60


def code_fingerprint(root: Path = SRC) -> str:
    """Hash of every .py file under `root` (path + content). The orchestrator imports the agents and tool
    adapters once at start, so a fix committed later is not used until it restarts (uart signoff 2026-10-06
    ran the old LEC; lesson s2s-ops-003)."""
    h = hashlib.sha256()
    for f in sorted(root.rglob("*.py")):
        h.update(str(f.relative_to(root)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:16]


class AlreadyRunning(RuntimeError):
    pass


class Orchestrator:
    def __init__(self, max_parallel: int = 4, poll_s: float = 0.1, watchdog_s: float = 0.5):
        self.instance = new_id("orc")
        self.max_parallel = max_parallel
        self.poll_s = poll_s
        self.watchdog_s = watchdog_s
        self.pool = ThreadPoolExecutor(max_workers=max_parallel, thread_name_prefix="agent")
        self.inflight: dict[str, Future] = {}
        self.stop = threading.Event()
        self._lock_conn = None
        self._last_watchdog = 0.0
        self.code_fp = code_fingerprint()
        self._last_stale_check = time.monotonic()
        self.stale_code = False

    # --- lifecycle -----------------------------------------------------------------------
    def start(self) -> int:
        self._lock_conn = engine().connect()
        if not self._lock_conn.execute(text("select pg_try_advisory_lock(:k)"), {"k": ADVISORY_LOCK_KEY}).scalar():
            self._lock_conn.close()
            raise AlreadyRunning("another orchestrator holds the lock")
        with db_session() as s:
            n_units = sync_org(s)
        recovered = self.recover()
        log.info("orchestrator %s started (pid %d, code %s): %d org units, recovered %d in-flight task(s)",
                 self.instance, os.getpid(), self.code_fp, n_units, len(recovered))
        return len(recovered)

    def recover(self) -> list[str]:
        """Tasks left `running` by a dead orchestrator resume from their checkpoint."""
        with db_session() as s:
            tasks = s.scalars(select(Task).where(Task.status == "running").with_for_update()).all()
            for t in tasks:
                step = (t.checkpoint or {}).get("step", 0)
                log.info("recovering %s (%s) at checkpoint step %s", t.id, t.stage, step)
                t.status, t.lease_owner, t.ready_at = "ready", None, utcnow()
            return [t.id for t in tasks]

    def run_forever(self) -> None:
        self.start()
        try:
            while not self.stop.is_set():
                self.tick()
                self.stop.wait(self.poll_s)
        finally:
            self.pool.shutdown(wait=True)
            if self._lock_conn is not None:
                self._lock_conn.close()

    # --- one scheduling pass ---------------------------------------------------------------
    def tick(self) -> None:
        self._reap()
        with db_session() as s:
            for run in s.scalars(select(Run).where(Run.status.in_(("pending", "running")))).all():
                self._advance_run(s, run)
        self._assign()
        if not self.stale_code and time.monotonic() - self._last_stale_check >= STALE_CHECK_S:
            self._last_stale_check = time.monotonic()
            if code_fingerprint() != self.code_fp:
                self.stale_code = True
                log.warning("code changed since this orchestrator started (code %s): restart it before the next "
                            "stage that needs the change", self.code_fp)
        if time.monotonic() - self._last_watchdog >= self.watchdog_s:
            self._last_watchdog = time.monotonic()
            watchdog.tick()
            mgmt.tick(inflight=set(self.inflight))

    def _reap(self) -> None:
        for tid, fut in list(self.inflight.items()):
            if fut.done():
                del self.inflight[tid]
                if fut.exception():
                    log.error("worker for %s raised: %r", tid, fut.exception())

    def _advance_run(self, s, run: Run) -> None:
        tasks = s.scalars(select(Task).where(Task.run_id == run.id).order_by(Task.seq)).all()
        by_stage = {t.stage: t for t in tasks}
        gates = {g.after_stage: g for g in s.scalars(select(Gate).where(Gate.run_id == run.id))}
        if run.status == "pending":
            run.status = "running"
        # open and (in auto mode) decide gates for completed gated stages
        for t in tasks:
            gate_name = flow.stage(t.stage).gate_after
            if t.status == "completed" and gate_name and t.stage not in gates:
                gates[t.stage] = self._open_gate(s, run, t, gate_name)
        # promote pending -> ready
        for t in tasks:
            if t.status != "pending":
                continue
            deps = [by_stage[d] for d in flow.stage(t.stage).depends_on if d in by_stage]
            if all(d.status == "completed" for d in deps) and all(
                    gates[d.stage].status == "approved" for d in deps if d.stage in gates):
                t.status, t.ready_at = "ready", utcnow()
        # finish the run
        if tasks and all(t.status == "completed" for t in tasks) and all(
                g.status == "approved" for g in gates.values()):
            run.status, run.ended_at = "completed", utcnow()
            emit(s, "stage.changed", f"Run {run.id} complete: all {len(tasks)} stages done",
                 run_id=run.id, design_id=run.design_id, agent_id="Atlas", team="program_office",
                 stage="done", detail={"from": run.current_stage, "to": "done"})
            run.current_stage = "done"
        elif any(t.status == "failed" for t in tasks) or any(g.status == "rejected" for g in gates.values()):
            run.status, run.ended_at = "failed", utcnow()

    def _open_gate(self, s, run: Run, task: Task, gate_name: str) -> Gate:
        g = Gate(id=new_id("gate"), run_id=run.id, gate=gate_name, status="pending", after_stage=task.stage)
        s.add(g)
        base = dict(run_id=run.id, design_id=run.design_id, stage=task.stage)
        emit(s, "gate.requested", f"{gate_name} requested after {task.stage}", agent_id="Atlas",
             team="program_office", status="waiting", detail={"gate_id": g.id, "gate": gate_name}, **base)
        cfg = management()["gates"]
        if cfg.get("mode") == "auto" and gate_name not in cfg.get("always_human", []):
            # Phase 0 auto mode: approve only if every check recorded for the stage passed last.
            ok = _stage_checks_ok(s, task.id)
            g.status = "approved" if ok else "pending"
            if ok:
                g.decision, g.reviewer, g.decided_at = "approved", "auto (gates.mode=auto)", utcnow()
                g.comments = "all checks passed"
                emit(s, "gate.decided", f"{gate_name} auto-approved: all {task.stage} checks passed",
                     agent_id="Atlas", team="program_office",
                     detail={"gate_id": g.id, "gate": gate_name, "decision": "approved", "mode": "auto"}, **base)
        return g

    def _assign(self) -> None:
        free = self.max_parallel - len(self.inflight)
        if free <= 0:
            return
        with db_session() as s:
            ready = s.scalars(select(Task).where(Task.status == "ready").order_by(Task.assigned_at.is_(None),
                              Task.seq).limit(free).with_for_update(skip_locked=True)).all()
            started = []
            for t in ready:
                run = s.get(Run, t.run_id)
                now = utcnow()
                resumed_from = int((t.checkpoint or {}).get("step", 0))
                t.status, t.lease_owner = "running", self.instance
                t.attempts += 1
                t.assigned_at = t.assigned_at or now
                t.started_at = t.started_at or now
                t.last_progress_at = now
                t.stalled_at = None
                base = dict(run_id=t.run_id, design_id=run.design_id, stage=t.stage, task_id=t.id,
                            agent_id=t.agent_id, team=t.team_id)
                if run.current_stage != t.stage:
                    emit(s, "stage.changed", f"Run {run.id} entered stage {t.stage}",
                         detail={"from": run.current_stage, "to": t.stage},
                         **{**base, "agent_id": "Atlas", "team": "program_office", "task_id": None})
                    run.current_stage = t.stage
                mgmt.on_assign(s, t, run)
                emit(s, "task.started", (f"{t.agent_id} resumed: {t.title} (from step {resumed_from})"
                                         if resumed_from else f"{t.agent_id} started: {t.title}"),
                     status="working", detail={"attempt": t.attempts, "resumed_from_step": resumed_from,
                                               "orchestrator": self.instance}, **base)
                started.append((t.id, run.agent_kind))
        for tid, kind in started:
            self.inflight[tid] = self.pool.submit(run_task, tid, AGENTS[kind](), GATEWAYS[kind]())


def _stage_checks_ok(s, task_id: str) -> bool:
    from s2s.db.models import Check
    checks = s.scalars(select(Check).where(Check.task_id == task_id).order_by(Check.id)).all()
    latest: dict[str, bool] = {}
    for c in checks:  # ids are monotonic ULIDs: the last record per check name wins
        latest[c.check_name] = c.passed
    return bool(latest) and all(latest.values())


def create_run(s, design: Design, from_stage: str | None = None, to_stage: str | None = None,
               agent_kind: str = "dummy", dummy: dict | None = None, inputs: dict | None = None) -> Run:
    """agent_kind "s2s" runs the real M0.5 agents (spec, architecture, rtl only)."""
    """Create a run and its tasks (status pending). The orchestrator picks it up."""
    from s2s.finance.meter import ensure_run_budget, task_budget
    from s2s.org import load_org
    if agent_kind not in AGENTS:
        raise ValueError(f"unknown agent kind {agent_kind!r}")
    stages = flow.select_stages(from_stage, to_stage)
    if agent_kind == "s2s":
        unbuilt = [st.name for st in stages if st.name not in DesignAgent.STAGES]
        if unbuilt:
            raise ValueError(f"stages {unbuilt} have no agents yet (built: {', '.join(DesignAgent.STAGES)})")
    run = Run(id=new_id("run"), design_id=design.id, status="pending",
              stages=[st.name for st in stages], agent_kind=agent_kind)
    s.add(run)
    s.flush()
    ids: dict[str, str] = {}
    org = load_org()
    sla = management()["sla"]
    # A task's expected step time; when not configured, stall detection falls back to
    # stall_minutes alone (threshold = min(stall, multiplier x expected)).
    expected = 60.0 * float(sla.get("default_expected_step_minutes",
                                    float(sla["stall_minutes"]) / float(sla["stall_multiplier_of_expected_step"])))
    for i, st in enumerate(stages):
        tid = new_id("task")
        ids[st.name] = tid
        lead = org.by_id(st.team_id).manager_agent_id
        s.add(Task(id=tid, run_id=run.id, agent_id=lead, stage=st.name, status="pending", title=st.title,
                   seq=i, team_id=st.team_id, depends_on=[ids[d] for d in st.depends_on if d in ids],
                   inputs={"design_id": design.id, "design_name": design.name, "dummy": dummy or {},
                           "request_text": design.request_text, **(inputs or {})},
                   budget=task_budget(lead), expected_step_seconds=expected))
    ensure_run_budget(s, run.id)
    s.flush()
    return run


def main() -> None:
    p = argparse.ArgumentParser(description="S2S orchestrator")
    p.add_argument("--max-parallel", type=int, default=4)
    p.add_argument("--poll", type=float, default=0.1)
    args = p.parse_args()
    logging.basicConfig(level=os.environ.get("S2S_LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    orc = Orchestrator(max_parallel=args.max_parallel, poll_s=args.poll)
    signal.signal(signal.SIGTERM, lambda *_: orc.stop.set())
    orc.run_forever()


if __name__ == "__main__":
    main()
