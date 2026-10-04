"use client";
// Human gate review (MASTER_SPEC Part 9; M0.8 "human gate UI"): the design's four gates with the evidence
// for each decision (the gated stage's latest checks: real tool results), and, for a pending gate, a review
// form that records a human decision through POST /gates/{id}/decision. Humans approve; agents never do.
import { useCallback, useEffect, useState } from "react";
import { getJSON, sendJSON } from "@/lib/api";

type GateCheck = { name: string; passed: boolean; tool: string; metrics: Record<string, unknown> };
export type GateRow = {
  id: string; gate: string; status: string; after_stage: string | null; run_id: string;
  reviewer: string | null; decision: string | null; comments: string | null; decided_at: string | null;
  stage: string | null; stage_title: string | null;
  evidence: { task_id: string | null; task_status: string | null; checks_passed: number; checks_failed: number;
    failed_checks: string[]; checks: GateCheck[] };
};
type Decision = "approve" | "approve_with_conditions" | "reject";

// Part 9 / Part 6: who signs each gate and what the evidence must show
const GATE_INFO: Record<string, { what: string; who: string; looks: string }> = {
  G1: { what: "Spec + architecture", who: "VP Front-End", looks: "spec and micro-architecture checks" },
  G2: { what: "RTL freeze", who: "VP Front-End", looks: "regression, coverage and formal results" },
  G3: { what: "Timing + physical signoff", who: "VP Physical",
    looks: "worst paths per corner, DRC/LVS summary, DFM high-severity items, IR/power margins" },
  G4: { what: "Tape-out", who: "VP Physical / CEO", looks: "the signed tape-out package and its re-verification" },
};
const DECISION_LABEL: Record<Decision, string> = {
  approve: "approve", approve_with_conditions: "approve with conditions", reject: "reject",
};
const GATE_CLASS: Record<string, string> = { approved: "ok", rejected: "bad", pending: "run" };

function hm(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }) : "–";
}

function Evidence({ g }: { g: GateRow }) {
  const e = g.evidence;
  const n = e.checks_passed + e.checks_failed;
  return (
    <div className="pj-gate-evidence">
      <span className="mono pj-small">
        {g.stage_title ?? g.after_stage ?? "stage"} · {n ? <>{e.checks_passed}✓ {e.checks_failed > 0 ? <b className="bad-t">{e.checks_failed}✗</b> : "0✗"}</> : "no checks recorded"}
        {e.task_status ? ` · task ${e.task_status}` : ""}
      </span>
      {e.failed_checks.length > 0 && (
        <p className="pj-gate-failed">Failed: <span className="mono">{e.failed_checks.join(", ")}</span></p>
      )}
      {n > 0 && (
        <details>
          <summary className="pj-small">All checks ({n})</summary>
          <ul className="pj-gate-checks">
            {e.checks.map((c) => (
              <li key={c.name}>
                <span className={`pj-chip ${c.passed ? "ok" : "bad"}`}>{c.passed ? "pass" : "fail"}</span>
                <span className="mono">{c.name}</span>
                <span className="mono muted">{c.tool}</span>
                <span className="mono muted pj-gate-metrics">{Object.entries(c.metrics).map(([k, v]) => `${k}=${Array.isArray(v) ? v.join(",") : String(v)}`).join("  ")}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function ReviewForm({ g, onDone }: { g: GateRow; onDone: () => void }) {
  const [reviewer, setReviewer] = useState("");
  const [decision, setDecision] = useState<Decision>("approve");
  const [comments, setComments] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const needComments = decision !== "approve";
  const valid = reviewer.trim().length > 0 && (!needComments || comments.trim().length > 0);
  const review = (e: React.FormEvent) => { e.preventDefault(); if (valid) { setMsg(null); setConfirming(true); } };
  const submit = () => {
    setBusy(true);
    sendJSON<GateRow>("POST", `/gates/${g.id}/decision`, {
      decision, reviewer: reviewer.trim(), ...(comments.trim() ? { comments: comments.trim() } : {}),
    }).then(() => { setConfirming(false); onDone(); })
      .catch((err: Error) => { setMsg(`Not recorded: ${err.message}`); setConfirming(false); onDone(); })
      .finally(() => setBusy(false));
  };
  const id = (k: string) => `gate-${g.id}-${k}`;
  return (
    <form className="pj-gate-form" onSubmit={review}>
      <div className="pj-gate-fields">
        <label htmlFor={id("rev")}>Reviewer (your name)
          <input id={id("rev")} className="btn" required value={reviewer} disabled={confirming || busy}
            onChange={(e) => setReviewer(e.target.value)} placeholder={GATE_INFO[g.gate]?.who ?? "name"} />
        </label>
        <fieldset className="pj-gate-decisions" disabled={confirming || busy}>
          <legend>Decision</legend>
          {(Object.keys(DECISION_LABEL) as Decision[]).map((d) => (
            <label key={d} className={`pj-gate-opt ${d === "reject" ? "bad" : d === "approve" ? "ok" : "cond"}`}>
              <input type="radio" name={id("dec")} value={d} checked={decision === d} onChange={() => setDecision(d)} />
              {DECISION_LABEL[d]}
            </label>
          ))}
        </fieldset>
      </div>
      <label htmlFor={id("com")}>Comments{needComments ? " (required: state the conditions or the reason)" : " (optional)"}
        <textarea id={id("com")} className="btn" rows={3} required={needComments} value={comments} disabled={confirming || busy}
          onChange={(e) => setComments(e.target.value)} />
      </label>
      {!confirming && <button type="submit" className="btn pj-primary" disabled={!valid}>Review decision…</button>}
      {confirming && (
        <div className={`pj-confirm pj-gate-confirm ${decision === "reject" ? "bad" : ""}`} role="alertdialog" aria-label="Confirm gate decision">
          <p>Record <b>{g.gate} {DECISION_LABEL[decision]}</b> by <b>{reviewer.trim()}</b> for run <span className="mono">{g.run_id}</span>?
            {g.evidence.checks_failed > 0 && decision !== "reject" ? ` ${g.evidence.checks_failed} check(s) of this stage failed.` : ""} A gate decision is final.</p>
          <button type="button" className="btn pj-primary" onClick={submit} disabled={busy}>{busy ? "Recording…" : "Confirm"}</button>{" "}
          <button type="button" className="btn" onClick={() => setConfirming(false)} disabled={busy}>Back</button>
        </div>
      )}
      {msg && <p className="pj-err">{msg}</p>}
    </form>
  );
}

export function GateReview({ designId, gateNames, onDecided }: { designId: string; gateNames: string[]; onDecided: () => void }) {
  const [rows, setRows] = useState<GateRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const load = useCallback(() => {
    getJSON<GateRow[]>(`/designs/${designId}/gates`, 15000).then((r) => { setRows(r); setErr(null); })
      .catch((e: Error) => setErr(e.message));
  }, [designId]);
  useEffect(() => { setRows(null); load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, [load]);
  const done = () => { load(); onDecided(); };
  return (
    <section className="card pj-pad pj-gates" aria-labelledby="gates-h">
      <h2 id="gates-h">Gates <span className="mono muted">human decisions on the tool evidence; agents never approve</span></h2>
      {err && <p className="pj-err">Gates unavailable: {err}</p>}
      {!rows && !err && <p className="muted">Loading…</p>}
      {rows && (
        <ol className="pj-gate-list">
          {gateNames.map((name) => {
            const all = rows.filter((r) => r.gate === name);
            const g = all[all.length - 1];  // latest run's gate
            const info = GATE_INFO[name];
            return (
              <li key={name} className={`pj-gate-item ${g ? GATE_CLASS[g.status] ?? "idle" : "idle"}`}>
                <div className="pj-gate-head">
                  <span className={`pj-gate ${g ? GATE_CLASS[g.status] ?? "" : ""}`}>{name}</span>
                  <b>{info?.what ?? name}</b>
                  <span className="mono muted pj-small">{info ? `signs: ${info.who}` : ""}</span>
                  <span className={`pj-chip ${g ? GATE_CLASS[g.status] ?? "idle" : "idle"}`}>{g ? g.status : "not reached"}</span>
                </div>
                {!g && <p className="muted pj-small">Opens when its stage passes. The reviewer looks at {info?.looks ?? "the stage checks"}.</p>}
                {g && (
                  <div className="pj-gate-body">
                    <Evidence g={g} />
                    {g.status === "pending" ? (
                      <>
                        <p className="muted pj-small">Review {info?.looks ?? "the evidence"} before deciding. Run <span className="mono">{g.run_id}</span>.</p>
                        <ReviewForm key={g.id} g={g} onDone={done} />
                      </>
                    ) : (
                      <p className="pj-gate-decided">
                        <b>{(g.decision ?? g.status).replace(/_/g, " ")}</b> by <b>{g.reviewer ?? "–"}</b> · {hm(g.decided_at)}
                        <span className="mono muted"> · run {g.run_id}</span>
                        {g.comments && <span className="pj-gate-comments">“{g.comments}”</span>}
                      </p>
                    )}
                    {all.length > 1 && (
                      <p className="muted mono pj-small">Earlier runs: {all.slice(0, -1).map((r) => `${r.run_id} ${r.status}${r.reviewer ? ` (${r.reviewer})` : ""}`).join(", ")}</p>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
