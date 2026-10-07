"""Run-to-trajectory exporter (Phase 1 trajectory item 1).

Turns one run into a single ordered, machine-readable trajectory (JSON lines, schema TRAJECTORY_SCHEMA):

    run header -> per task: task -> [plan | tool_call | tool_result | model_call | check | finding | handoff |
    escalation | gate | stage | ...] in time order -> analyses -> decisions -> outcome

Every record has: seq, kind, ts, id (stable: the event / check / call / annotation / analysis / decision id), run_id,
task_id, agent, and `labels` (annotations on it, e.g. false_alarm, operator_influenced). The run header carries the
autonomy verdict: "autonomous" only if no task, event, model call or bridge request of the run is labelled
operator_influenced / manual_intervention; otherwise "operator_influenced" with the reasons, so consumers can separate
pure-autonomous trajectories from operator-influenced ones.

Model calls come from runs/<id>/logs/model_calls.jsonl. Schema-2 records carry their own call_id and timestamp;
schema-1 (Phase 0) records are aligned to the model tool_call events of the same task in order (flagged
alignment="by_order"). Heartbeats are counted, not listed (`--with-heartbeats` lists them).

    python -m s2s.records.trajectory export <run_id> [-o out.jsonl] [--with-heartbeats]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from s2s.db.models import Analysis, Annotation, Check, Design, Event, Gate, Run, Task
from s2s.db.session import session as db_session

TRAJECTORY_SCHEMA = 1
NOISE = {"task.heartbeat", "agent.status", "manager.checkin"}
KIND = {"plan": "plan", "tool_call": "tool_call", "tool_result": "tool_result", "finding": "finding",
        "handoff": "handoff", "escalation": "escalation", "gate.requested": "gate", "gate.decided": "gate",
        "stage.changed": "stage", "task.started": "task_event", "task.completed": "task_event",
        "task.failed": "task_event", "task.stalled": "stall", "budget.warning": "budget",
        "artifact.created": "artifact", "check.passed": "check", "check.failed": "check"}
INFLUENCE = {"operator_influenced", "manual_intervention"}


def _iso(t) -> str | None:
    return t.isoformat() if isinstance(t, dt.datetime) else t


def _model_calls(workdir: Path) -> list[dict]:
    p = workdir / "logs" / "model_calls.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def export(run_id: str, artifacts: Path, with_heartbeats: bool = False) -> list[dict]:
    with db_session() as s:
        run = s.get(Run, run_id)
        if run is None:
            raise KeyError(f"no run {run_id}")
        design = s.get(Design, run.design_id)
        tasks = s.scalars(select(Task).where(Task.run_id == run_id).order_by(Task.seq)).all()
        task_ids = [t.id for t in tasks]
        events = s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id)).all()
        checks = {c.id: c for c in s.scalars(select(Check).where(Check.task_id.in_(task_ids))).all()}
        gates = s.scalars(select(Gate).where(Gate.run_id == run_id)).all()
        analyses = s.scalars(select(Analysis).where(Analysis.run_id == run_id).order_by(Analysis.ts)).all()
        anns = s.scalars(select(Annotation).where(Annotation.run_id == run_id)).all()
        anns += s.scalars(select(Annotation).where(Annotation.target_id.in_(task_ids + [run_id]),
                                                   Annotation.run_id.is_(None))).all()
        labels: dict[str, list[dict]] = defaultdict(list)
        for a in anns:
            labels[a.target_id].append({"label": a.label, "reason": a.reason, "author": a.author, "annotation": a.id,
                                        **({"detail": a.detail} if a.detail else {})})

        calls = _model_calls(artifacts / "runs" / run_id)
        by_task: dict[str, list[dict]] = defaultdict(list)
        for c in calls:
            by_task[c["task_id"]].append(c)
        model_events: dict[str, list[Event]] = defaultdict(list)
        for e in events:
            if e.type == "tool_call" and (e.detail or {}).get("tool") == "model":
                model_events[e.task_id].append(e)

        out: list[dict] = []
        hb = 0
        for e in events:
            if e.type == "task.heartbeat":
                hb += 1
            if e.type in NOISE and not (with_heartbeats and e.type == "task.heartbeat"):
                continue
            kind = KIND.get(e.type, e.type)
            rec = {"kind": kind, "ts": _iso(e.ts), "id": e.id, "event_type": e.type, "task_id": e.task_id,
                   "agent": e.agent_id, "stage": e.stage, "summary": e.summary, "status": e.status,
                   "to_agent": e.to_agent_id, "detail": e.detail or {}}
            if kind == "check":
                c = checks.get((e.detail or {}).get("check_id"))
                if c:
                    rec.update(id=c.id, check={"name": c.check_name, "tool": c.tool, "tool_version": c.tool_version,
                                               "passed": c.passed, "metrics": c.metrics, "command": c.command})
            out.append(rec)
            if e.type == "tool_call" and (e.detail or {}).get("tool") == "model":
                k = model_events[e.task_id].index(e)
                cs = by_task.get(e.task_id, [])
                if k < len(cs) and cs[k].get("schema", 1) == 1:
                    out.append(_model_rec(cs[k], e, alignment="by_order"))
        for c in calls:
            if c.get("schema", 1) >= 2:  # carries its own id and time
                out.append(_model_rec(c, None, alignment="own_timestamp"))
        for a in analyses:
            out.append({"kind": "analysis", "ts": _iso(a.ts), "id": a.id, "task_id": a.task_id, "agent": a.author,
                        "analysis": {"kind": a.kind, "title": a.title, "label": a.label, "method": a.method,
                                     "inputs": a.inputs, "results": a.results, "sources": a.sources,
                                     "operator_influenced": a.operator_influenced, "location": a.location}})
        from s2s.records import decisions as dec
        for d in dec.all_decisions():
            if run_id in (d.get("links") or {}).get("runs", []):
                out.append({"kind": "decision", "ts": d.get("ts") or f"{d['date']}T23:59:59+00:00", "id": d["id"],
                            "task_id": None, "agent": d.get("actor"), "decision": d})
        out.sort(key=lambda r: (r["ts"] or "", r["id"]))

        for r in out:
            r["labels"] = labels.get(r["id"], []) + ([lab for lab in labels.get(r.get("call_id") or "", [])]
                                                      if r.get("call_id") else [])
            br = (r.get("model_call") or {}).get("bridge_request_ids") or []
            for b in br:
                r["labels"] += labels.get(b, [])

        for r in out:  # lift backfilled provenance into Phase 0 model-call records (labelled as backfilled)
            mc = r.get("model_call")
            if not mc:
                continue
            ab = [lab for lab in r["labels"] if lab["label"] == "answered_by"]
            if mc.get("answered_by") in (None, "unrecorded") and ab:
                mc["answered_by"] = {"model": ab[0]["detail"].get("model"), "via": ab[0]["detail"].get("via"),
                                     "source": "backfilled from the operator session transcript"}
            if mc.get("operator_influenced") is None:
                mc["operator_influenced"] = any(lab["label"] == "operator_influenced" for lab in r["labels"])
        task_recs = []
        for t in tasks:
            task_recs.append({"kind": "task", "ts": _iso(t.started_at) or _iso(t.assigned_at), "id": t.id, "task_id": t.id,
                              "agent": t.agent_id, "stage": t.stage, "title": t.title, "status": t.status,
                              "budget": t.budget, "usage": t.usage, "attempts": t.attempts,
                              "ended_at": _iso(t.ended_at), "labels": labels.get(t.id, [])})
        influenced = sorted({lab["reason"][:160] for rid, labs in labels.items() for lab in labs
                             if lab["label"] in INFLUENCE})
        header = {"kind": "run", "trajectory_schema": TRAJECTORY_SCHEMA, "ts": _iso(run.started_at), "id": run.id,
                  "run_id": run.id, "design": design.name if design else None, "agent_kind": run.agent_kind,
                  "stages": run.stages, "status": run.status, "started_at": _iso(run.started_at),
                  "ended_at": _iso(run.ended_at), "config_hash": run.config_hash,
                  "autonomy": "operator_influenced" if influenced else "autonomous",
                  "operator_influence": influenced, "labels": labels.get(run.id, []),
                  "counts": {"events": len(events), "heartbeats_omitted": 0 if with_heartbeats else hb,
                             "model_calls": len(calls), "checks": len(checks), "tasks": len(tasks),
                             "model_call_schema_1": sum(1 for c in calls if c.get("schema", 1) == 1)}}
        failed = sorted({c.check_name for c in checks.values() if not c.passed})
        last = {}
        for c in sorted(checks.values(), key=lambda c: c.id):
            last[c.check_name] = c.passed
        outcome = {"kind": "outcome", "ts": _iso(run.ended_at) or (out[-1]["ts"] if out else None), "id": f"outcome:{run.id}",
                   "run_status": run.status, "task_status": {t.stage: t.status for t in tasks},
                   "gates": [{"gate": g.gate, "status": g.status, "reviewer": g.reviewer, "decision": g.decision}
                             for g in gates],
                   "checks_total": len(checks), "checks_failed_ever": failed,
                   "checks_failing_last": sorted(k for k, v in last.items() if not v),
                   "verdict": "pass" if run.status == "completed" and not any(not v for v in last.values())
                              else "fail" if run.status == "failed" else "incomplete"}
        recs = [header] + _interleave(task_recs, out) + [outcome]
        for i, r in enumerate(recs):
            r["seq"] = i
            r.setdefault("run_id", run.id)
        return recs


def _interleave(tasks: list[dict], recs: list[dict]) -> list[dict]:
    """Each task record just before its first record."""
    seen, res = set(), []
    first = {t["id"]: t for t in tasks}
    for r in recs:
        tid = r.get("task_id")
        if tid in first and tid not in seen:
            res.append(first[tid])
            seen.add(tid)
        res.append(r)
    res = [t for t in tasks if t["id"] not in seen] + res
    return res


def bridge_index(bridge_dir: Path) -> dict[str, str]:
    """sha256 of a bridge request's user message -> request id (the logged prompt is that exact message)."""
    import hashlib
    idx = {}
    for rq in sorted((bridge_dir / "requests").glob("br_*.json")):
        if rq.name.endswith(".assign.json"):
            continue
        try:
            msgs = json.loads(rq.read_text()).get("messages") or []
        except (OSError, ValueError):
            continue
        content = "".join(str(m.get("content", "")) for m in msgs)
        idx.setdefault(hashlib.sha256(content.encode()).hexdigest(), rq.stem)
    return idx


_BRIDGE: dict[str, str] | None = None


def _bridge_lookup(prompt: str | None) -> str | None:
    import hashlib
    import os
    global _BRIDGE
    if _BRIDGE is None:
        root = Path(os.environ.get("S2S_BRIDGE_DIR", str(Path(__file__).resolve().parents[3] / "var" / "bridge")))
        _BRIDGE = bridge_index(root) if root.exists() else {}
    return _BRIDGE.get(hashlib.sha256(prompt.encode()).hexdigest()) if prompt else None


def _model_rec(c: dict, ev: Event | None, alignment: str) -> dict:
    prov = c.get("provenance") or {}
    bridge_ids = [a["request_id"] for a in prov.get("attempts", [])]
    if not bridge_ids and (rid := _bridge_lookup(c.get("prompt"))):
        bridge_ids = [rid]  # Phase 0 record: matched to its bridge request by the exact prompt text
    return {"kind": "model_call", "ts": c.get("ts") or (_iso(ev.ts) if ev else None),
            "id": c.get("call_id") or f"mc:{ev.id if ev else c['task_id']}", "call_id": c.get("call_id"),
            "task_id": c["task_id"], "agent": c.get("agent"),
            "model_call": {"schema": c.get("schema", 1), "alignment": alignment, "goal": c.get("goal"),
                           "attempt": c.get("attempt"), "prior_feedback": c.get("prior_feedback"),
                           "model_hint": c.get("model_hint"), "effort": c.get("effort"), "model": c.get("model"),
                           "answered_by": c.get("answered_by", "unrecorded"),
                           "operator_influenced": c.get("operator_influenced"),
                           "bridge_request_ids": bridge_ids,
                           "system_sha256": c.get("system_sha256"), "prompt": c.get("prompt"),
                           "answer": c.get("answer"), "provenance": prov or None}}


def main(argv: list[str] | None = None) -> int:
    import os
    ap = argparse.ArgumentParser(prog="python -m s2s.records.trajectory")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("run_id")
    e.add_argument("-o", "--out", type=Path)
    e.add_argument("--with-heartbeats", action="store_true")
    a = ap.parse_args(argv)
    recs = export(a.run_id, Path(os.environ.get("S2S_ARTIFACT_DIR", "/tmp/s2s-artifacts")), a.with_heartbeats)
    text = "".join(json.dumps(r, default=str) + "\n" for r in recs)
    if a.out:
        a.out.write_text(text)
        print(f"{len(recs)} records -> {a.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
