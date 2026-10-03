"use client";
import { useEffect, useState } from "react";
import { getJSON } from "@/lib/api";
import { SEATS } from "@/lib/org";
import { useOffice } from "@/lib/store";
import type { S2SEvent } from "@/lib/types";

const STATUS_COLOR: Record<string, string> = {
  idle: "var(--idle)", thinking: "var(--think)", working: "var(--accent)", waiting: "var(--wait)",
  blocked: "var(--bad)", reviewing: "var(--review)",
};

interface AgentDetail {
  current_task: null | { id: string; title: string; usage: Record<string, number>; budget: Record<string, number>; percent: number };
  recent_events: S2SEvent[];
}

const hhmmss = (ts: string) => new Date(ts).toLocaleTimeString([], { hour12: false });

export function Panel() {
  const id = useOffice((s) => s.selected);
  const mode = useOffice((s) => s.mode);
  const a = useOffice((s) => (id ? s.agents[id] : undefined));
  const [detail, setDetail] = useState<AgentDetail | null>(null);

  // Live/replay: fill in budget usage and older history from the API, after the panel is shown.
  useEffect(() => {
    setDetail(null);
    if (!id || mode === "demo" || SEATS[id]?.kind === "human") return;
    let cancelled = false;
    getJSON<AgentDetail>(`/agents/${encodeURIComponent(id)}`).then((d) => { if (!cancelled) setDetail(d); }).catch(() => {});
    return () => { cancelled = true; };
  }, [id, mode]);

  if (!id || !a) {
    return (
      <aside className="panel card" aria-label="Agent detail" data-testid="panel">
        <p className="muted">Select any seat to see who it is, what it is working on and what it has done.</p>
      </aside>
    );
  }
  const seat = SEATS[id];
  const timeline = a.timeline.length ? a.timeline : (detail?.recent_events ?? []);
  const usage = detail?.current_task?.usage;
  const budget = detail?.current_task?.budget;
  return (
    <aside className="panel card" aria-label={`Agent detail: ${seat.name}`} data-testid="panel" data-agent={id}>
      <div>
        <h2 data-testid="panel-name">{seat.name}</h2>
        <div className="muted" data-testid="panel-role">{seat.role}</div>
        <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap" }}>
          <span className="pill" data-testid="panel-status"><i style={{ background: STATUS_COLOR[a.status] }} />{a.status}</span>
          {a.stalled && <span className="pill" style={{ borderColor: "var(--accent)" }}>stalled</span>}
          {seat.phase > 0 && <span className="pill">starts in Phase {seat.phase}</span>}
          {mode === "demo" && <span className="pill badge-sim">simulated</span>}
        </div>
      </div>
      <div className="sec">
        <h3>Persona and expertise</h3>
        <div data-testid="panel-mission">{seat.mission ?? "—"}</div>
      </div>
      <div className="sec" data-testid="panel-task">
        <h3>Current task</h3>
        {a.task ? (
          <>
            <div>{a.task.title} <span className="muted mono">({a.task.stage ?? "—"})</span></div>
            <div className="bar" aria-label={`progress ${Math.round(a.task.progress * 100)}%`}>
              <span style={{ width: `${Math.round(a.task.progress * 100)}%` }} />
            </div>
            <small className="muted mono">{Math.round(a.task.progress * 100)}%{a.task.evidence ? ` · ${a.task.evidence}` : ""}</small>
          </>
        ) : <div className="muted">No task assigned</div>}
      </div>
      <div className="sec"><h3>Plan</h3><div data-testid="panel-plan">{a.plan ?? <span className="muted">—</span>}</div></div>
      <div className="stats" data-testid="panel-stats">
        <div><b>{a.checks.passed}</b><small>checks passed</small></div>
        <div><b>{a.checks.failed}</b><small>checks failed</small></div>
        <div><b>{a.files.length}</b><small>files</small></div>
        <div><b>{a.messages.length}</b><small>messages</small></div>
      </div>
      <div className="sec"><h3>Budget used</h3>
        <div className="mono" data-testid="panel-budget" style={{ fontSize: 12.5 }}>
          {usage && budget ? (
            <>
              tokens {usage.tokens ?? 0} / {budget.max_tokens ?? "—"} · tool runs {usage.tool_runs ?? 0} / {budget.max_tool_runs ?? "—"} ·
              ${Number(usage.cost_usd ?? 0).toFixed(4)}
            </>
          ) : mode === "demo" ? "simulated" : a.task ? "loading…" : "—"}
        </div>
      </div>
      <div className="sec"><h3>Files touched</h3>
        <div className="chips" data-testid="panel-files">{a.files.length ? a.files.map((f) => <span key={f} title={f}>{f}</span>) : <span>none</span>}</div>
      </div>
      <div className="sec"><h3>Tools used</h3>
        <div className="chips" data-testid="panel-tools">{a.tools.length ? a.tools.map((t) => <span key={t}>{t}</span>) : <span>none</span>}</div>
      </div>
      <div className="sec"><h3>Messages</h3>
        <ul className="hist" data-testid="panel-messages">
          {a.messages.length ? a.messages.slice(0, 8).map((m, i) => (
            <li key={i}><time>{hhmmss(m.ts)}</time><span>{m.dir === "sent" ? `→ ${m.other}` : `← ${m.other}`}: {m.text}</span></li>
          )) : <li><span className="muted">none</span></li>}
        </ul>
      </div>
      <div className="sec"><h3>Recent actions</h3>
        <ul className="hist" data-testid="panel-timeline">
          {timeline.slice(0, 20).map((e) => (
            <li key={e.id}><time>{hhmmss(e.ts)}</time><span><span className="mono muted">{e.type}</span> {e.summary}</span></li>
          ))}
          {!timeline.length && <li><span className="muted">nothing yet</span></li>}
        </ul>
      </div>
    </aside>
  );
}
