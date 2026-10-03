"use client";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Management, FinanceTab } from "@/components/Dashboards";
import { Feed } from "@/components/Feed";
import { Floor } from "@/components/Floor";
import { OrgView, Toasts } from "@/components/OrgView";
import { Panel } from "@/components/Panel";
import { TopBar } from "@/components/TopBar";
import { backendReachable, getJSON, type RunSummary } from "@/lib/api";
import { startDemo, startLive, startReplay } from "@/lib/sources";
import { useOffice } from "@/lib/store";
import type { Mode, S2SEvent } from "@/lib/types";

const SPEEDS = [1, 2, 5, 10, 25, 50];

function useTheme() {
  const [theme, setTheme] = useState<"auto" | "light" | "dark">("auto");
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("theme");
    let saved: string | null = null;
    try { saved = localStorage.getItem("s2s-theme"); } catch { /* storage unavailable */ }
    const t = (q ?? saved ?? "auto") as "auto" | "light" | "dark";
    setTheme(t);
  }, []);
  useEffect(() => {
    if (theme === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("s2s-theme", theme); } catch { /* ignore */ }
  }, [theme]);
  return [theme, setTheme] as const;
}

function ReplayControls() {
  const replay = useOffice((s) => s.replay);
  const set = useOffice((s) => s.set);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  useEffect(() => { getJSON<RunSummary[]>("/runs?limit=30").then(setRuns).catch(() => setRuns([])); }, []);
  const go = (runId: string, speed: number) => {
    const u = new URL(window.location.href);
    u.searchParams.set("mode", "replay"); u.searchParams.set("run", runId); u.searchParams.set("speed", String(speed));
    window.location.href = u.toString();
  };
  return (
    <div className="card" style={{ padding: "8px 12px", display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }} data-testid="replay-controls">
      <span className="mono muted" style={{ fontSize: 12 }}>Replay run</span>
      <select className="btn" aria-label="Run to replay" value={replay?.runId ?? ""} onChange={(e) => go(e.target.value, replay?.speed ?? 10)}>
        <option value="" disabled>choose a run…</option>
        {runs.map((r) => <option key={r.id} value={r.id}>{r.id} · {r.design_name} · {r.status} · {r.events} events</option>)}
      </select>
      {replay && (
        <>
          <span className="mono muted" style={{ fontSize: 12 }}>speed</span>
          {SPEEDS.map((sp) => (
            <button key={sp} type="button" className="btn" aria-pressed={replay.speed === sp}
              onClick={() => set({ replay: { ...replay, speed: sp } })}>{sp}x</button>
          ))}
          <button type="button" className="btn" onClick={() => set({ replay: { ...replay, playing: !replay.playing } })}>
            {replay.playing ? "Pause" : "Play"}
          </button>
          <span className="mono muted" style={{ fontSize: 12 }} data-testid="replay-position">{replay.position}/{replay.total} events</span>
        </>
      )}
    </div>
  );
}

function Office() {
  const params = useSearchParams();
  const mode = useOffice((s) => s.mode);
  const reset = useOffice((s) => s.reset);
  const [tab, setTab] = useState<"office" | "management" | "finance">("office");
  const [view, setView] = useState<"floor" | "org">("floor");
  const [theme, setTheme] = useTheme();
  const [resolved, setResolved] = useState<Mode | null>(null);

  // Decide the mode: ?mode=live|replay|demo, else live if the API answers, else demo.
  useEffect(() => {
    const q = params.get("mode") as Mode | null;
    if (q === "live" || q === "replay" || q === "demo") { setResolved(q); return; }
    void backendReachable().then((ok) => setResolved(ok ? "live" : "demo"));
  }, [params]);

  useEffect(() => {
    if (!resolved) return;
    reset(resolved);
    const speed = Number(params.get("speed") ?? (resolved === "demo" ? 1 : 10));
    const run = params.get("run");
    const stop = resolved === "live" ? startLive()
      : resolved === "replay" ? (run ? startReplay(run, speed) : () => {})
      : startDemo(speed);
    if (params.get("testhooks") === "1") {
      (window as unknown as { __s2s: unknown }).__s2s = {
        apply: (ev: S2SEvent) => useOffice.getState().apply(ev),
        state: () => useOffice.getState(),
      };
    }
    return stop;
  }, [resolved, params, reset]);

  const switchMode = useCallback((m: Mode) => {
    const u = new URL(window.location.href);
    u.searchParams.set("mode", m);
    if (m !== "replay") { u.searchParams.delete("run"); u.searchParams.delete("speed"); }
    window.location.href = u.toString();
  }, []);

  return (
    <div className="wrap">
      <TopBar />
      {mode === "demo" && (
        <div className="sim-banner" role="note" data-testid="sim-banner">
          <b>Simulation.</b> No backend is connected: this is a built-in scripted demo of how S2S operates.
          Nothing shown here is real tool output.
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "space-between" }}>
        <div role="tablist" aria-label="Views" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {(["office", "management", "finance"] as const).map((t) => (
            <button key={t} type="button" role="tab" className="btn" aria-selected={tab === t} data-testid={`tab-${t}`}
              onClick={() => setTab(t)}>{t === "office" ? "Office" : t === "management" ? "Management" : "Finance"}</button>
          ))}
          {tab === "office" && (
            <span style={{ display: "inline-flex", gap: 6, marginLeft: 8 }}>
              <button type="button" className="btn" aria-pressed={view === "floor"} onClick={() => setView("floor")} data-testid="view-floor">Floor view</button>
              <button type="button" className="btn" aria-pressed={view === "org"} onClick={() => setView("org")} data-testid="view-org">Org view</button>
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }} role="group" aria-label="Mode and theme">
          {(["live", "replay", "demo"] as const).map((m) => (
            <button key={m} type="button" className="btn" aria-pressed={mode === m} onClick={() => switchMode(m)} data-testid={`mode-${m}`}>
              {m === "demo" ? "Demo (simulation)" : m[0].toUpperCase() + m.slice(1)}
            </button>
          ))}
          <button type="button" className="btn" data-testid="theme-toggle"
            onClick={() => setTheme(theme === "dark" ? "light" : theme === "light" ? "auto" : "dark")}>Theme: {theme}</button>
        </div>
      </div>
      {mode === "replay" && <ReplayControls />}
      {tab === "office" && (
        <>
          <div className="main">
            {view === "floor" ? <Floor /> : <OrgView />}
            <Panel />
          </div>
          <Feed />
        </>
      )}
      {tab === "management" && <Management />}
      {tab === "finance" && <FinanceTab />}
      <Toasts />
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<p className="muted">Loading…</p>}><Office /></Suspense>;
}
