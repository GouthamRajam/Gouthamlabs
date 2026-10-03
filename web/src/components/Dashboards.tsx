"use client";
import { useEffect, useState } from "react";
import { getJSON } from "@/lib/api";
import { SEATS } from "@/lib/org";
import { useOffice } from "@/lib/store";

/** Poll an API path every `ms` (live/replay modes). Replay shows the API's current data. */
function usePoll<T>(path: string, ms = 2000): { data: T | null; error: string | null } {
  const mode = useOffice((s) => s.mode);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (mode === "demo") return;
    let alive = true;
    const load = () => getJSON<T>(path).then((d) => { if (alive) { setData(d); setError(null); } })
      .catch((e: Error) => { if (alive) setError(e.message); });
    load();
    const t = setInterval(load, ms);
    return () => { alive = false; clearInterval(t); };
  }, [path, ms, mode]);
  return { data, error };
}

export const usd = (x: number | null | undefined) =>
  x === null || x === undefined ? "—" : `$${x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const SimNote = () => (
  <p className="sim-banner" data-testid="dash-sim">Simulation: these numbers come from the scripted demo, not from a real system.</p>
);

interface TaskRow {
  id: string; run_id: string; agent_id: string; stage: string; title: string; percent: number;
  evidence_signal: string | null; silent_for_s?: number | null; stalled_at: string | null; last_progress_at: string | null;
}
const silentMin = (t: TaskRow) => t.last_progress_at ? (Date.now() - Date.parse(t.last_progress_at)) / 60000 : null;
interface Dashboard {
  backlog: { pending: number; ready: number }; task_counts: Record<string, number>; running: TaskRow[];
  stalls: TaskRow[]; ready_past_assignment_sla: string[]; sla: Record<string, number>;
  assignments: { count: number; within_sla: number; sla_hit_rate: number | null; sla_s: number };
  team_metrics: Record<string, unknown>[];
}

export function Management() {
  const mode = useOffice((s) => s.mode);
  const agents = useOffice((s) => s.agents);
  const { data, error } = usePoll<Dashboard>("/management/dashboard");
  if (mode === "demo") {
    const running = Object.entries(agents).filter(([, a]) => a.task && a.task.progress < 1);
    const stalled = Object.entries(agents).filter(([id, a]) => a.stalled && SEATS[id]?.kind === "lead");
    return (
      <div className="flex flex-col gap-3" data-testid="management">
        <SimNote />
        <div className="kpis">
          <div className="card kpi"><b>{running.length}</b><small>running tasks</small></div>
          <div className="card kpi"><b data-testid="stall-count">{stalled.length}</b><small>stalls</small></div>
        </div>
        <section className="card" style={{ padding: 12 }}><h3 className="mono muted">Stalls</h3>
          <ul>{stalled.map(([id]) => <li key={id}>{id} (simulated)</li>)}{!stalled.length && <li className="muted">none</li>}</ul>
        </section>
      </div>
    );
  }
  if (!data) return <p className="muted" data-testid="management">{error ? `Cannot load /management/dashboard: ${error}` : "Loading…"}</p>;
  const hit = data.assignments.sla_hit_rate;
  return (
    <div className="flex flex-col gap-3" data-testid="management">
      {mode === "replay" && <p className="muted">Dashboards show the system's current state from the API, not the replayed moment.</p>}
      <div className="kpis">
        <div className="card kpi"><b data-testid="kpi-backlog">{data.backlog.pending + data.backlog.ready}</b><small>backlog ({data.backlog.ready} ready)</small></div>
        <div className="card kpi"><b>{data.running.length}</b><small>running tasks</small></div>
        <div className="card kpi"><b data-testid="stall-count">{data.stalls.length}</b><small>stalls</small></div>
        <div className="card kpi"><b>{hit === null ? "—" : `${(hit * 100).toFixed(1)}%`}</b>
          <small>assignment SLA hit rate ({data.assignments.within_sla}/{data.assignments.count} within {data.sla.assign_ready_task_minutes} min)</small></div>
      </div>
      <section className="card" style={{ padding: 12 }} aria-label="Stalls">
        <h3 className="mono muted" style={{ fontSize: 11, margin: "0 0 8px" }}>STALLS — no progress for longer than the stall SLA ({data.sla.stall_minutes} min)</h3>
        <div className="scroll-x"><table className="dt" data-testid="stalls-table"><thead><tr><th>Task</th><th>Agent</th><th>Stage</th><th className="num">Silent for</th><th>Last evidence</th><th>Flagged at</th></tr></thead>
          <tbody>
            {data.stalls.map((t) => (
              <tr key={t.id} className="row-stall" data-task={t.id}><td className="mono">{t.id}</td><td>{t.agent_id}</td><td>{t.stage}</td>
                <td className="num">{silentMin(t) != null ? `${Math.round(silentMin(t)!)} min` : "—"}</td>
                <td>{t.evidence_signal ?? "—"}</td><td className="mono">{t.stalled_at ? new Date(t.stalled_at).toLocaleTimeString([], { hour12: false }) : ""}</td></tr>
            ))}
            {!data.stalls.length && <tr><td colSpan={6} className="muted">No stalls</td></tr>}
          </tbody></table></div>
      </section>
      <section className="card" style={{ padding: 12 }} aria-label="Running tasks">
        <h3 className="mono muted" style={{ fontSize: 11, margin: "0 0 8px" }}>RUNNING TASKS</h3>
        <div className="scroll-x"><table className="dt"><thead><tr><th>Agent</th><th>Task</th><th className="num">Progress</th><th>Evidence</th><th className="num">Silent</th></tr></thead>
          <tbody>
            {data.running.map((t) => (
              <tr key={t.id} className={t.stalled_at ? "row-stall" : ""}><td>{t.agent_id}</td><td>{t.title} <span className="muted mono">{t.stage}</span></td>
                <td className="num">{Math.round(t.percent * 100)}%</td><td>{t.evidence_signal ?? "—"}</td>
                <td className="num">{t.silent_for_s != null ? `${t.silent_for_s.toFixed(0)} s` : "—"}</td></tr>
            ))}
            {!data.running.length && <tr><td colSpan={5} className="muted">Nothing running</td></tr>}
          </tbody></table></div>
      </section>
      <section className="card" style={{ padding: 12 }} aria-label="SLAs and team metrics">
        <h3 className="mono muted" style={{ fontSize: 11, margin: "0 0 8px" }}>SLAs (config/management.yaml) AND TEAM METRICS</h3>
        <div className="chips">{Object.entries(data.sla).map(([k, v]) => <span key={k}>{k}: {v}</span>)}</div>
        <p className="muted" style={{ marginBottom: 0 }}>{data.team_metrics.length ? `${data.team_metrics.length} team metric rows` :
          "No team metrics computed yet (throughput, cycle time, first-pass yield arrive with the manager runtime, M0.5)."}</p>
      </section>
    </div>
  );
}

interface Finance {
  total_usd: number; today_usd: number; records: number; as_of: string;
  by_source: Record<string, number>; by_model: Record<string, number>; by_agent: Record<string, number>; by_run: Record<string, number>;
  budgets: { id: string; scope: string; scope_id: string; limit_usd: number; spent_usd: number; pct: number }[];
  alerts: { id: string; budget_id: string; type: string; amount: number }[];
  credits: { provider: string; balance: number; expires_at: string | null }[];
  runway: null | number;
}

function Breakdown({ title, data, testid }: { title: string; data: Record<string, number>; testid?: string }) {
  const rows = Object.entries(data).sort((a, b) => b[1] - a[1]);
  return (
    <section className="card" style={{ padding: 12 }} aria-label={title}>
      <h3 className="mono muted" style={{ fontSize: 11, margin: "0 0 8px" }}>{title.toUpperCase()}</h3>
      <table className="dt" data-testid={testid}><tbody>
        {rows.slice(0, 12).map(([k, v]) => <tr key={k} data-key={k}><td className="mono">{k}</td><td className="num" title={`$${v}`}>{usd(v)}</td></tr>)}
        {!rows.length && <tr><td className="muted">none</td></tr>}
      </tbody></table>
    </section>
  );
}

export function FinanceTab() {
  const mode = useOffice((s) => s.mode);
  const spend = useOffice((s) => s.spendUsd);
  const { data, error } = usePoll<Finance>("/finance/summary");
  if (mode === "demo") {
    return (
      <div className="flex flex-col gap-3" data-testid="finance">
        <SimNote />
        <div className="kpis"><div className="card kpi"><b>{usd(spend ?? 0)}</b><small>simulated run spend</small></div></div>
      </div>
    );
  }
  if (!data) return <p className="muted" data-testid="finance">{error ? `Cannot load /finance/summary: ${error}` : "Loading…"}</p>;
  return (
    <div className="flex flex-col gap-3" data-testid="finance">
      <div className="kpis">
        <div className="card kpi"><b data-testid="fin-today" title={`$${data.today_usd}`}>{usd(data.today_usd)}</b><small>spend today (UTC)</small></div>
        <div className="card kpi"><b data-testid="fin-total" title={`$${data.total_usd}`}>{usd(data.total_usd)}</b><small>total metered ({data.records} usage records)</small></div>
        <div className="card kpi"><b>{data.alerts.length}</b><small>budget alerts</small></div>
        <div className="card kpi"><b data-testid="fin-runway">{data.runway === null ? "n/a" : data.runway}</b>
          <small>{data.runway === null ? "runway: needs ledger data (M0.9)" : "months of runway"}</small></div>
      </div>
      <section className="card" style={{ padding: 12 }} aria-label="Budget vs actual">
        <h3 className="mono muted" style={{ fontSize: 11, margin: "0 0 8px" }}>BUDGET VS ACTUAL</h3>
        <div className="scroll-x"><table className="dt" data-testid="budgets-table"><thead><tr><th>Scope</th><th className="num">Budget</th><th className="num">Spent</th><th>Used</th></tr></thead>
          <tbody>{data.budgets.slice(0, 15).map((b) => (
            <tr key={b.id} data-scope-id={b.scope_id}><td className="mono">{b.scope} {b.scope_id}</td><td className="num">{usd(b.limit_usd)}</td>
              <td className="num" title={`$${b.spent_usd}`}>{usd(b.spent_usd)}</td>
              <td style={{ minWidth: 120 }}><div className="bar"><span style={{ width: `${Math.min(100, b.pct)}%`,
                background: b.pct >= 100 ? "var(--bad)" : b.pct >= 80 ? "var(--accent)" : "var(--ok)" }} /></div>
                <small className="mono muted">{b.pct.toFixed(1)}%</small></td></tr>))}
            {!data.budgets.length && <tr><td colSpan={4} className="muted">No budgets yet</td></tr>}
          </tbody></table></div>
      </section>
      <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
        <Breakdown title="By source" data={data.by_source} testid="fin-by-source" />
        <Breakdown title="By model" data={data.by_model} />
        <Breakdown title="By agent" data={data.by_agent} />
        <Breakdown title="By run" data={data.by_run} testid="fin-by-run" />
      </div>
      <section className="card" style={{ padding: 12 }} aria-label="Credits">
        <h3 className="mono muted" style={{ fontSize: 11, margin: "0 0 8px" }}>CREDITS</h3>
        {data.credits.length ? <table className="dt"><tbody>{data.credits.map((c) => <tr key={c.provider}><td>{c.provider}</td><td className="num">{usd(c.balance)}</td><td>{c.expires_at ?? ""}</td></tr>)}</tbody></table>
          : <p className="muted" style={{ margin: 0 }}>No credit balances recorded yet (Grant tracks them from M0.9).</p>}
      </section>
      <p className="muted mono" style={{ fontSize: 11 }}>as of {new Date(data.as_of).toLocaleTimeString([], { hour12: false })} · amounts rounded to the cent; hover for exact values</p>
    </div>
  );
}
