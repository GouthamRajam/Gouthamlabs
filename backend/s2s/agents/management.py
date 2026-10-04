"""Generic director / manager runtime (MASTER_SPEC Appendix A3.1, A3.2; Part 6.6.2), M0.5.

Phase 0 runs these loops as rules from config/management.yaml, not as model calls: assignment,
SLA tracking, stall handling and spot checks are mechanical and must be cheap and reliable.
The A3.1/A3.2 prompts are stored in agents/prompts for the model-driven reports of M0.9.

The manager of a task is the first entry of its team's manager chain (department manager, else
the division director): Reid for the RTL teams, Juno for Spec and Micro-architecture.

Manager (A3.2):
  1. assign: every task the orchestrator starts gets an assignment brief from its manager (goal,
     inputs, exit criteria, expected duration, budget, progress signal). A task that waited
     longer than sla.assign_ready_task_minutes is reported to the director.
  2. check-ins: s2s.orchestrator.watchdog (manager.checkin every manager_checkin_minutes).
  3. stall: once the watchdog flags a stall, the manager reviews the task: if no worker is
     running it any more, it is reassigned (back to ready, resumes from its checkpoint);
     otherwise it is escalated to the director.
  4. spot check: every completed task's outputs are re-hashed against its task.result (100% in
     Phase 0); a mismatch is a finding escalated to the director.
Director (A3.1):
  - every sla.director_review_minutes (default 60) of active work: a division review with
    backlog, running, stalls, assignment-SLA hit rate and cost.
  - escalations from managers that stay unresolved for escalate_to_human_after_minutes go to
    the division's human owner.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
from decimal import Decimal

from sqlalchemy import func, select

from s2s.config import management, settings, sla_seconds
from s2s.db.models import Event, Run, Task, UsageRecord
from s2s.db.session import session as db_session
from s2s.events.bus import emit, utcnow
from s2s.org import load_org


def manager_of(team_id: str | None) -> str | None:
    chain = load_org().manager_chain(team_id) if team_id else []
    return chain[0] if chain else None


def escalation_target(team_id: str | None) -> str:
    """Where a manager escalates: the next level up (the director); a director who manages the
    team directly escalates to Atlas (program office: capacity and cross-division issues)."""
    chain = load_org().manager_chain(team_id) if team_id else []
    return chain[1] if len(chain) > 1 else "Atlas"


def _base(t: Task, run: Run | None = None) -> dict:
    return dict(run_id=t.run_id, task_id=t.id, stage=t.stage,
                design_id=(run.design_id if run else t.inputs.get("design_id")))


def on_assign(s, t: Task, run: Run) -> None:
    """Manager loop item 1, called by the orchestrator in the transaction that starts the task."""
    mgr = manager_of(t.team_id)
    if not mgr:
        return
    waited = (t.assigned_at - t.ready_at).total_seconds() if t.ready_at and t.assigned_at else 0.0
    sla = sla_seconds("assign_ready_task_minutes")
    budget = t.budget or {}
    emit(s, "handoff", f"{mgr} assigned '{t.title}' to {t.agent_id}", agent_id=mgr, team=t.team_id,
         to_agent_id=t.agent_id, **_base(t, run),
         detail={"goal": t.title, "inputs": t.inputs.get("artifacts", ["design request"]),
                 "exit_criteria": t.inputs.get("exit_criteria", ["all stage checks pass in the Trust Layer"]),
                 "expected_minutes": round(t.expected_step_seconds / 60, 2), "budget": budget,
                 "progress_signal": "steps done / steps planned (heartbeat evidence)",
                 "waited_s": round(waited, 3), "assign_sla_s": sla, "within_sla": waited <= sla})
    if waited > sla:
        emit(s, "escalation", f"{mgr}: '{t.title}' waited {waited:.0f}s for assignment (SLA {sla:.0f}s)",
             agent_id=mgr, team=t.team_id, to_agent_id=escalation_target(t.team_id), **_base(t, run),
             detail={"rule": "assignment SLA missed", "waited_s": waited, "sla_s": sla})


def _already(s, task_id: str, rule: str) -> bool:
    return s.scalar(select(func.count()).select_from(Event).where(
        Event.task_id == task_id, Event.detail["rule"].astext == rule)) > 0


def tick(inflight: set[str] | None = None, now: dt.datetime | None = None) -> dict[str, int]:
    """One pass of every manager and director loop. `inflight`: task ids a worker is running now."""
    now = now or utcnow()
    inflight = inflight or set()
    done = {"assign_sla_flags": 0, "reassigned": 0, "stall_escalations": 0, "spot_checks": 0,
            "spot_check_failures": 0, "director_reviews": 0, "to_human": 0}
    sla = sla_seconds("assign_ready_task_minutes")
    with db_session() as s:
        ready = s.scalars(select(Task).where(Task.status == "ready")).all()
        for t in ready:  # waiting too long for assignment (e.g. no free worker)
            if t.ready_at and (now - t.ready_at).total_seconds() > sla and not _already(s, t.id, "assignment SLA at risk"):
                mgr = manager_of(t.team_id)
                emit(s, "escalation", f"{mgr}: '{t.title}' ready for {(now - t.ready_at).total_seconds():.0f}s and "
                     f"not assigned (SLA {sla:.0f}s); asking for capacity", agent_id=mgr, team=t.team_id,
                     to_agent_id=escalation_target(t.team_id), **_base(t),
                     detail={"rule": "assignment SLA at risk", "sla_s": sla})
                done["assign_sla_flags"] += 1
    with db_session() as s:  # stall handling (watchdog flagged the stall)
        stalled = s.scalars(select(Task).where(Task.status == "running", Task.stalled_at.is_not(None))
                            .with_for_update(skip_locked=True)).all()
        for t in stalled:
            if _already(s, t.id, f"stall handled {t.stalled_at.isoformat()}"):
                continue
            mgr = manager_of(t.team_id)
            rule = f"stall handled {t.stalled_at.isoformat()}"
            if t.id not in inflight:
                t.status, t.lease_owner, t.ready_at = "ready", None, now
                emit(s, "handoff", f"{mgr} reviewed stalled '{t.title}': no worker is running it; reassigned "
                     f"(resumes at step {(t.checkpoint or {}).get('step', 0)})", agent_id=mgr, team=t.team_id,
                     to_agent_id=t.agent_id, **_base(t),
                     detail={"rule": rule, "action": "reassign", "evidence_signal": t.evidence_signal})
                done["reassigned"] += 1
            else:
                emit(s, "escalation", f"{mgr} reviewed stalled '{t.title}': worker still running with no "
                     f"progress ({t.evidence_signal or 'no evidence'}); escalated to {escalation_target(t.team_id)}",
                     agent_id=mgr, team=t.team_id, to_agent_id=escalation_target(t.team_id), **_base(t),
                     detail={"rule": rule, "action": "escalate", "evidence_signal": t.evidence_signal})
                done["stall_escalations"] += 1
    with db_session() as s:  # spot checks on completed outputs (100% in Phase 0)
        completed = s.scalars(select(Task).where(Task.status == "completed")).all()
        for t in completed:
            result_path = (t.outputs or {}).get("task_result")
            if not result_path or _already(s, t.id, "spot check"):
                continue
            ok, bad = _spot_check(t)
            mgr = manager_of(t.team_id)
            emit(s, "manager.checkin", f"{mgr} spot-checked {t.agent_id}'s '{t.title}': "
                 + ("all output hashes match" if ok else f"{len(bad)} output(s) changed after the result"),
                 agent_id=mgr, team=t.team_id, to_agent_id=t.agent_id, **_base(t),
                 detail={"rule": "spot check", "passed": ok, "mismatches": bad})
            done["spot_checks"] += 1
            if not ok:
                done["spot_check_failures"] += 1
                emit(s, "escalation", f"{mgr}: outputs of '{t.title}' do not match its task.result", agent_id=mgr,
                     team=t.team_id, to_agent_id=escalation_target(t.team_id), **_base(t),
                     detail={"rule": "spot check failed", "mismatches": bad})
    done["director_reviews"] = _director_reviews(now)
    done["to_human"] = _forward_to_humans(now)
    return done


def _spot_check(t: Task) -> tuple[bool, list[str]]:
    from s2s.agents.runtime import artifact_dir
    root = artifact_dir() / "runs" / t.run_id
    try:
        result = json.loads((root / t.outputs["task_result"]).read_text())
    except (OSError, ValueError):
        return False, [t.outputs["task_result"]]
    bad = [o["path"] for o in result.get("outputs", [])
           if not (root / o["path"]).exists() or hashlib.sha256((root / o["path"]).read_bytes()).hexdigest() != o["sha256"]]
    return not bad, bad


_last_review: dict[str, float] = {}


def _director_reviews(now: dt.datetime) -> int:
    every = 60.0 * float(management()["sla"].get("director_review_minutes", 60))
    org, n = load_org(), 0
    with db_session() as s:
        active = s.scalars(select(Task).join(Run, Run.id == Task.run_id).where(Run.status == "running")).all()
        divisions: dict[str, list[Task]] = {}
        for t in active:
            if t.team_id:
                divisions.setdefault(org.division_of(t.team_id).id, []).append(t)
        for div_id, tasks in divisions.items():
            director = org.by_id(div_id).manager_agent_id
            key = f"{settings().database_url}|{div_id}"
            if not director or time.monotonic() - _last_review.get(key, -1e18) < every:
                continue
            if not any(t.status in ("ready", "running") for t in tasks):
                continue
            _last_review[key] = time.monotonic()
            assigned = [t for t in tasks if t.assigned_at and t.ready_at]
            sla = sla_seconds("assign_ready_task_minutes")
            hit = sum((t.assigned_at - t.ready_at).total_seconds() <= sla for t in assigned)
            cost = s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                            .where(UsageRecord.task_id.in_([t.id for t in tasks])))
            counts = {k: sum(t.status == k for t in tasks) for k in ("pending", "ready", "running", "completed",
                                                                     "paused", "failed")}
            stalls = sum(t.stalled_at is not None for t in tasks)
            emit(s, "manager.checkin", f"{director} division review: {counts['running']} running, "
                 f"{counts['ready'] + counts['pending']} backlog, {stalls} stalled, assignment SLA "
                 f"{hit}/{len(assigned)}, cost ${Decimal(str(cost)):.4f}", agent_id=director,
                 team=None, run_id=tasks[0].run_id,
                 detail={"rule": "director review", "division": div_id, "tasks": counts, "stalls": stalls,
                         "assign_sla_hit": hit, "assigned": len(assigned), "cost_usd": float(cost)})
            n += 1
    return n


def _forward_to_humans(now: dt.datetime) -> int:
    """Director: a manager escalation still open after escalate_to_human_after_minutes goes to the
    division's human owner (once)."""
    after = sla_seconds("escalate_to_human_after_minutes")
    org, n = load_org(), 0
    with db_session() as s:
        evs = s.scalars(select(Event).where(Event.type == "escalation", Event.task_id.is_not(None),
                                            Event.detail["rule"].astext.in_(("assignment SLA at risk",
                                                                             "assignment SLA missed",
                                                                             "spot check failed")))).all()
        for e in evs:
            t = s.get(Task, e.task_id)
            if t is None or (now - e.ts).total_seconds() < after or _already(s, t.id, f"to human {e.id}"):
                continue
            if e.detail.get("rule", "").startswith("assignment") and t.status != "ready":
                continue  # resolved: the task was assigned
            div = org.division_of(t.team_id)
            emit(s, "escalation", f"{div.manager_agent_id}: unresolved after {after:.0f}s - {e.summary}",
                 agent_id=div.manager_agent_id, team=t.team_id, to_agent_id="human", **_base(t),
                 detail={"rule": f"to human {e.id}", "human_owner": div.human_owner, "original": e.summary})
            n += 1
    return n
