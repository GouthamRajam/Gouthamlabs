"use client";
import { useEffect, useState } from "react";
import { useOffice } from "@/lib/store";
import { PIPELINE } from "@/lib/types";

function Clock() {
  const [now, setNow] = useState<Date | null>(null);
  const [start] = useState(() => Date.now());
  useEffect(() => { setNow(new Date()); const t = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(t); }, []);
  if (!now) return null;
  const up = Math.floor((now.getTime() - start) / 1000);
  const hms = [Math.floor(up / 3600), Math.floor(up / 60) % 60, up % 60].map((n) => String(n).padStart(2, "0")).join(":");
  return (
    <>
      <span>Time <b>{now.toLocaleTimeString([], { hour12: false })}</b></span>
      <span title="Time this view has been watching; the agents run 24x7">Watching <b>{hms}</b> · running 24x7</span>
    </>
  );
}

export function ModeBadge() {
  const mode = useOffice((s) => s.mode);
  const conn = useOffice((s) => s.connection);
  const replay = useOffice((s) => s.replay);
  if (mode === "demo") {
    return <span className="badge-mode badge-sim" data-testid="mode-badge" title="Scripted simulation, not real tool output">Simulation</span>;
  }
  if (mode === "replay") {
    return <span className="badge-mode badge-replay" data-testid="mode-badge">Replay {replay ? `${replay.speed}x` : ""}</span>;
  }
  return (
    <span className="badge-mode badge-live" data-testid="mode-badge" title={`WebSocket ${conn}`}>
      {conn === "open" && <span className="dot-live" aria-hidden="true" />}Live{conn !== "open" ? ` (${conn})` : ""}
    </span>
  );
}

export function TopBar() {
  const run = useOffice((s) => s.run);
  const c = useOffice((s) => s.counters);
  const spend = useOffice((s) => s.spendUsd);
  return (
    <>
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", justifyContent: "space-between", gap: "12px 24px" }}>
        <div>
          <h1 className="display" style={{ fontWeight: 700, fontSize: 28, margin: 0, lineHeight: 1.1 }}>
            S2S Live Office <ModeBadge />
          </h1>
          <p className="muted" style={{ margin: "4px 0 0" }}>The AI design team at work. Real tools decide pass/fail; humans approve at four gates.</p>
        </div>
        <div className="mono muted" style={{ display: "flex", flexWrap: "wrap", gap: "8px 18px", fontSize: 12.5 }}>
          <span>Run <b data-testid="run-id" style={{ color: "var(--fg)" }}>{run.id ?? "—"}</b></span>
          {spend !== undefined && <span>Run spend <b style={{ color: "var(--fg)" }} data-testid="run-spend">${spend.toFixed(2)}</b></span>}
          <Clock />
        </div>
      </header>
      <nav className="pipe" aria-label="Design flow stages" data-testid="pipeline">
        {PIPELINE.map((p, i) => (
          <div key={p.label} className={`stage${i < run.stageIndex ? " done" : i === run.stageIndex && !run.complete ? " now" : ""}`}
            data-effect={i === run.stageIndex || (run.complete && i === run.stageIndex - 1) ? "stage.changed" : undefined}
            aria-current={i === run.stageIndex && !run.complete ? "step" : undefined}>
            <div className="n">{i + 1} <span>{p.zone}</span></div>
            <div className="t">{p.label}</div>
          </div>
        ))}
      </nav>
      <div className="mono muted" style={{ display: "flex", flexWrap: "wrap", gap: "6px 22px", fontSize: 12.5 }} data-testid="counters">
        <span><b style={{ color: "var(--fg)" }} data-testid="c-tools">{c.toolRuns}</b> tool runs</span>
        <span><b style={{ color: "var(--fg)" }} data-testid="c-pass">{c.checksPassed}</b> checks passed</span>
        <span><b style={{ color: "var(--fg)" }} data-testid="c-fail">{c.checksFailed}</b> checks failed</span>
        <span><b style={{ color: "var(--fg)" }} data-testid="c-findings">{c.openFindings}</b> open findings</span>
        <span><b style={{ color: "var(--fg)" }} data-testid="c-gates">{c.pendingGates}</b> gates pending</span>
      </div>
    </>
  );
}
