"use client";
// Projects: one page per design across all of its runs. The current activity, the 11-stage flow with
// its four human gates, every stage's checks (real tool results), checkpoints and log, the timeline
// and the spend. "New project" turns a plain-English request into a project + design (MASTER_SPEC
// Part 12 run views; Part 9 gates). Read-only except creating a project and, on request, starting a run.
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { apiBase, getJSON, sendJSON } from "@/lib/api";

const Layout3D = dynamic(() => import("@/components/Layout3D").then((m) => m.Layout3D), { ssr: false });

type DesignRow = { id: string; name: string; state: string; current_stage: string | null; spend_usd: number;
  runs: number; last_activity: string | null; created_at: string | null };
type ProjectRow = { id: string; name: string; last_activity: string | null; designs: DesignRow[] };
type Check = { name: string; passed: boolean; tool: string; command: string; records: number; metrics: Record<string, unknown> };
type TaskInfo = { id: string; run_id: string; agent_id: string; status: string; attempts: number; percent: number;
  evidence: string | null; started_at: string | null; ended_at: string | null; last_progress_at: string | null;
  stalled_at: string | null; checkpoint_step: number; steps: string[] | null };
type Stage = { name: string; title: string; zone: string | null; lead: string | null; gate_after: string | null;
  status: string; task: TaskInfo | null; checks: Check[]; checks_passed: number; checks_failed: number;
  gate: { gate: string; status: string; reviewer: string | null; decided_at: string | null } | null;
  spend_usd: number; events: number; earlier_attempts: { run_id: string; status: string; started_at: string | null }[] };
type Overview = {
  design: { id: string; name: string; pdk: string; target_clock_mhz: number | null; request_text: string | null; created_at: string | null };
  project: { id: string; name: string } | null;
  runs: { id: string; status: string; stages: string[]; started_at: string | null; ended_at: string | null }[];
  stages: Stage[]; current: (TaskInfo & { stage: string; status: string }) | null;
  timeline: { ts: string | null; kind: string; label: string; run_id: string }[];
  spend: { total_usd: number; cap_usd: number | null; by_agent: Record<string, number>; by_stage: Record<string, number> };
  summary: { passed: number; failed: number; stages: number };
  outputs: { label: string; path: string; run_id: string; bytes: number }[];
};
type LogEvent = { id: string; ts: string; type: string; agent_id: string | null; to_agent_id: string | null; summary: string; run_id: string };

const STATUS_CLASS: Record<string, string> = {
  passed: "ok", failed: "bad", running: "run", queued: "wait", "needs you": "bad", "awaiting gate": "run",
  "not started": "idle", "needs you": "bad", idle: "idle", new: "idle",
};
const STEP_LABEL: Record<string, string> = {
  stop_if_blocked: "blocked check", regress_debug: "regression + formal + debug", cora: "coverage closure (Cora)",
  myra: "mutation testing (Myra)", anticheat: "anti-cheating guard", report: "report", task_result: "task result",
  setup: "setup", change_requests: "change requests", pnr_loop: "placement / CTS / routing loop", ol_signoff: "OpenLane signoff",
  calla: "DRC + LVS (Calla)", chronos: "9-corner STA (Chronos)", volta: "power + IR (Volta)", fabian: "DFM (Fabian)",
  equivalence_gls: "equivalence + gate-level sim", package: "package", gideon_verify: "re-verify packaged GDS",
  proof: "clean-container reproduce (Proof)", checklist: "checklist + readiness", release_notes: "release notes",
  sign: "signed manifest", sloane: "division report", sienna_sdc: "constraints (Sienna)",
  sentinel_constraints: "Sentinel review", synth: "synthesis + pre-layout STA", eqy_synth: "equivalence",
  sienna_report: "synthesis report", "<lambda>": "task result", tess: "DFT plan (Tess)", grid: "floorplan plan (Grid)", fp_run: "floorplan run",
  tick: "clock tree report (Tick)", orion_report: "P&R report (Orion)", mason: "division report", result: "task result",
};

function ago(iso: string | null): string {
  if (!iso) return "–";
  const s = Math.max(0, (Date.now() - Date.parse(iso)) / 1000);
  if (s < 90) return `${Math.round(s)} s ago`;
  if (s < 5400) return `${Math.round(s / 60)} min ago`;
  if (s < 172800) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86400)} d ago`;
}
function hm(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }) : "–";
}
function dur(a: string | null, b: string | null): string {
  if (!a) return "–";
  const s = ((b ? Date.parse(b) : Date.now()) - Date.parse(a)) / 1000;
  if (s < 120) return `${Math.round(s)} s`;
  if (s < 7200) return `${Math.round(s / 60)} min`;
  return `${(s / 3600).toFixed(1)} h`;
}
const usd = (v: number) => `$${v.toFixed(2)}`;
const Chip = ({ s }: { s: string }) => <span className={`pj-chip ${STATUS_CLASS[s] ?? "idle"}`}>{s}</span>;

// --- sidebar ---------------------------------------------------------------------------------------
function Sidebar({ projects, sel, onSelect, onNew, err }: { projects: ProjectRow[]; sel: string | null;
  onSelect: (id: string) => void; onNew: () => void; err: string | null }) {
  return (
    <aside className="pj-side card" aria-label="Projects">
      <button type="button" className="pj-new" onClick={onNew} data-testid="new-project">+ New project</button>
      {err && <p className="pj-err">{err}</p>}
      <nav className="pj-list">
        {projects.map((p) => (
          <div key={p.id} className="pj-proj">
            <div className="pj-proj-name mono">{p.name}</div>
            {p.designs.map((d) => (
              <button key={d.id} type="button" className="pj-item" aria-current={sel === d.id ? "true" : undefined}
                onClick={() => onSelect(d.id)}>
                <span className="pj-item-top"><b>{d.name}</b><Chip s={d.state} /></span>
                <span className="pj-item-sub mono">
                  {d.current_stage ? `${d.current_stage} · ` : ""}{d.runs} run{d.runs === 1 ? "" : "s"} · {usd(d.spend_usd)} · {ago(d.last_activity ?? d.created_at)}
                </span>
              </button>
            ))}
          </div>
        ))}
        {!projects.length && !err && <p className="muted">No projects yet.</p>}
      </nav>
    </aside>
  );
}

// --- the flow strip ----------------------------------------------------------------------------------
function Flow({ stages, onJump }: { stages: Stage[]; onJump: (n: string) => void }) {
  return (
    <div className="pj-flow" role="list" aria-label="Design flow">
      {stages.map((st, i) => (
        <div key={st.name} className="pj-flow-cell" role="listitem">
          <button type="button" className={`pj-node ${STATUS_CLASS[st.status] ?? "idle"}`} onClick={() => onJump(st.name)}
            title={`${st.title}: ${st.status}`}>
            <span className="pj-node-n mono">{i + 1} · Z{st.zone}</span>
            <span className="pj-node-t">{st.name.replace("_", " ")}</span>
            <span className="pj-node-s mono">{st.status}</span>
          </button>
          {st.gate_after && (
            <span className={`pj-gate ${st.gate?.status === "approved" ? "ok" : st.gate ? "run" : "idle"}`}
              title={`${st.gate_after}: ${st.gate?.status ?? "not reached"}`}>{st.gate_after}</span>
          )}
        </div>
      ))}
    </div>
  );
}

// --- one stage, expandable -----------------------------------------------------------------------
function StageLog({ designId, stage }: { designId: string; stage: string }) {
  const [rows, setRows] = useState<LogEvent[] | null>(null);
  const [filter, setFilter] = useState("all");
  const [err, setErr] = useState<string | null>(null);
  const load = useCallback(() => {
    getJSON<LogEvent[]>(`/designs/${designId}/stages/${stage}/events?limit=600`, 15000).then(setRows)
      .catch((e: Error) => setErr(e.message));
  }, [designId, stage]);
  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);
  const types = useMemo(() => Array.from(new Set((rows ?? []).map((r) => r.type))).sort(), [rows]);
  const shown = (rows ?? []).filter((r) => filter === "all" || r.type === filter);
  return (
    <div className="pj-log">
      <div className="pj-log-head">
        <span className="mono muted">{rows ? `${rows.length} events` : "loading…"}</span>
        <label className="mono muted">type{" "}
          <select className="btn" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">all</option>
            {types.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
      </div>
      {err && <p className="pj-err">Log unavailable: {err}</p>}
      <ol className="pj-log-list">
        {shown.map((r) => (
          <li key={r.id} className={`t-${r.type.replace(".", "-")}`}>
            <time className="mono">{hm(r.ts)}</time>
            <span className="mono pj-log-type">{r.type}</span>
            <span><b>{r.agent_id ?? "–"}</b>{r.to_agent_id ? ` → ${r.to_agent_id}` : ""}: {r.summary}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function StageCard({ st, idx, designId, open, setOpen }: { st: Stage; idx: number; designId: string; open: boolean;
  setOpen: (v: boolean) => void }) {
  const [showLog, setShowLog] = useState(false);
  const t = st.task;
  return (
    <section id={`stage-${st.name}`} className={`pj-stage card ${open ? "open" : ""}`}>
      <button type="button" className="pj-stage-head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="pj-stage-n mono">{String(idx + 1).padStart(2, "0")}</span>
        <span className="pj-stage-title"><b>{st.title}</b><span className="mono muted"> · zone {st.zone} · lead {st.lead ?? "–"}</span></span>
        <span className="pj-stage-meta mono">
          {st.checks_passed + st.checks_failed > 0 && <span>{st.checks_passed}✓ {st.checks_failed > 0 && <b className="bad-t">{st.checks_failed}✗</b>}</span>}
          {st.spend_usd > 0 && <span>{usd(st.spend_usd)}</span>}
          {t && <span>{dur(t.started_at, t.ended_at)}</span>}
          {st.gate && <span className={`pj-gate ${st.gate.status === "approved" ? "ok" : "run"}`}>{st.gate.gate} {st.gate.status}</span>}
        </span>
        <Chip s={st.status} />
      </button>
      {open && (
        <div className="pj-stage-body">
          {!t && <p className="muted">Not started yet. It starts when the stages before it pass{st.gate_after ? ` (then ${st.gate_after})` : ""}.</p>}
          {t && (
            <div className="pj-kv">
              <div><span>Owner</span><b>{t.agent_id}</b></div>
              <div><span>Task status</span><b>{t.status}</b></div>
              <div><span>Run</span><b className="mono">{t.run_id}</b></div>
              <div><span>Attempts</span><b>{t.attempts}</b></div>
              <div><span>Started</span><b>{hm(t.started_at)}</b></div>
              <div><span>Ended</span><b>{t.ended_at ? hm(t.ended_at) : "–"}</b></div>
              <div><span>Last progress</span><b>{ago(t.last_progress_at)}</b></div>
              <div><span>Evidence</span><b>{t.evidence ?? "–"}</b></div>
            </div>
          )}
          {t?.steps && (
            <>
              <h4>Checkpoints <span className="mono muted">step {Math.min(t.checkpoint_step + (t.status === "completed" ? 0 : 1), t.steps.length)} of {t.steps.length}</span></h4>
              <ol className="pj-steps">
                {t.steps.map((s, i) => {
                  const state = i < t.checkpoint_step ? "done" : i === t.checkpoint_step && t.status !== "completed" ? (t.status === "running" ? "now" : "stopped") : t.status === "completed" ? "done" : "todo";
                  return <li key={i} className={state}><span className="mono">{i + 1}</span>{STEP_LABEL[s] ?? s.replace(/_/g, " ")}<em>{state === "now" ? "running" : state === "stopped" ? t.status : state === "done" ? "saved" : ""}</em></li>;
                })}
              </ol>
            </>
          )}
          {st.checks.length > 0 && (
            <>
              <h4>Checks <span className="mono muted">real tool results; latest record per check</span></h4>
              <div className="pj-table-wrap">
                <table className="pj-table">
                  <thead><tr><th>Check</th><th>Result</th><th>Tool</th><th className="n">Records</th><th>Key numbers</th></tr></thead>
                  <tbody>
                    {st.checks.map((c) => (
                      <tr key={c.name}>
                        <td className="mono">{c.name}</td>
                        <td><span className={`pj-chip ${c.passed ? "ok" : "bad"}`}>{c.passed ? "pass" : "fail"}</span></td>
                        <td className="mono muted">{c.tool}</td>
                        <td className="n mono">{c.records}</td>
                        <td className="mono pj-metrics">{Object.entries(c.metrics).map(([k, v]) => `${k}=${Array.isArray(v) ? v.join(",") : String(v)}`).join("  ") || "–"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          {st.earlier_attempts.length > 0 && (
            <p className="muted mono pj-small">Earlier attempts: {st.earlier_attempts.map((a) => `${a.run_id} (${a.status})`).join(", ")}</p>
          )}
          <button type="button" className="btn" aria-expanded={showLog} onClick={() => setShowLog(!showLog)}>
            {showLog ? "Hide log" : `Show log (${st.events} events)`}
          </button>
          {showLog && <StageLog designId={designId} stage={st.name} />}
        </div>
      )}
    </section>
  );
}

// --- one design ----------------------------------------------------------------------------------------
function DesignView({ designId }: { designId: string }) {
  const [o, setO] = useState<Overview | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [updated, setUpdated] = useState<string | null>(null);
  const [startMsg, setStartMsg] = useState<string | null>(null);
  const [confirmStart, setConfirmStart] = useState(false);
  const [show3d, setShow3d] = useState(false);
  const load = useCallback(() => {
    getJSON<Overview>(`/designs/${designId}/overview`, 20000).then((x) => {
      setO(x); setErr(null); setUpdated(new Date().toISOString());
      setOpen((prev) => Object.keys(prev).length ? prev : Object.fromEntries(x.stages.filter((s) => ["running", "needs you", "failed"].includes(s.status)).map((s) => [s.name, true])));
    }).catch((e: Error) => setErr(e.message));
  }, [designId]);
  useEffect(() => { setO(null); setOpen({}); load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, [load]);
  const jump = (n: string) => { setOpen((p) => ({ ...p, [n]: true })); document.getElementById(`stage-${n}`)?.scrollIntoView({ behavior: "smooth", block: "start" }); };

  if (err && !o) return <div className="card pj-pad"><p className="pj-err">Could not load the design: {err}</p></div>;
  if (!o) return <div className="card pj-pad"><p className="muted">Loading…</p></div>;
  const c = o.current;
  const capPct = o.spend.cap_usd ? Math.min(100, (100 * o.spend.total_usd) / o.spend.cap_usd) : 0;
  const notStarted = o.runs.length === 0;
  const start = () => {
    sendJSON<{ id: string }>("POST", `/designs/${designId}/runs`, { agent_kind: "s2s", from_stage: "spec", to_stage: "rtl" })
      .then((r) => { setStartMsg(`Run ${r.id} created (spec → architecture → RTL). The orchestrator picks it up.`); setConfirmStart(false); load(); })
      .catch((e: Error) => setStartMsg(`Could not start: ${e.message}`));
  };
  return (
    <div className="pj-main">
      <header className="pj-head">
        <div>
          <div className="mono muted pj-small">{o.project?.name} · {o.design.pdk} · {o.design.target_clock_mhz ? `${o.design.target_clock_mhz} MHz target` : "clock from spec"} · created {hm(o.design.created_at)}</div>
          <h1 className="display">{o.design.name}</h1>
        </div>
        <div className="mono muted pj-small">updated {updated ? ago(updated) : "–"} · refreshes every 10 s</div>
      </header>

      <section className={`card pj-now ${c ? STATUS_CLASS[c.status] ?? "" : ""}`} aria-labelledby="now-h">
        <h2 id="now-h">Happening now</h2>
        {c ? (
          <>
            <p className="pj-now-what"><b>{c.stage.replace("_", " ")}</b> · {c.agent_id} · {c.status}{c.steps ? ` · step ${Math.min(c.checkpoint_step + 1, c.steps.length)} of ${c.steps.length}: ${STEP_LABEL[c.steps[Math.min(c.checkpoint_step, c.steps.length - 1)]] ?? c.steps[c.checkpoint_step]}` : ""}</p>
            <p className="muted">{c.evidence ?? "no progress signal yet"} · last progress {ago(c.last_progress_at)}{c.stalled_at ? " · flagged as stalled by the manager (long tool runs send no heartbeat)" : ""}</p>
            {c.status === "needs you" && <p className="pj-err">This stage is paused for a human decision. See its log below.</p>}
          </>
        ) : notStarted ? (
          <p className="muted">No run yet. Starting one makes real agent calls (spec → architecture → RTL first).</p>
        ) : (
          <p className="muted">Nothing running. {o.summary.passed} of {o.summary.stages} stages passed{o.summary.failed ? `, ${o.summary.failed} failed` : ""}.</p>
        )}
        {notStarted && !confirmStart && <button type="button" className="btn" onClick={() => setConfirmStart(true)}>Start spec → RTL run…</button>}
        {confirmStart && (
          <div className="pj-confirm">
            <p>This starts real agents (Iris, Kepler, Ada…) through the configured model provider and counts against the spend caps. Start?</p>
            <button type="button" className="btn pj-primary" onClick={start}>Start run</button>{" "}
            <button type="button" className="btn" onClick={() => setConfirmStart(false)}>Cancel</button>
          </div>
        )}
        {startMsg && <p className="mono pj-small">{startMsg}</p>}
      </section>

      <div className="pj-stats">
        <div className="card"><span>Stages passed</span><b>{o.summary.passed} / {o.summary.stages}</b></div>
        <div className="card"><span>Stages failed</span><b className={o.summary.failed ? "bad-t" : ""}>{o.summary.failed}</b></div>
        <div className="card"><span>Runs</span><b>{o.runs.length}</b></div>
        <div className="card"><span>Spend (API)</span><b>{usd(o.spend.total_usd)}{o.spend.cap_usd ? ` / ${usd(o.spend.cap_usd)}` : ""}</b>
          <div className="pj-bar" aria-hidden="true"><i style={{ width: `${capPct}%` }} className={capPct > 85 ? "hot" : ""} /></div></div>
      </div>

      <section className="card pj-pad pj-out" aria-labelledby="out-h">
        <h2 id="out-h">Outputs <span className="mono muted">the deliverable is the GDSII layout</span></h2>
        {o.outputs.some((f) => f.path.endsWith(".gds")) && !show3d && (
          <button type="button" className="btn pj-primary" style={{ marginBottom: 8 }} onClick={() => setShow3d(true)}>Open 3D view of the GDSII</button>
        )}
        {show3d && <Layout3D runId={o.outputs[0].run_id} onClose={() => setShow3d(false)} />}
        {o.outputs.length ? (
          <ul className="pj-out-list">
            {o.outputs.map((f) => (
              <li key={f.path} className={f.path.endsWith(".gds") ? "gds" : ""}>
                <a href={`${apiBase()}/runs/${f.run_id}/files/${f.path}`}>{f.label}</a>
                <span className="mono muted">{f.path} · {f.bytes >= 1e6 ? `${(f.bytes / 1e6).toFixed(1)} MB` : `${(f.bytes / 1e3).toFixed(1)} kB`}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No GDSII yet. It is produced at the last stage (gdsii), after signoff passes G3: the final layout plus a
            signed tape-out package (signoff reports, checklist, readiness report, reproduce.sh).</p>
        )}
      </section>

      <section aria-labelledby="flow-h">
        <h2 id="flow-h" className="pj-h2">Design flow <span className="mono muted">spec → GDSII · four human gates</span></h2>
        <Flow stages={o.stages} onJump={jump} />
      </section>

      <section aria-labelledby="stages-h" className="pj-stages">
        <h2 id="stages-h" className="pj-h2">Stages <span className="mono muted">open a stage for its checkpoints, checks and log</span></h2>
        {o.stages.map((st, i) => (
          <StageCard key={st.name} st={st} idx={i} designId={designId} open={!!open[st.name]}
            setOpen={(v) => setOpen((p) => ({ ...p, [st.name]: v }))} />
        ))}
      </section>

      <div className="pj-two">
        <section className="card pj-pad" aria-labelledby="tl-h">
          <h2 id="tl-h">Timeline</h2>
          <ol className="pj-timeline">
            {[...o.timeline].reverse().map((t, i) => (
              <li key={i} className={`k-${t.kind}`}><time className="mono">{hm(t.ts)}</time><span>{t.label}</span></li>
            ))}
          </ol>
        </section>
        <section className="card pj-pad" aria-labelledby="sp-h">
          <h2 id="sp-h">Spend by agent</h2>
          <table className="pj-table">
            <tbody>
              {Object.entries(o.spend.by_agent).sort((a, b) => b[1] - a[1]).map(([a, v]) => (
                <tr key={a}><td>{a}</td><td className="n mono">{usd(v)}</td></tr>
              ))}
            </tbody>
          </table>
          <p className="muted pj-small">Metered API cost. Claude Code bridge calls are recorded at $0.</p>
          <h2>Runs</h2>
          <ul className="pj-runs mono">
            {o.runs.map((r) => <li key={r.id}>{r.id} · {r.stages.join(" → ")} · {r.status}</li>)}
          </ul>
          {o.design.request_text && (<details><summary>Original request</summary><p className="pj-req">{o.design.request_text}</p></details>)}
        </section>
      </div>
    </div>
  );
}

// --- new project (chat-style) ---------------------------------------------------------------------
type Msg = { who: "s2s" | "you"; text: string };
function NewProject({ onCreated }: { onCreated: (designId: string) => void }) {
  const [msgs, setMsgs] = useState<Msg[]>([{ who: "s2s", text: "Describe the chip block you want in plain English: what it does, its interfaces, and the clock. " +
    "I'll create a project and a design for it. Phase 0 designs use the open SKY130 process. Nothing runs until you start a run." }]);
  const [project, setProject] = useState("");
  const [name, setName] = useState("");
  const [mhz, setMhz] = useState("");
  const [req, setReq] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [msgs]);
  const send = (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setMsgs((m) => [...m, { who: "you", text: `${req}${mhz ? ` (target ${mhz} MHz)` : ""}` }]);
    sendJSON<{ design: { id: string; name: string }; project: { name: string } }>("POST", "/projects/requests", {
      project_name: project || name, design_name: name, request_text: req, target_clock_mhz: mhz ? Number(mhz) : null,
    }).then((r) => {
      setCreated(r.design.id);
      setMsgs((m) => [...m, { who: "s2s", text: `Created project "${r.project.name}" with design ${r.design.name}. ` +
        "Open it to start the first run (spec → architecture → RTL) when you're ready." }]);
      setReq("");
    }).catch((err: Error) => setMsgs((m) => [...m, { who: "s2s", text: `Not created: ${err.message}` }]))
      .finally(() => setBusy(false));
  };
  return (
    <div className="pj-main">
      <header className="pj-head"><h1 className="display">New project</h1></header>
      <div className="card pj-chat">
        <div className="pj-msgs" aria-live="polite">
          {msgs.map((m, i) => <div key={i} className={`pj-msg ${m.who}`}><span className="mono">{m.who === "s2s" ? "S2S" : "You"}</span><p>{m.text}</p></div>)}
          {created && <button type="button" className="btn pj-primary" onClick={() => onCreated(created)}>Open the new design</button>}
          <div ref={end} />
        </div>
        <form className="pj-compose" onSubmit={send}>
          <div className="pj-fields">
            <label>Project name<input id="np-project" className="btn" value={project} onChange={(e) => setProject(e.target.value)} placeholder="e.g. Phase 0 blocks" /></label>
            <label>Design name<input id="np-design" className="btn" required pattern="[a-z][a-z0-9_]{1,63}" value={name}
              onChange={(e) => setName(e.target.value)} placeholder="e.g. alu8" title="lower case, digits and _; becomes the Verilog top name" /></label>
            <label>Target clock (MHz)<input id="np-mhz" className="btn" type="number" min="1" max="2000" value={mhz} onChange={(e) => setMhz(e.target.value)} placeholder="from the spec" /></label>
          </div>
          <textarea id="np-request" className="btn" required minLength={10} rows={4} value={req} onChange={(e) => setReq(e.target.value)}
            placeholder="e.g. 8-bit ALU with add, subtract, AND, OR, XOR, shift left/right, compare; zero, carry, overflow, negative flags; registered outputs." />
          <button type="submit" className="btn pj-primary" disabled={busy}>{busy ? "Creating…" : "Create project"}</button>
        </form>
      </div>
    </div>
  );
}

// --- page -------------------------------------------------------------------------------------------------
function Projects() {
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [mode, setMode] = useState<"design" | "new">("design");
  const load = useCallback(() => {
    getJSON<ProjectRow[]>("/projects", 15000).then((p) => {
      setProjects(p); setErr(null);
      setSel((cur) => cur ?? (typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("design") : null) ?? p[0]?.designs[0]?.id ?? null);
    }).catch((e: Error) => setErr(`API unreachable (${e.message}). Is the backend running on port 8000?`));
  }, []);
  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);
  const select = (id: string) => {
    setSel(id); setMode("design");
    const u = new URL(window.location.href); u.searchParams.set("design", id); window.history.replaceState(null, "", u.toString());
  };
  return (
    <div className="pj-wrap">
      <div className="pj-top">
        <span className="display pj-brand">S2S Projects</span>
        <Link href="/" className="btn">Live Office</Link>
      </div>
      <div className="pj-grid">
        <Sidebar projects={projects} sel={mode === "design" ? sel : null} onSelect={select} onNew={() => setMode("new")} err={err} />
        {mode === "new" ? <NewProject onCreated={(id) => { load(); select(id); }} />
          : sel ? <DesignView designId={sel} /> : <div className="card pj-pad"><p className="muted">Choose a design on the left, or start a new project.</p></div>}
      </div>
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<p className="muted">Loading…</p>}><Projects /></Suspense>;
}
