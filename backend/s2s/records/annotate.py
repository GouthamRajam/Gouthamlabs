"""Annotations and analyses for the trajectory record, and the one-time Phase 0 backfill (trajectory items 4-6).

Labels never edit history: each is an append-only row (target, label, reason, author). The backfill is idempotent.

    python -m s2s.records.annotate backfill [--transcript <claude session .jsonl>]

1. false_alarm      - a `task.stalled` event raised while the task was waiting on a running tool or model call
                      (its last tool_call had no tool_result yet): no heartbeat was emitted during tool runs then.
2. operator_influenced / manual_intervention
                    - every task and run with an operator event (escalation detail.rule "operator decision" /
                      "operator resume" / "operator correction", or a summary starting "Operator"); manual_intervention
                      where the event says the operator changed task/run state, config or files by hand (checkpoint,
                      budget, gate, block, resume point, reverted file).
                    - bridge requests whose answer was given with an operator note OUTSIDE the request (found in the
                      coding-agent session transcript; the request id, the note and its task are recorded).
3. answered_by      - which model answered each Phase 0 bridge request, from the subagent call in the transcript.
4. analyses         - the what-if derated STA runs (var/artifacts/scratch_ocv/*) and the antenna analysis
                      (scratch_ant/*), linked to their runs with input hashes, method and results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select

from s2s.db.models import ANNOTATION_LABELS, Analysis, Annotation, Event, Run, Task
from s2s.db.session import session as db_session
from s2s.ids import new_id

REPO = Path(__file__).resolve().parents[3]
OPERATOR_RULES = ("operator decision", "operator resume", "operator correction")
EDIT_WORDS = re.compile(r"checkpoint|budget|withdrawn|cleared|block|step [0-9]+|set back|raised", re.I)
LABELS = ANNOTATION_LABELS + ("answered_by",)


def annotate(s, target_kind: str, target_id: str, label: str, reason: str, author: str, run_id: str | None = None,
             detail: dict | None = None) -> str | None:
    """Add a label unless the same (target, label, author) exists. Returns the new id or None."""
    if label not in LABELS:
        raise ValueError(f"unknown label {label!r}; allowed {LABELS}")
    if s.scalar(select(Annotation.id).where(Annotation.target_kind == target_kind, Annotation.target_id == target_id,
                                            Annotation.label == label, Annotation.author == author)):
        return None
    aid = new_id("ann")
    s.add(Annotation(id=aid, target_kind=target_kind, target_id=target_id, run_id=run_id, label=label,
                     reason=reason, author=author, detail=detail or {}))
    return aid


# --- 1. false stall alarms -------------------------------------------------------------------------------------
def stall_verdicts(s) -> list[dict]:
    """For every task.stalled event: was a tool or model call open (started, not finished) at that moment?"""
    out = []
    for st in s.scalars(select(Event).where(Event.type == "task.stalled").order_by(Event.ts)).all():
        last = s.scalars(select(Event).where(Event.task_id == st.task_id, Event.ts <= st.ts,
                                             Event.type.in_(("tool_call", "tool_result")))
                         .order_by(Event.ts.desc()).limit(1)).first()
        open_call = last is not None and last.type == "tool_call"
        out.append({"event": st, "open_call": last if open_call else None})
    return out


def backfill_false_stalls(s, author: str = "backfill:phase1") -> dict:
    n_false = n_other = 0
    for v in stall_verdicts(s):
        st, call = v["event"], v["open_call"]
        if call is None:
            n_other += 1
            continue
        tool = (call.detail or {}).get("tool")
        if annotate(s, "event", st.id, "false_alarm",
                    f"raised while {tool or 'a tool'} was running (tool_call {call.id} at {call.ts.isoformat()} had "
                    "no result yet); tool runs emitted no heartbeat before harness #3", author, st.run_id,
                    {"open_tool_call": call.id, "tool": tool, "call_summary": call.summary[:200]}):
            n_false += 1
    return {"stalls_false_alarm": n_false, "stalls_not_labelled": n_other}


# --- 2. operator influence ----------------------------------------------------------------------------------------
def backfill_operator_events(s, author: str = "backfill:phase1") -> dict:
    n = 0
    evs = s.scalars(select(Event).where(Event.type == "escalation").order_by(Event.ts)).all()
    for e in evs:
        rule = (e.detail or {}).get("rule")
        if rule not in OPERATOR_RULES and not (e.summary or "").startswith("Operator"):
            continue
        reason = f"operator event {e.id}: {e.summary[:240]}"
        for kind, tid in (("task", e.task_id), ("run", e.run_id)):
            if tid and annotate(s, kind, tid, "operator_influenced", reason, author, e.run_id,
                                {"event": e.id, "rule": rule}):
                n += 1
        if e.task_id and (rule == "operator correction" or EDIT_WORDS.search(e.summary or "")):
            annotate(s, "event", e.id, "manual_intervention", f"the operator changed task/run state, config or files by hand: {e.summary[:240]}",
                     author, e.run_id, {"task": e.task_id, "rule": rule})
    return {"operator_annotations": n}


def _session_records(transcript: Path):
    for line in transcript.open():
        try:
            yield json.loads(line)
        except ValueError:
            continue


def _bridge_subagent_calls(transcript: Path):
    """(request_id, model, prompt) for every subagent the operator started to answer a bridge request."""
    for d in _session_records(transcript):
        if d.get("type") != "assistant":
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Agent":
                prompt = (c.get("input") or {}).get("prompt", "")
                ids = re.findall(r"br_[0-9A-Z]{26}(?:_retry)?", prompt)
                if ids:
                    yield ids[0], (c.get("input") or {}).get("model") or "inherited (session model)", prompt


def _request_task(rid: str) -> tuple[str | None, str | None]:
    rq = REPO / "var" / "bridge" / "requests" / f"{rid}.json"
    try:
        text = json.dumps(json.loads(rq.read_text()).get("messages"))
    except (OSError, ValueError):
        return None, None
    m = re.search(r"task_[0-9A-Z]{26}", text)
    return (m[0], None) if m else (None, None)


def backfill_transcript(s, transcript: Path, author: str = "backfill:phase1-transcript") -> dict:
    n_notes = n_models = 0
    for rid, model, prompt in _bridge_subagent_calls(transcript):
        tid, _ = _request_task(rid)
        run_id = s.get(Task, tid).run_id if tid and s.get(Task, tid) else None
        if annotate(s, "bridge_request", rid, "answered_by", f"subagent started with model {model!r}", author, run_id,
                    {"model": model, "via": "claude-code subagent", "task": tid}):
            n_models += 1
        m = re.search(r"Operator note[^\n]*(?:\n(?!Rules:)[^\n]*)*", prompt)
        if m:
            note = m[0].strip()
            for kind, target in (("bridge_request", rid), ("task", tid), ("run", run_id)):
                if target:
                    annotate(s, kind, target, "operator_influenced",
                             f"bridge request {rid} was answered with an operator note given OUTSIDE the request "
                             f"(not in the logged prompt): {note[:300]}", author, run_id,
                             {"bridge_request": rid, "note": note})
            n_notes += 1
    return {"answered_by": n_models, "out_of_band_notes": n_notes}


# --- 4. what-if analyses ------------------------------------------------------------------------------------------
SIGNED = {"counter8": "run_01M43B9BVD8M5ANEVYTE43N0KN", "alu8": "run_01M44DR7XRWAQ9XY53AG8SRJCM",
          "sync_fifo": "run_01M43MDNVKWCHEQ0GGHPJFT602", "uart": "run_01M47BE6QKCPAEAE7RVYYJ9TEY",
          "spi_master": "run_01M484JWYZ7ADCE8N97SZV80QG",
          "sync_fifo_fix_it3": "run_01M4A7YXRDRF2TV0HY1ERGQJ0A",
          "sync_fifo_fix2_it3": "run_01M4AFNT5QK68FGT27TVRBYWZN"}


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _done_at(paths) -> "dt.datetime":
    """When the analysis was done: the newest output file's modification time (not the backfill time)."""
    import datetime as dt
    times = [p.stat().st_mtime for p in paths]
    return dt.datetime.fromtimestamp(max(times), dt.timezone.utc) if times else dt.datetime.now(dt.timezone.utc)


def _ws(log: Path) -> float | None:
    m = re.findall(r"^(?:S2S_)?WS (\S+)", log.read_text(errors="replace"), re.M)
    try:
        return float(m[-1]) * (1e9 if abs(float(m[-1])) < 1e-3 else 1) if m else None
    except ValueError:
        return None


def backfill_analyses(s, root: Path | None = None, author: str = "operator (Phase 0, recorded by backfill)") -> dict:
    root = root or REPO / "var" / "artifacts"
    n = 0
    for d in sorted((root / "scratch_ocv").glob("*")):
        run_id = SIGNED.get(d.name)
        title = f"what-if flat OCV derated STA: {d.name}"
        if not run_id or s.scalar(select(Analysis.id).where(Analysis.title == title)):
            continue
        res = {}
        for log in sorted(d.glob("*.log")):
            m = re.match(r"(setup|hold)_?(\d+(?:\.\d+)?)", log.stem)
            if not m:
                continue
            pct = m[2] if "." not in m[2] else f"{round((float(m[2]) - 1) * 100):g}"
            res.setdefault(m[1], {})[f"{pct}pct"] = _ws(log)
        tcl = sorted(d.glob("setup*1*.tcl")) or sorted(d.glob("*.tcl"))
        when = _done_at(d.glob("*.log"))
        s.add(Analysis(id=new_id("ana"), ts=when, run_id=run_id, kind="what_if", title=title,
                       method=("OpenSTA on read-only copies of the routed netlist and SPEF with the reviewed SDC; "
                               "flat set_timing_derate early 1-p / late 1+p (p = 0, 5, 10 %); setup at ss_100C_1v60 "
                               "with max RC, hold at ff_n40C_1v95 with min RC; worst slack in ns. Example script:\n"
                               + (tcl[0].read_text() if tcl else "")),
                       inputs=[{"path": str(p.relative_to(REPO)), "sha256": _sha(p)}
                               for p in sorted(d.glob("*")) if p.suffix in (".v", ".spef", ".sdc")],
                       results={"worst_slack_ns": res, "unit": "ns"},
                       sources=["docs/milestones/m0.7-evidence/ocv_derated_results.md"], author=author,
                       operator_influenced=True, location=str(d.relative_to(REPO))))
        n += 1
    ant = root / "scratch_ant" / "fifo2_it5"
    title = "antenna analysis: check_antennas -verbose on sync_fifo change #2 it5 global route (post-repair)"
    if ant.exists() and not s.scalar(select(Analysis.id).where(Analysis.title == title)):
        rpt = (ant / "est_after_repair.rpt").read_text(errors="replace") if (ant / "est_after_repair.rpt").exists() else ""
        s.add(Analysis(id=new_id("ana"), ts=_done_at(ant.glob("*.rpt")), run_id=SIGNED["sync_fifo_fix2_it3"],
                       kind="diagnosis", title=title,
                       label="analysis, not a recorded check",
                       method=(ant / "chk.tcl").read_text() if (ant / "chk.tcl").exists() else "",
                       inputs=[{"path": str(p.relative_to(REPO)), "sha256": _sha(p)} for p in sorted(ant.glob("*.odb"))],
                       results={"net19_met1_side_ratio_global_route": 476.73, "net19_required_global_route": 2736.24,
                                "net19_met1_side_ratio_detailed_route": 469.18, "net19_required_detailed_route": 400.0,
                                "report": "scratch_ant/fifo2_it5/est_after_repair.rpt" if rpt else None},
                       sources=["https://openroad.readthedocs.io/en/latest/main/src/grt/README.html"], author=author,
                       operator_influenced=True, location=str(ant.relative_to(REPO))))
        n += 1
    return {"analyses": n}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m s2s.records.annotate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backfill")
    b.add_argument("--transcript", type=Path)
    a = ap.parse_args(argv)
    out = {}
    with db_session() as s:
        out.update(backfill_false_stalls(s))
        out.update(backfill_operator_events(s))
        if a.transcript:
            out.update(backfill_transcript(s, a.transcript))
        out.update(backfill_analyses(s))
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
