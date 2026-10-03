"use client";
import { useEffect, useState } from "react";
import { ORG, ROOMS, SEATS } from "@/lib/org";
import { useOffice } from "@/lib/store";

const COLOR: Record<string, string> = {
  idle: "var(--idle)", thinking: "var(--think)", working: "var(--accent)", waiting: "var(--wait)",
  blocked: "var(--bad)", reviewing: "var(--review)",
};

function Who({ id }: { id: string }) {
  const a = useOffice((s) => s.agents[id]);
  const select = useOffice((s) => s.select);
  const seat = SEATS[id];
  return (
    <button type="button" className="btn" style={{ border: 0, padding: "0 4px", background: "none" }} onClick={() => select(id)}
      data-agent={id} aria-label={`${seat.name}, ${seat.role}, ${a.status}`}>
      <span className="st" style={{ borderColor: COLOR[a.status] }} />
      <b>{seat.name}</b> <span className="muted">{seat.role}</span>
      {a.stalled && <span className="gate-banner" style={{ marginLeft: 6 }}>STALL</span>}
      {seat.phase > 0 && <span className="muted"> (Phase {seat.phase}+)</span>}
    </button>
  );
}

/** Org chart with live status (Part 12.2 "Org view"). */
export function OrgView() {
  return (
    <div className="card org" style={{ padding: 16 }} data-testid="org-view">
      <div style={{ marginBottom: 8 }}><b>CEO:</b> {ORG.ceo}</div>
      <ul>
        {ORG.divisions.map((d) => {
          const room = ROOMS[d.id];
          const tables = room.children?.map((c) => ROOMS[c]) ?? [];
          return (
            <li key={d.id}>
              <b>{d.name}</b> <span className="muted">· {d.human_owner}</span>
              <ul>
                {room.head && SEATS[room.head]?.kind === "director" && <li><Who id={room.head} /></li>}
                {tables.map((t) => (
                  <li key={t.id}><span className="muted">{t.label}</span>
                    <ul>{t.seats.map((s) => <li key={s}><Who id={s} /></li>)}</ul>
                  </li>
                ))}
                {!tables.length && room.seats.filter((s) => SEATS[s].kind !== "director").map((s) => <li key={s}><Who id={s} /></li>)}
              </ul>
            </li>
          );
        })}
        <li><b>Human leaders</b><ul>{ROOMS.humans.seats.map((s) => <li key={s}><Who id={s} /></li>)}</ul></li>
      </ul>
    </div>
  );
}

export const TOAST_MS = 8000;

export function Toasts() {
  const toasts = useOffice((s) => s.toasts);
  const [, tick] = useState(0);
  // re-check every second so toasts disappear after TOAST_MS even when nothing else changes
  useEffect(() => { if (!toasts.length) return; const t = setInterval(() => tick((n) => n + 1), 1000); return () => clearInterval(t); }, [toasts.length]);
  const recent = toasts.filter((t) => performance.now() - t.at < TOAST_MS);
  if (!recent.length) return null;
  return (
    <div className="toasts" role="alert" aria-live="assertive">
      {recent.map((t) => <div key={t.id} className="toast" data-effect="escalation"><b>Escalation</b> — {t.text}</div>)}
    </div>
  );
}
