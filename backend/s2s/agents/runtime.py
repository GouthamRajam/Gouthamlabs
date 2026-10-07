"""Agent runtime (MASTER_SPEC Part 7.4), M0.3 skeleton: resumable step execution.

An agent turns a task into an ordered list of steps (Plan -> Act -> Check -> Report).
The runtime executes them from the task's checkpoint. Each step runs in ONE database
transaction that also writes the step's events, its heartbeat and the new checkpoint
(`{"step": i + 1, "state": ...}`), so after a crash the task resumes exactly at the first
step whose transaction did not commit. Events reach the live stream only after commit.

Model calls and compute are metered in their own transactions (s2s.finance.meter): a call
that happened is paid for even if its step is later re-run.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import fcntl
import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.orm import Session

from s2s.db.models import Artifact, Check, Heartbeat, Task
from s2s.db.session import session as db_session
from s2s.events.bus import emit, utcnow
from s2s.finance import meter
from s2s.models.gateway import ModelGateway
from s2s.org import load_org
from s2s.tools import runner

log = logging.getLogger(__name__)

LIVE_EVENT_TYPES = frozenset({"agent.status", "plan", "tool_call", "tool_result"})


def artifact_dir() -> Path:
    """Content-addressed artifact store (Phase 0: local filesystem). Read at call time."""
    return Path(os.environ.get("S2S_ARTIFACT_DIR", "/tmp/s2s-artifacts"))


@dataclass
class StepContext:
    """What a step can do. Everything it writes goes into the step's transaction."""
    session: Session
    task: Task
    state: dict[str, Any]
    gateway: ModelGateway
    step_index: int
    step_count: int
    evidence: str | None = None  # measurable progress signal for this step's heartbeat

    @property
    def workdir(self) -> Path:
        """The run's working folder (spec/, arch/, rtl/, reports/, logs/); EDA tools mount it."""
        return artifact_dir() / "runs" / self.task.run_id

    @property
    def ref(self) -> meter.TaskRef:
        t = self.task
        return meter.TaskRef(t.id, t.run_id, t.agent_id, t.stage, t.team_id, dict(t.budget or {}))

    def emit(self, type: str, summary: str, **kw: Any) -> dict:
        """Live action events (status, plan, tool started/finished) publish immediately; all
        others are state events committed with the step (see s2s.events.bus)."""
        t = self.task
        kw.setdefault("agent_id", t.agent_id)
        kw.setdefault("team", t.team_id)
        kw.setdefault("immediate", type in LIVE_EVENT_TYPES)
        return emit(self.session, type, summary, run_id=t.run_id, design_id=t.inputs.get("design_id"),
                    stage=t.stage, task_id=t.id, **kw)

    def model(self, prompt: str, system: str = "You are an S2S engineer agent.") -> str:
        return self.gateway.complete(task=self.ref, system=system,
                                     messages=[{"role": "user", "content": prompt}]).text

    def beat(self, evidence: str) -> None:
        """A heartbeat from inside a long step (e.g. a 20-minute regression): progress evidence is
        committed at once in its own short transaction, so the watchdog sees a live task. The step's
        own transaction still commits the checkpoint at the end."""
        from s2s.db.session import session as own_session
        with own_session() as s:
            t = s.get(Task, self.task.id, with_for_update={"key_share": True})
            now = utcnow()
            t.last_progress_at, t.evidence_signal, t.stalled_at = now, evidence[:200], None
            s.add(Heartbeat(task_id=t.id, percent=t.percent, evidence_signal=evidence[:200],
                            step=f"step {self.step_index + 1}/{self.step_count} (in progress)", blockers=[]))
        self.emit("task.heartbeat", f"{self.task.agent_id}: {evidence[:160]}", status="working", immediate=True,
                  progress=self.task.percent, detail={"step": self.step_index + 1, "of": self.step_count,
                                                       "evidence_signal": evidence, "in_step": True})

    def compute(self, tool: str, cpu_seconds: float, agent_id: str | None = None) -> None:
        ref = self.ref if not agent_id else dataclasses.replace(self.ref, agent_id=agent_id)
        meter.record_compute(ref, cpu_seconds, tool)

    def artifact(self, kind: str, path: str, content: bytes, agent_id: str | None = None,
                 team: str | None = None) -> str:
        sha = hashlib.sha256(content).hexdigest()
        store = artifact_dir()
        store.mkdir(parents=True, exist_ok=True)
        blob = store / sha
        if not blob.exists():  # content-addressed and never overwritten
            blob.write_bytes(content)
        if self.session.get(Artifact, sha) is None:
            self.session.add(Artifact(sha256=sha, kind=kind, path=path, size=len(content),
                                      created_by_task=self.task.id))
        who = agent_id or self.task.agent_id
        self.emit("artifact.created", f"{who} wrote {path}",
                  detail={"path": path, "kind": kind, "artifacts": [f"sha256:{sha}"], "size": len(content)},
                  **{k: v for k, v in (("agent_id", agent_id), ("team", team)) if v})
        return sha

    def check(self, name: str, tool: str, passed: bool, metrics: dict, command: str = "",
              agent_id: str | None = None, team: str | None = None) -> bool:
        """Record a deterministic check result; 3 identical failures in a row escalate (Part 6.6.2)."""
        from s2s.ids import new_id
        chk_id = new_id("chk")
        self.session.add(Check(id=chk_id, task_id=self.task.id, check_name=name, tool=tool,
                               command=command, passed=passed, metrics=metrics))
        who = {k: v for k, v in (("agent_id", agent_id), ("team", team)) if v}
        self.emit("check.passed" if passed else "check.failed",
                  f"{name}: {'passed' if passed else 'FAILED'}",
                  detail={"tool": tool, "metrics": metrics, "check_id": chk_id, "command": command}, **who)
        self.state.setdefault("checks_run", []).append(chk_id)
        fails = self.state.setdefault("consecutive_failures", {})
        fails[name] = 0 if passed else fails.get(name, 0) + 1
        if fails[name] == 3:
            chain = load_org().manager_chain(self.task.team_id) if self.task.team_id else []
            target = chain[1] if len(chain) > 1 else (chain[0] if chain else None)
            self.emit("escalation", f"{name} failed 3 times in a row; escalated to {target}",
                      to_agent_id=target, detail={"rule": "same failure 3 times", "check": name})
        return passed


Step = Callable[[StepContext], None]


class Agent:
    """Base class: subclasses return the task's steps."""
    def steps(self, task: Task) -> list[Step]:
        raise NotImplementedError


def tool_pulse(task: Task, step_index: int, step_count: int):
    """(heartbeat callable, interval) for one step while EDA tools run (Phase 1 harness #3). It captures plain values
    only and writes in its own transactions, so tool threads may call it; one beat per interval per task, however
    many threads run tools. Interval: the SLA heartbeat, but at most a third of the task's stall threshold."""
    import threading
    from s2s.config import sla_seconds
    from s2s.orchestrator.watchdog import stall_threshold_s
    every = max(0.05, min(sla_seconds("heartbeat_minutes"), stall_threshold_s(task) / 3))
    tid, agent, team, run_id, stage = task.id, task.agent_id, task.team_id, task.run_id, task.stage
    design_id, percent = (task.inputs or {}).get("design_id"), task.percent
    lock, last = threading.Lock(), [0.0]

    def pulse(evidence: str) -> None:
        import time as _t
        with lock:
            if _t.monotonic() - last[0] < every * 0.9:
                return
            last[0] = _t.monotonic()
        with db_session() as s:
            t = s.get(Task, tid, with_for_update={"key_share": True})
            now = utcnow()
            t.last_progress_at, t.evidence_signal, t.stalled_at = now, evidence[:200], None
            s.add(Heartbeat(task_id=tid, percent=percent, evidence_signal=evidence[:200],
                            step=f"step {step_index + 1}/{step_count} (tool running)", blockers=[]))
        emit(None, "task.heartbeat", f"{agent}: {evidence[:160]}", run_id=run_id, design_id=design_id, stage=stage,
             task_id=tid, agent_id=agent, team=team, status="working", progress=percent, immediate=True,
             detail={"step": step_index + 1, "of": step_count, "evidence_signal": evidence, "in_step": True,
                     "source": "tool runner"})
    return pulse, every


class NeedsHuman(RuntimeError):
    """The stage cannot finish on its own (e.g. blocking Sentinel findings remain, or the same
    check failed three times): the task pauses and a human decides (Sentinel rule, Part 6.6.2)."""


@dataclass
class Outcome:
    status: str  # completed / failed / paused
    detail: dict = field(default_factory=dict)


def run_task(task_id: str, agent: Agent, gateway: ModelGateway | None = None) -> Outcome:
    """Execute (or resume) a task to completion. Returns the final task status.

    Only one process may run a task at a time: an exclusive file lock per task (released by the OS
    if the process dies). A second runner is refused and the refusal is recorded; it never runs the
    task's steps (two runs of one task on the same run folder gave an invalid result once)."""
    from s2s.tools.runner import lock_dir
    lock_dir().mkdir(parents=True, exist_ok=True)
    with open(lock_dir() / f"task_{task_id}.lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            with db_session() as s:
                task = s.get(Task, task_id)
                emit(s, "escalation", f"Refused a second concurrent run of task {task_id}: it is already running "
                     "in another process", run_id=task.run_id, agent_id="Atlas", task_id=task_id, stage=task.stage,
                     detail={"rule": "one runner per task", "pid": os.getpid()})
            return Outcome("refused", {"rule": "one runner per task"})
        return _run_task(task_id, agent, gateway)


def _run_task(task_id: str, agent: Agent, gateway: ModelGateway | None = None) -> Outcome:
    gateway = gateway or ModelGateway()
    with db_session() as s:
        task = s.get(Task, task_id)
        steps = agent.steps(task)
        start = int((task.checkpoint or {}).get("step", 0))
    n = len(steps)
    try:
        for i in range(start, n):
            with db_session() as s:
                # No row lock while the step works (a hung step must not block the stall
                # watchdog); the step's own column updates are written briefly at commit.
                task = s.get(Task, task_id)
                state = dict((task.checkpoint or {}).get("state", {}))
                ctx = StepContext(s, task, state, gateway, i, n)
                pulse, every = tool_pulse(task, i, n)
                with runner.heartbeat_to(pulse, every):
                    steps[i](ctx)
                now = utcnow()
                evidence = ctx.evidence or f"steps_done={i + 1}/{n}"
                task.checkpoint = {"step": i + 1, "state": ctx.state, "at": now.isoformat()}
                task.percent = round((i + 1) / n, 4)
                task.evidence_signal = evidence
                task.last_progress_at = now
                task.stalled_at = None
                task.usage = meter.task_usage(s, task.id)
                s.add(Heartbeat(task_id=task.id, percent=task.percent, evidence_signal=evidence,
                                step=steps[i].__name__, blockers=[]))
                ctx.emit("task.heartbeat", f"{task.agent_id}: {task.percent:.0%} ({evidence})",
                         progress=task.percent, status="working",
                         detail={"step": i + 1, "of": n, "step_name": steps[i].__name__,
                                 "evidence_signal": evidence})
    except meter.BudgetExceeded as e:
        return _finish(task_id, "paused", "blocked", "escalation",
                       f"Hard budget stop: {e}; task paused for approval",
                       {"budget": e.what, "used": e.used, "limit": e.limit, "rule": "hard stop"})
    except NeedsHuman as e:
        return _finish(task_id, "paused", "blocked", "escalation", f"Needs a human: {e}",
                       {"rule": "needs human", "reason": str(e)}, to_human=True)
    except Exception as e:  # noqa: BLE001 - any agent crash fails the task, visibly
        log.exception("task %s failed", task_id)
        return _finish(task_id, "failed", "blocked", "escalation", f"Task failed: {e!r}",
                       {"error": repr(e)})
    return _finish(task_id, "completed", "idle", "task.completed", None, {})


def _finish(task_id: str, status: str, agent_status: str, event: str, summary: str | None,
            detail: dict, to_human: bool = False) -> Outcome:
    with db_session() as s:
        task = s.get(Task, task_id, with_for_update=True)
        task.status = status
        task.ended_at = utcnow() if status in ("completed", "failed") else None
        task.usage = meter.task_usage(s, task.id)
        task.lease_owner = None
        if status == "completed":
            task.outputs = {**(task.outputs or {}), "checkpoint_steps": task.checkpoint.get("step")}
        ctx = StepContext(s, task, {}, None, 0, 0)
        if event == "task.completed":
            ctx.emit("task.completed", f"{task.agent_id} completed: {task.title}", progress=1.0,
                     status="idle", detail={"usage": task.usage})
        else:
            chain = load_org().manager_chain(task.team_id) if task.team_id else []
            ctx.emit(event, summary, to_agent_id="human" if to_human else (chain[0] if chain else None),
                     detail=detail)
        # final status is part of the task's final state: committed with it, not ahead of it
        ctx.emit("agent.status", f"{task.agent_id} is {agent_status}", status=agent_status, immediate=False)
    return Outcome(status, detail)
