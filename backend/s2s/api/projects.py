"""Project view API (web /projects): per design, the whole flow across all of its runs.

GET  /projects                               projects with their designs, newest activity first
GET  /designs/{id}/overview                  the 10 stages (Part 5 flow) with status, owner, checks,
                                             gate, spend and time; current activity; timeline; spend
GET  /designs/{id}/stages/{stage}/events     the stage's log (its events, oldest first)
POST /projects/requests                      new project + design from a plain-English request
                                             (creates records only; starting a run is a separate,
                                             explicit POST /designs/{id}/runs)

Read-only views of the Trust Layer records: every status shown comes from a task, a check (a real
tool result) or a gate record. Nothing here decides pass/fail.
"""
from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from s2s.config import spend_caps
from s2s.db.models import Check, Design, Event, Gate, Project, Run, Task, UsageRecord
from s2s.ids import new_id
from s2s.orchestrator import flow
from s2s.org import load_org

router = APIRouter()
ZONES = {"spec": "1", "architecture": "1", "rtl": "2A", "test_build": "2B", "verification": "2C", "synthesis": "3",
         "dft": "3", "floorplan": "3", "place_route": "3", "signoff": "4", "gdsii": "4"}
QUIET = ("task.heartbeat", "agent.status", "manager.checkin")


def _db():
    from s2s.api.app import db  # the app's session dependency (commit on success)
    yield from db()


def _iso(v) -> str | None:
    return v.isoformat() if v is not None else None


def _runs_of(s: Session, design_id: str) -> list[Run]:
    return list(s.scalars(select(Run).where(Run.design_id == design_id).order_by(Run.started_at)))


def _last_activity(s: Session, design_id: str):
    return s.scalar(select(func.max(Event.ts)).where(Event.design_id == design_id))


def _spend(s: Session, run_ids: list[str]) -> float:
    if not run_ids:
        return 0.0
    v = s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0)).where(UsageRecord.run_id.in_(run_ids)))
    return float(Decimal(str(v)))


@router.get("/projects")
def list_projects(s: Session = Depends(_db)) -> list[dict]:
    out = []
    for p in s.scalars(select(Project)):
        designs = []
        for d in s.scalars(select(Design).where(Design.project_id == p.id)):
            runs = _runs_of(s, d.id)
            running = s.scalar(select(Task).where(Task.run_id.in_([r.id for r in runs] or [""]),
                                                  Task.status.in_(("running", "ready"))))
            paused = s.scalar(select(Task).where(Task.run_id.in_([r.id for r in runs] or [""]), Task.status == "paused"))
            last = _last_activity(s, d.id)
            designs.append({"id": d.id, "name": d.name, "pdk": d.pdk, "created_at": _iso(d.created_at),
                            "runs": len(runs), "spend_usd": round(_spend(s, [r.id for r in runs]), 4),
                            "state": "running" if running else ("needs you" if paused else ("idle" if runs else "new")),
                            "current_stage": running.stage if running else (paused.stage if paused else None),
                            "last_activity": _iso(last)})
        last = max((d["last_activity"] or d["created_at"] or "" for d in designs), default=_iso(p.created_at))
        out.append({"id": p.id, "name": p.name, "owner": p.owner, "created_at": _iso(p.created_at),
                    "last_activity": last, "designs": designs})
    return sorted(out, key=lambda p: p["last_activity"] or "", reverse=True)


def _stage_status(task: Task | None, checks: dict[str, Check], gate: Gate | None) -> str:
    if task is None:
        return "not started"
    if task.status == "running":
        return "running"
    if task.status in ("ready", "pending"):
        return "queued"
    if task.status == "paused":
        return "needs you"
    if task.status == "failed":
        return "failed"
    failed = [c for c in checks.values() if not c.passed]
    if failed:
        return "failed"
    if gate is not None and gate.status == "pending":
        return "awaiting gate"
    if gate is not None and gate.status == "rejected":
        return "failed"
    return "passed"


@router.get("/designs/{design_id}/overview")
def design_overview(design_id: str, s: Session = Depends(_db)) -> dict:
    d = s.get(Design, design_id)
    if d is None:
        raise HTTPException(404, f"design {design_id!r} not found")
    p = s.get(Project, d.project_id)
    runs = _runs_of(s, d.id)
    run_ids = [r.id for r in runs]
    tasks = list(s.scalars(select(Task).where(Task.run_id.in_(run_ids or [""]))))
    run_start = {r.id: r.started_at for r in runs}
    by_stage: dict[str, list[Task]] = defaultdict(list)
    for t in tasks:
        by_stage[t.stage].append(t)
    gates = list(s.scalars(select(Gate).where(Gate.run_id.in_(run_ids or [""]))))
    org = load_org()
    usage_by_task = dict(s.execute(select(UsageRecord.task_id, func.sum(UsageRecord.cost_usd))
                                   .where(UsageRecord.run_id.in_(run_ids or [""])).group_by(UsageRecord.task_id)).all())
    usage_by_agent = dict(s.execute(select(UsageRecord.agent_id, func.sum(UsageRecord.cost_usd))
                                    .where(UsageRecord.run_id.in_(run_ids or [""])).group_by(UsageRecord.agent_id)).all())
    ev_counts = dict(s.execute(select(Event.stage, func.count()).where(Event.run_id.in_(run_ids or [""]))
                               .group_by(Event.stage)).all())
    stages = []
    for st in flow.STAGES:
        attempts = sorted(by_stage.get(st.name, []), key=lambda t: (run_start.get(t.run_id) or t.started_at, t.seq))
        task = attempts[-1] if attempts else None
        checks_all = list(s.scalars(select(Check).where(Check.task_id == task.id).order_by(Check.id))) if task else []
        latest: dict[str, Check] = {}
        history: dict[str, int] = defaultdict(int)
        for c in checks_all:
            latest[c.check_name] = c
            history[c.check_name] += 1
        gate = None
        if st.gate_after and task:
            gate = next((g for g in gates if g.run_id == task.run_id and g.after_stage == st.name), None)
        steps = None
        if task is not None:
            try:
                from s2s.agents.m05 import DesignAgent
                import s2s.agents.m06  # noqa: F401
                import s2s.agents.m07  # noqa: F401
                fn = DesignAgent.STAGES.get(st.name)
                steps = [getattr(x, "__name__", "step") for x in fn()] if fn else None
            except Exception:  # noqa: BLE001 - the view must not fail on an import problem
                steps = None
        lead_unit = org.by_id(st.team_id)
        stages.append({
            "name": st.name, "title": st.title, "zone": ZONES.get(st.name), "team": st.team_id,
            "lead": lead_unit.manager_agent_id if lead_unit else None, "gate_after": st.gate_after,
            "status": _stage_status(task, latest, gate),
            "task": None if task is None else {
                "id": task.id, "run_id": task.run_id, "agent_id": task.agent_id, "status": task.status,
                "attempts": task.attempts, "percent": task.percent, "evidence": task.evidence_signal,
                "started_at": _iso(task.started_at), "ended_at": _iso(task.ended_at),
                "last_progress_at": _iso(task.last_progress_at), "stalled_at": _iso(task.stalled_at),
                "checkpoint_step": (task.checkpoint or {}).get("step", 0), "steps": steps,
                "usage": task.usage},
            "earlier_attempts": [{"run_id": t.run_id, "status": t.status, "started_at": _iso(t.started_at),
                                  "ended_at": _iso(t.ended_at)} for t in attempts[:-1]],
            "checks": [{"name": n, "passed": c.passed, "tool": c.tool, "command": (c.command or "")[:400],
                        "records": history[n], "metrics": _short(c.metrics)} for n, c in latest.items()],
            "checks_passed": sum(1 for c in latest.values() if c.passed),
            "checks_failed": sum(1 for c in latest.values() if not c.passed),
            "gate": None if gate is None else {"gate": gate.gate, "status": gate.status, "reviewer": gate.reviewer,
                                               "decided_at": _iso(gate.decided_at), "comments": gate.comments},
            "spend_usd": round(sum(float(usage_by_task.get(t.id, 0) or 0) for t in attempts), 4),
            "events": ev_counts.get(st.name, 0),
        })
    cur = next((x for x in stages if x["status"] in ("running", "queued", "needs you")), None)
    timeline: list[dict] = []
    for r in runs:
        timeline.append({"ts": _iso(r.started_at), "kind": "run", "label": f"Run started ({', '.join(r.stages)})",
                         "run_id": r.id})
    for t in tasks:
        if t.started_at:
            timeline.append({"ts": _iso(t.started_at), "kind": "stage", "label": f"{t.stage} started ({t.agent_id})",
                             "run_id": t.run_id})
        if t.ended_at:
            timeline.append({"ts": _iso(t.ended_at), "kind": "stage_end", "label": f"{t.stage} {t.status}",
                             "run_id": t.run_id})
    for g in gates:
        if g.decided_at:
            timeline.append({"ts": _iso(g.decided_at), "kind": "gate",
                             "label": f"{g.gate} {g.status} ({g.reviewer or 'pending'})", "run_id": g.run_id})
    for e in s.scalars(select(Event).where(Event.run_id.in_(run_ids or [""]), Event.type == "escalation")
                       .order_by(Event.ts)):
        timeline.append({"ts": _iso(e.ts), "kind": "escalation", "label": f"{e.agent_id}: {e.summary[:180]}",
                         "run_id": e.run_id})
    timeline.sort(key=lambda x: x["ts"] or "")
    total = _spend(s, run_ids)
    cap = spend_caps().get("per_design_usd")
    outputs = _outputs(runs)
    return {
        "design": {"id": d.id, "name": d.name, "pdk": d.pdk, "target_clock_mhz": d.target_clock_mhz,
                   "request_text": d.request_text, "created_at": _iso(d.created_at), "status": d.status},
        "project": {"id": p.id, "name": p.name, "owner": p.owner} if p else None,
        "runs": [{"id": r.id, "status": r.status, "stages": r.stages, "started_at": _iso(r.started_at),
                  "ended_at": _iso(r.ended_at), "current_stage": r.current_stage} for r in runs],
        "stages": stages,
        "current": None if cur is None else {"stage": cur["name"], "status": cur["status"], **(cur["task"] or {})},
        "timeline": timeline[-200:],
        "spend": {"total_usd": round(total, 4), "cap_usd": cap,
                  "by_agent": {a: round(float(v), 4) for a, v in usage_by_agent.items() if a},
                  "by_stage": {x["name"]: x["spend_usd"] for x in stages if x["spend_usd"]}},
        "outputs": outputs,
        "summary": {"passed": sum(1 for x in stages if x["status"] == "passed"),
                    "failed": sum(1 for x in stages if x["status"] == "failed"),
                    "stages": len(stages)},
    }


OUTPUT_FILES = (  # (label, path in the run folder); the GDSII is the deliverable
    ("GDSII (final layout)", "tapeout/gds/{top}.gds"),
    ("Tape-out readiness report", "reports/tapeout_readiness.md"),
    ("Tape-out checklist (B.9)", "reports/tapeout_checklist.md"),
    ("DFM scorecard", "reports/dfm_scorecard.md"),
    ("Release notes", "tapeout/release_notes.md"),
    ("reproduce.sh", "tapeout/reproduce.sh"),
    ("Manifest (SHA-256)", "tapeout/MANIFEST.sha256"),
    ("Final netlist", "tapeout/netlist/{top}.nl.v"),
    ("Constraints (SDC)", "tapeout/constraints/constraints.sdc"),
)


def _top_of(run_dir) -> str | None:
    import yaml
    a = run_dir / "arch" / "arch.yaml"
    try:
        return yaml.safe_load(a.read_text())["top"] if a.exists() else None
    except Exception:  # noqa: BLE001
        return None


def _outputs(runs: list[Run]) -> list[dict]:
    """Files of the newest run that produced a tape-out package (GDSII first)."""
    from s2s.agents.runtime import artifact_dir
    for r in reversed(runs):
        rd = artifact_dir() / "runs" / r.id
        top = _top_of(rd)
        if not top or not (rd / "tapeout").exists():
            continue
        out = []
        for label, rel in OUTPUT_FILES:
            p = rd / rel.format(top=top)
            if p.exists():
                out.append({"label": label, "path": rel.format(top=top), "run_id": r.id, "bytes": p.stat().st_size})
        return out
    return []


@router.get("/runs/{run_id}/files/{path:path}")
def run_file(run_id: str, path: str, s: Session = Depends(_db)):
    """Download an output file of a run (only the tape-out outputs listed above)."""
    from fastapi.responses import FileResponse
    from s2s.agents.runtime import artifact_dir
    if s.get(Run, run_id) is None:
        raise HTTPException(404, f"run {run_id!r} not found")
    rd = artifact_dir() / "runs" / run_id
    allowed = {rel.format(top=_top_of(rd) or "") for _, rel in OUTPUT_FILES}
    if path not in allowed:
        raise HTTPException(403, "only tape-out output files can be downloaded here")
    p = rd / path
    if not p.is_file():
        raise HTTPException(404, f"{path} does not exist for run {run_id}")
    return FileResponse(p, filename=p.name)


@router.get("/runs/{run_id}/layout3d")
def run_layout3d(run_id: str):
    """3D layer geometry of the run's GDSII (tape-out package, else the final P&R GDS), built once by
    KLayout from the GDS and the PDK's own layer stack, then cached next to it."""
    from fastapi.responses import Response
    from s2s.agents.runtime import artifact_dir
    from s2s.physical.layout3d import layout3d
    if not re.fullmatch(r"run_[0-9A-Za-z]{10,40}", run_id):
        raise HTTPException(422, "bad run id")
    rd = artifact_dir() / "runs" / run_id
    top = _top_of(rd)
    if not top:
        raise HTTPException(404, f"run {run_id} has no design files")
    gds = rd / "tapeout" / "gds" / f"{top}.gds"
    if not gds.exists():
        finals = sorted((rd / "pnr" / "runs").glob(f"*/final/gds/{top}.gds")) if (rd / "pnr" / "runs").exists() else []
        if not finals:
            raise HTTPException(404, f"run {run_id} has no GDSII yet")
        gds = finals[-1]
    cache = rd / "signoff" / "layout3d.json"
    if not cache.exists() or cache.stat().st_mtime < gds.stat().st_mtime:
        try:
            layout3d(gds, top, rd, cache)
        except RuntimeError as e:
            raise HTTPException(500, str(e)) from None
    return Response(content=cache.read_bytes(), media_type="application/json")  # written atomically by layout3d


def _short(m: dict[str, Any] | None) -> dict:
    """Small, readable metric subset for the stage table (full records stay in the database)."""
    out = {}
    for k, v in (m or {}).items():
        if isinstance(v, (int, float, bool, str)) and len(str(v)) <= 160:
            out[k] = v
        elif isinstance(v, list) and len(v) <= 6 and all(isinstance(x, (int, float, str)) for x in v):
            out[k] = v
        if len(out) >= 8:
            break
    return out


@router.get("/designs/{design_id}/stages/{stage}/events")
def stage_events(design_id: str, stage: str, limit: int = Query(400, le=2000), quiet: bool = False,
                 s: Session = Depends(_db)) -> list[dict]:
    if stage not in flow.STAGE_NAMES:
        raise HTTPException(422, f"unknown stage {stage!r}")
    run_ids = [r.id for r in _runs_of(s, design_id)]
    q = select(Event).where(Event.run_id.in_(run_ids or [""]), Event.stage == stage)
    if not quiet:
        q = q.where(Event.type.not_in(QUIET))
    rows = list(s.scalars(q.order_by(Event.ts.desc(), Event.id.desc()).limit(limit)))
    return [{"id": e.id, "ts": _iso(e.ts), "type": e.type, "agent_id": e.agent_id, "to_agent_id": e.to_agent_id,
             "summary": e.summary, "status": e.status, "run_id": e.run_id,
             "detail": _short(e.detail)} for e in reversed(rows)]


class NewRequestIn(BaseModel):
    project_name: str = Field(min_length=1, max_length=120)
    design_name: str = Field(min_length=1, max_length=64)
    request_text: str = Field(min_length=10, max_length=8000)
    target_clock_mhz: float | None = Field(default=None, gt=0, le=2000)
    owner: str | None = Field(default=None, max_length=120)


@router.post("/projects/requests", status_code=201)
def new_request(body: NewRequestIn, s: Session = Depends(_db)) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", body.design_name):
        raise HTTPException(422, "design name: lower case letters, digits and _ (it becomes the Verilog top name), "
                                 "starting with a letter")
    p = Project(id=new_id("prj"), name=body.project_name.strip(), owner=body.owner)
    s.add(p)
    s.flush()
    d = Design(id=new_id("des"), project_id=p.id, name=body.design_name, pdk="sky130A",
               target_clock_mhz=body.target_clock_mhz, request_text=body.request_text.strip(),
               options={"created_from": "web /projects"}, status="created")
    s.add(d)
    s.flush()
    return {"project": {"id": p.id, "name": p.name}, "design": {"id": d.id, "name": d.name},
            "next": f"POST /designs/{d.id}/runs with agent_kind 's2s' starts spec -> architecture -> RTL"}
