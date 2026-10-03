"""S2S API (MASTER_SPEC Part 7.7) and the live event stream WS /ws/events (Part 11.3)."""
from __future__ import annotations

import asyncio
import json
import os
from decimal import Decimal
from typing import Any

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from s2s.agents.runtime import artifact_dir
from s2s.config import management, save_spend_caps, settings, sla_seconds, spend_caps
from s2s.db.models import (Artifact, Budget, BudgetEvent, Credit, Design, Event, EvidencePacket, Gate,
                           OrgUnit, Project, ResearchBrief, Run, Task, TeamMetric, UsageRecord)
from s2s.db.session import session_factory
from s2s.events.bus import emit, utcnow
from s2s.finance import meter
from s2s.models import access
from s2s.ids import new_id
from s2s.orchestrator import flow
from s2s.orchestrator.engine import create_run
from s2s.org import load_org

app = FastAPI(title="S2S API", version="0.4.0")
# The Live Office (web app, M0.4) runs on its own origin and calls this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get(
        "S2S_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["content-type"],
)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError):
    # Settings bodies can carry an API key: never echo submitted values back (FastAPI's default
    # 422 body includes each invalid field's input).
    if request.url.path.startswith("/settings"):
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]})
    return await request_validation_exception_handler(request, exc)


def db() -> Session:
    s = session_factory()()
    try:
        yield s
        s.commit()
    except BaseException:
        s.rollback()
        raise
    finally:
        s.close()


def _row(obj: Any) -> dict:
    out = {}
    for c in obj.__table__.columns:
        v = getattr(obj, c.key)
        out[c.key] = float(v) if isinstance(v, Decimal) else (v.isoformat() if hasattr(v, "isoformat") else v)
    return out


def _get(s: Session, model, key, what: str):
    obj = s.get(model, key)
    if obj is None:
        raise HTTPException(404, f"{what} {key!r} not found")
    return obj


# --- request bodies -------------------------------------------------------------------------
class ProjectIn(BaseModel):
    name: str
    owner: str | None = None


class DesignIn(BaseModel):
    project_id: str
    name: str
    request_text: str
    pdk: str = "sky130A"
    target_clock_mhz: float | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class RunIn(BaseModel):
    from_stage: str | None = None
    to_stage: str | None = None
    agent_kind: str = "dummy"
    dummy: dict[str, Any] = Field(default_factory=dict)  # dummy agent knobs (see s2s.agents.dummy)


class GateDecisionIn(BaseModel):
    decision: str  # approve / reject / approve_with_conditions
    reviewer: str
    comments: str | None = None


# --- projects, designs, runs ------------------------------------------------------------------
@app.get("/health")
def health(s: Session = Depends(db)) -> dict:
    s.execute(select(1))
    return {"status": "ok"}


@app.post("/projects", status_code=201)
def create_project(body: ProjectIn, s: Session = Depends(db)) -> dict:
    p = Project(id=new_id("prj"), name=body.name, owner=body.owner)
    s.add(p)
    s.flush()
    return _row(p)


@app.post("/designs", status_code=201)
def create_design(body: DesignIn, s: Session = Depends(db)) -> dict:
    _get(s, Project, body.project_id, "project")
    d = Design(id=new_id("des"), project_id=body.project_id, name=body.name, pdk=body.pdk,
               target_clock_mhz=body.target_clock_mhz, request_text=body.request_text,
               options=body.options, status="created")
    s.add(d)
    s.flush()
    return _row(d)


@app.post("/designs/{design_id}/runs", status_code=201)
def start_run(design_id: str, body: RunIn, s: Session = Depends(db)) -> dict:
    d = _get(s, Design, design_id, "design")
    for st in (body.from_stage, body.to_stage):
        if st is not None and st not in flow.STAGE_NAMES:
            raise HTTPException(422, f"unknown stage {st!r}; stages: {list(flow.STAGE_NAMES)}")
    try:
        run = create_run(s, d, body.from_stage, body.to_stage, body.agent_kind, body.dummy)
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    d.status = "running"
    return _run_view(s, run)


def _run_view(s: Session, run: Run) -> dict:
    tasks = s.scalars(select(Task).where(Task.run_id == run.id).order_by(Task.seq)).all()
    gates = s.scalars(select(Gate).where(Gate.run_id == run.id)).all()
    return {**_row(run), "tasks": [_task_view(t) for t in tasks], "gates": [_row(g) for g in gates]}


def _task_view(t: Task) -> dict:
    keep = ("id", "run_id", "agent_id", "stage", "title", "status", "seq", "depends_on", "team_id",
            "attempts", "percent", "evidence_signal", "usage", "budget", "started_at", "ended_at",
            "last_progress_at", "stalled_at")
    row = _row(t)
    return {**{k: row[k] for k in keep}, "checkpoint_step": (t.checkpoint or {}).get("step", 0)}


@app.get("/runs")
def list_runs(limit: int = Query(20, le=100), s: Session = Depends(db)) -> list[dict]:
    """Most recent runs first (the Live Office's replay picker)."""
    out = []
    for run in s.scalars(select(Run).order_by(Run.id.desc()).limit(limit)):
        d = s.get(Design, run.design_id)
        n_events = s.scalar(select(func.count()).select_from(Event).where(Event.run_id == run.id))
        out.append({**_row(run), "design_name": d.name if d else None, "events": n_events})
    return out


@app.get("/runs/{run_id}")
def get_run(run_id: str, s: Session = Depends(db)) -> dict:
    return _run_view(s, _get(s, Run, run_id, "run"))


@app.get("/runs/{run_id}/tasks")
def get_run_tasks(run_id: str, s: Session = Depends(db)) -> list[dict]:
    _get(s, Run, run_id, "run")
    return [_task_view(t) for t in s.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.seq))]


@app.get("/events")
def list_events(run_id: str | None = None, before: str | None = None,
                limit: int = Query(100, le=500), s: Session = Depends(db)) -> list[dict]:
    """Older events by page (newest first), for clients that only keep the last 500 live."""
    q = select(Event).order_by(Event.id.desc()).limit(limit)
    if run_id:
        q = q.where(Event.run_id == run_id)
    if before:
        q = q.where(Event.id < before)
    return [_row(e) for e in s.scalars(q)]


@app.get("/artifacts/{sha}")
def get_artifact(sha: str, s: Session = Depends(db)):
    a = _get(s, Artifact, sha, "artifact")
    blob = artifact_dir() / a.sha256
    if not blob.is_file():
        raise HTTPException(410, f"artifact {sha} is recorded but its content is missing")
    return FileResponse(blob, filename=a.path.rsplit("/", 1)[-1])


@app.get("/runs/{run_id}/evidence/{stage}")
def get_evidence(run_id: str, stage: str, s: Session = Depends(db)) -> dict:
    _get(s, Run, run_id, "run")
    p = s.scalar(select(EvidencePacket).where(EvidencePacket.run_id == run_id, EvidencePacket.stage == stage))
    if p is None:
        raise HTTPException(404, f"no evidence packet for run {run_id} stage {stage!r}")
    return _row(p)


# --- gates ------------------------------------------------------------------------------------------
@app.get("/gates")
def list_gates(status: str | None = None, s: Session = Depends(db)) -> list[dict]:
    q = select(Gate).order_by(Gate.id)
    if status:
        q = q.where(Gate.status == status)
    return [_row(g) for g in s.scalars(q)]


@app.post("/gates/{gate_id}/decision")
def decide_gate(gate_id: str, body: GateDecisionIn, s: Session = Depends(db)) -> dict:
    mapping = {"approve": "approved", "approve_with_conditions": "approved", "reject": "rejected"}
    if body.decision not in mapping:
        raise HTTPException(422, f"decision must be one of {sorted(mapping)}")
    g = s.get(Gate, gate_id, with_for_update=True)
    if g is None:
        raise HTTPException(404, f"gate {gate_id!r} not found")
    if g.status != "pending":
        raise HTTPException(409, f"gate {gate_id} already {g.status}")
    g.status, g.decision, g.reviewer = mapping[body.decision], body.decision, body.reviewer
    g.comments, g.decided_at = body.comments, utcnow()
    run = s.get(Run, g.run_id)
    emit(s, "gate.decided", f"{g.gate} {body.decision.replace('_', ' ')} by {body.reviewer}",
         run_id=g.run_id, design_id=run.design_id, stage=g.after_stage, agent_id="Atlas",
         team="program_office", detail={"gate_id": g.id, "gate": g.gate, "decision": body.decision,
                                        "reviewer": body.reviewer, "mode": "human"})
    return _row(g)


# --- agents and org ---------------------------------------------------------------------------------
def _latest_status(s: Session) -> dict[str, dict]:
    sub = (select(Event.agent_id, func.max(Event.id).label("mid"))
           .where(Event.type == "agent.status").group_by(Event.agent_id).subquery())
    rows = s.execute(select(Event).join(sub, Event.id == sub.c.mid)).scalars().all()
    return {e.agent_id: {"status": e.status, "since": e.ts.isoformat()} for e in rows}


@app.get("/agents")
def list_agents(s: Session = Depends(db)) -> list[dict]:
    status = _latest_status(s)
    running = {t.agent_id: t for t in s.scalars(select(Task).where(Task.status == "running"))}
    return [{**a, "status": status.get(a["id"], {}).get("status", "idle"),
             "current_task": running[a["id"]].id if a["id"] in running else None}
            for a in load_org().agents()]


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str, s: Session = Depends(db)) -> dict:
    agent = next((a for a in load_org().agents() if a["id"] == agent_id), None)
    if agent is None:
        raise HTTPException(404, f"agent {agent_id!r} not found")
    task = s.scalar(select(Task).where(Task.agent_id == agent_id, Task.status == "running"))
    recent = s.scalars(select(Event).where(Event.agent_id == agent_id).order_by(Event.id.desc()).limit(20))
    return {**agent, "status": _latest_status(s).get(agent_id, {}).get("status", "idle"),
            "current_task": _task_view(task) if task else None, "recent_events": [_row(e) for e in recent]}


@app.get("/org")
def get_org(s: Session = Depends(db)) -> dict:
    units = [_row(u) for u in s.scalars(select(OrgUnit))]
    if not units:
        raise HTTPException(503, "org_units is empty: the orchestrator syncs it from config at startup")
    children: dict[str | None, list] = {}
    for u in units:
        children.setdefault(u["parent_id"], []).append(u)

    def tree(u: dict) -> dict:
        return {**u, "children": [tree(c) for c in children.get(u["id"], [])]}

    return {"ceo": management()["org"]["ceo"], "divisions": [tree(u) for u in children.get(None, [])]}


# --- management, finance, research ---------------------------------------------------------------
@app.get("/management/dashboard")
def management_dashboard(s: Session = Depends(db)) -> dict:
    now = utcnow()
    counts = dict(s.execute(select(Task.status, func.count()).group_by(Task.status)).all())
    running = s.scalars(select(Task).where(Task.status == "running")).all()
    ready = s.scalars(select(Task).where(Task.status == "ready")).all()
    assign_sla = sla_seconds("assign_ready_task_minutes")
    assigned = s.scalars(select(Task).where(Task.assigned_at.is_not(None))).all()
    stalls = s.scalars(select(Task).where(Task.stalled_at.is_not(None), Task.status == "running")).all()
    within = sum(1 for t in assigned if t.ready_at and
                 (t.assigned_at - t.ready_at).total_seconds() <= assign_sla)
    return {
        "backlog": {"pending": counts.get("pending", 0), "ready": counts.get("ready", 0)},
        "task_counts": counts,
        "running": [{**_task_view(t), "silent_for_s": round((now - t.last_progress_at).total_seconds(), 1)
                     if t.last_progress_at else None} for t in running],
        "stalls": [_task_view(t) for t in stalls],
        "ready_past_assignment_sla": [t.id for t in ready
                                      if t.ready_at and (now - t.ready_at).total_seconds() > assign_sla],
        "sla": dict(management()["sla"]),
        "assignments": {"count": len(assigned), "sla_s": assign_sla, "within_sla": within,
                        "sla_hit_rate": round(within / len(assigned), 4) if assigned else None},
        "team_metrics": [_row(m) for m in s.scalars(select(TeamMetric))],
    }


@app.get("/finance/summary")
def finance_summary(s: Session = Depends(db)) -> dict:
    def by(col):
        return {k or "unknown": float(v) for k, v in
                s.execute(select(col, func.sum(UsageRecord.cost_usd)).group_by(col)).all()}

    total = float(s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))))
    midnight = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today = float(s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0))
                           .where(UsageRecord.ts >= midnight)))
    budgets = []
    for b in s.scalars(select(Budget)):
        spent = float(s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0)).where(
            {"run": UsageRecord.run_id, "task": UsageRecord.task_id}.get(b.scope, UsageRecord.run_id) == b.scope_id)))
        budgets.append({**_row(b), "spent_usd": spent, "pct": round(100 * spent / float(b.limit_usd), 3)})
    return {
        "total_usd": total,
        "today_usd": today,  # since 00:00 UTC
        "as_of": utcnow().isoformat(),
        "records": s.scalar(select(func.count()).select_from(UsageRecord)),
        "by_source": by(UsageRecord.source), "by_model": by(UsageRecord.model),
        "by_agent": by(UsageRecord.agent_id), "by_run": by(UsageRecord.run_id),
        "budgets": budgets,
        "alerts": [_row(e) for e in s.scalars(select(BudgetEvent).order_by(BudgetEvent.id))],
        "credits": [_row(c) for c in s.scalars(select(Credit))],
        "runway": None,  # needs ledger data (M0.9); not estimated here
    }


@app.get("/research/briefs")
def research_briefs(limit: int = Query(20, le=100), s: Session = Depends(db)) -> list[dict]:
    return [_row(b) for b in s.scalars(select(ResearchBrief).order_by(ResearchBrief.id.desc()).limit(limit))]


# --- live events ------------------------------------------------------------------------------------
def _division_of(ev: dict) -> str | None:
    org = load_org()
    team = ev.get("team")
    if team:
        try:
            return org.division_of(team).id
        except StopIteration:
            pass
    agent = next((a for a in org.agents() if a["id"] == ev.get("agent_id")), None)
    return agent["division_id"] if agent else None


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket, run_id: str | None = None, agent_id: str | None = None,
                    division: str | None = None, since: str | None = None) -> None:
    """Live events from the Redis stream. `since` = a stream id to replay from (default: now)."""
    await ws.accept()
    cfg = settings()
    r = aioredis.from_url(cfg.redis_url, decode_responses=True)
    try:
        if since:
            last = since
        else:  # pin "now" to a concrete id so nothing between reads is skipped
            tail = await r.xrevrange(cfg.event_stream, count=1)
            last = tail[0][0] if tail else "0-0"
        await ws.send_text(json.dumps({"type": "stream.subscribed", "from": last}))
        while True:
            resp = await r.xread({cfg.event_stream: last}, block=1000, count=200)
            for _stream, entries in resp or []:
                for sid, fields in entries:
                    last = sid
                    ev = json.loads(fields["event"])
                    if run_id and ev.get("run_id") != run_id:
                        continue
                    if agent_id and ev.get("agent_id") != agent_id:
                        continue
                    if division and _division_of(ev) != division:
                        continue
                    await ws.send_text(json.dumps({**ev, "stream_id": sid}))
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        await r.aclose()


# --- Settings (MASTER_SPEC Part 28) ---------------------------------------------------------
# Thin Phase 0 version: no login/roles yet (Part 28.5 #4 comes with the hardened version).

class ModelAccessIn(BaseModel):
    provider: str = "anthropic"
    api_key: str | None = Field(default=None, max_length=512)  # write-only; omitted = keep stored key
    endpoint: str | None = Field(default=None, max_length=512)


@app.get("/settings/model-access")
def get_model_access() -> dict:
    return access.public_view()


@app.put("/settings/model-access")
def put_model_access(body: ModelAccessIn) -> dict:
    try:
        return access.save(body.provider, body.api_key, body.endpoint)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None


@app.post("/settings/model-access/test")
def test_model_access() -> dict:
    return access.test_connection()


class SpendCapsIn(BaseModel):
    per_design_usd: float = Field(gt=0, le=1_000_000)
    daily_usd: float = Field(gt=0, le=1_000_000)


def _caps_view(s: Session) -> dict:
    caps = spend_caps()
    return {"per_design_usd": caps.get("per_design_usd"), "daily_usd": caps.get("daily_usd"),
            "spent_today_usd": float(meter.spend_so_far(s)["today_usd"]), "source": "config/finance.yaml"}


@app.get("/settings/spend-caps")
def get_spend_caps(s: Session = Depends(db)) -> dict:
    return _caps_view(s)


@app.put("/settings/spend-caps")
def put_spend_caps(body: SpendCapsIn, s: Session = Depends(db)) -> dict:
    save_spend_caps(body.per_design_usd, body.daily_usd)
    return _caps_view(s)
