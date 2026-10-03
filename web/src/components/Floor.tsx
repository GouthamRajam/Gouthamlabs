"use client";
import { useEffect, useRef, useState } from "react";
import { ROOM_ORDER, ROOMS, type Room } from "@/lib/org";
import { useOffice } from "@/lib/store";
import { Seat } from "./Seat";

function RoomBox({ room }: { room: Room }) {
  const later = room.phase > 0;
  const cls = ["room", room.kind === "zone" ? "zone" : "", room.kind === "group" ? "group" : "", later ? "phase-later" : ""]
    .filter(Boolean).join(" ");
  const rest = room.seats.filter((s) => s !== room.head);
  return (
    <section className={cls} aria-label={room.label} data-room={room.id}>
      <div className="hd">{room.label}</div>
      {room.kind === "group" ? (
        <>
          {room.head && <div className="head-row"><Seat id={room.head} /></div>}
          <div className="inner">{room.children?.map((c) => <RoomBox key={c} room={ROOMS[c]} />)}</div>
        </>
      ) : (
        <div className="seats">
          {room.head && <div className="head"><Seat id={room.head} /></div>}
          {rest.map((s) => <Seat key={s} id={s} />)}
        </div>
      )}
    </section>
  );
}

/** Animated handoff packets between two seats' real on-screen positions. */
function Packets({ floor }: { floor: React.RefObject<HTMLDivElement | null> }) {
  const handoffs = useOffice((s) => s.handoffs);
  const [frames, setFrames] = useState<{ id: string; x1: number; y1: number; x2: number; y2: number; k: number }[]>([]);
  useEffect(() => {
    const el = floor.current;
    if (!el || handoffs.length === 0) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const dur = reduce ? 1 : 1300;
    let raf = 0;
    const draw = () => {
      const box = el.getBoundingClientRect();
      const t = performance.now();
      const pos = (id: string) => {
        const s = el.querySelector(`[data-agent="${CSS.escape(id)}"] .av`)?.getBoundingClientRect();
        return s ? { x: s.left + s.width / 2 - box.left, y: s.top + s.height / 2 - box.top } : null;
      };
      const live = handoffs.filter((h) => t - h.at < dur + 900).map((h) => {
        const a = pos(h.from), b = pos(h.to);
        if (!a || !b) return null;
        return { id: h.id, x1: a.x, y1: a.y, x2: b.x, y2: b.y, k: Math.min(1, (t - h.at) / dur) };
      }).filter(Boolean) as typeof frames;
      setFrames(live);
      if (live.length) raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [handoffs, floor]);
  return (
    <svg className="links" aria-hidden="true">
      {frames.map((f) => {
        const e = f.k < 0.5 ? 2 * f.k * f.k : 1 - (-2 * f.k + 2) ** 2 / 2;
        return (
          <g key={f.id} data-effect="handoff">
            <line x1={f.x1} y1={f.y1} x2={f.x2} y2={f.y2} stroke="var(--accent)" strokeWidth={1.5} strokeDasharray="4 4" opacity={0.7} />
            <circle cx={f.x1 + (f.x2 - f.x1) * e} cy={f.y1 + (f.y2 - f.y1) * e} r={5} fill="var(--accent)" stroke="var(--surface)" strokeWidth={2} />
          </g>
        );
      })}
    </svg>
  );
}

export function Floor() {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <div className="floor" ref={ref} aria-label="Office floor by division">
      {([1, 2, 3] as const).map((c) => (
        <div className="col" key={c}>
          {ROOM_ORDER[c].map((r) => <RoomBox key={r} room={ROOMS[r]} />)}
        </div>
      ))}
      <Packets floor={ref} />
    </div>
  );
}
