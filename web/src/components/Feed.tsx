"use client";
import { memo, useMemo, useState } from "react";
import { DIVISIONS, divisionOf, SEATS } from "@/lib/org";
import { useOffice } from "@/lib/store";
import { EVENT_TYPES, type S2SEvent } from "@/lib/types";

const KIND: Partial<Record<S2SEvent["type"], string>> = {
  "check.passed": "ok", "task.completed": "ok", "gate.decided": "ok", "check.failed": "bad", escalation: "bad",
  "task.stalled": "bad", plan: "think", "research.brief": "think", finding: "review", handoff: "wait",
  "gate.requested": "wait", "budget.warning": "wait", "budget.alert": "wait", tool_call: "work", tool_result: "work",
};

/** One feed line. Memoized: a new event renders only its own row, not the 200 already shown. */
const Row = memo(function Row({ e, sim }: { e: S2SEvent; sim: boolean }) {
  return (
    <li data-type={e.type}>
      <time>{new Date(e.ts).toLocaleTimeString([], { hour12: false })}</time>
      <span className={`k ${KIND[e.type] ?? ""}`} aria-hidden="true" />
      <span className="who">{e.agent_id ?? "system"}</span>
      <span className="ty">{e.type}</span>
      <span className="txt">{sim && <span className="simtag">SIM</span>}{e.summary}</span>
    </li>
  );
});

/** Live activity feed, newest first; filter by team (division), agent or type (Part 12.2). */
export function Feed() {
  const feed = useOffice((s) => s.feed);
  const mode = useOffice((s) => s.mode);
  const [division, setDivision] = useState("");
  const [agent, setAgent] = useState("");
  const [type, setType] = useState("");
  const rows = useMemo(() => feed.filter((e) =>
    (!division || divisionOf(e.agent_id) === division || divisionOf(e.team) === division)
    && (!agent || e.agent_id === agent || e.to_agent_id === agent)
    && (!type || e.type === type)).slice(0, 200), [feed, division, agent, type]);
  return (
    <section className="card" style={{ padding: "12px 16px" }} aria-label="Activity feed">
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
        <h2 className="display" style={{ fontSize: 16, margin: 0, fontWeight: 600 }}>Activity feed</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          <select className="btn" aria-label="Filter by team" value={division} onChange={(e) => setDivision(e.target.value)}>
            <option value="">All teams</option>
            {DIVISIONS.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select className="btn" aria-label="Filter by agent" value={agent} onChange={(e) => setAgent(e.target.value)}>
            <option value="">All agents</option>
            {Object.values(SEATS).filter((s) => s.kind !== "human").map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <select className="btn" aria-label="Filter by type" value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">All types</option>
            {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>
      <ul className="feed" data-testid="feed">
        {rows.map((e) => <Row key={e.id} e={e} sim={mode === "demo"} />)}
        {!rows.length && <li><span /><span /><span className="muted">No events yet</span></li>}
      </ul>
    </section>
  );
}
