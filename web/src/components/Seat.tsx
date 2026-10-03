"use client";
import { memo, useEffect, useLayoutEffect, useRef, useState } from "react";
import { SEATS } from "@/lib/org";
import { useOffice } from "@/lib/store";

/** True for `ms` after `at` changes (transient effects: flashes, bubbles, tool pulses). */
function useTransient(at: number | undefined, ms: number): boolean {
  const [on, setOn] = useState(false);
  useEffect(() => {
    if (at === undefined) return;
    setOn(true);
    const t = setTimeout(() => setOn(false), ms);
    return () => clearTimeout(t);
  }, [at, ms]);
  return on;
}

export const BUBBLE_MS = 4500;

function SeatImpl({ id }: { id: string }) {
  const seat = SEATS[id];
  const a = useOffice((s) => s.agents[id]);
  const selected = useOffice((s) => s.selected === id);
  const select = useOffice((s) => s.select);
  const flashOn = useTransient(a.flash?.at, 900);
  const toolOn = useTransient(a.tool?.at, 2500);
  const bubbleOn = useTransient(a.bubble?.at, BUBBLE_MS);
  const checkinOn = useTransient(a.checkin?.at, 3000);
  const ref = useRef<HTMLButtonElement>(null);
  const [side, setSide] = useState<"mid" | "left" | "right">("mid");
  // Keep the bubble on screen: near an edge, anchor it toward the inside.
  useLayoutEffect(() => {
    if (!bubbleOn || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const vw = window.innerWidth;
    setSide(r.left + r.width / 2 < 110 ? "left" : vw - (r.left + r.width / 2) < 110 ? "right" : "mid");
  }, [bubbleOn]);
  // decided gates show briefly ("G1 approved"), then the banner goes away
  const lastDecided = a.gates.filter((g) => g.status !== "pending").reduce<number | undefined>((m, g) => Math.max(m ?? 0, g.at), undefined);
  const decidedOn = useTransient(lastDecided, 6000);
  const gates = a.gates.filter((g) => g.status === "pending" || (decidedOn && g.at === lastDecided));
  const stalledHere = a.stalled || a.stallsFlagged.length > 0;
  const cls = ["seat", seat.kind === "human" ? "human" : "", seat.kind === "director" || seat.kind === "manager" ? "mgr" : "",
    seat.phase > 0 ? "later" : "", flashOn && a.flash ? `flash-${a.flash.kind}` : ""].filter(Boolean).join(" ");
  const label = `${seat.name}, ${seat.role}, ${a.status}${a.stalled ? ", stalled" : a.stallsFlagged.length ? ", a managed task is stalled" : ""}${seat.phase > 0 ? `, starts in Phase ${seat.phase}` : ""}`;

  return (
    <button type="button" ref={ref} className={cls} data-agent={id} data-status={a.status} data-flash={flashOn ? a.flash?.kind : undefined}
      data-effect={flashOn ? (a.flash?.kind === "money" ? "budget.alert" : a.flash?.kind === "ok" ? "check.passed" : "check.failed") : undefined}
      aria-pressed={selected} aria-label={label} title={label} onClick={() => select(id)}>
      {bubbleOn && a.bubble && (
        <span className={`bubble k-${a.bubble.kind} b-${side}`} data-effect={a.bubble.type} role="status">{a.bubble.text}</span>
      )}
      <span className="av" aria-hidden="true">
        {seat.initials}
        <span className="dots"><i /><i /><i /></span>
        {toolOn && a.tool && <span className="tool-chip" data-effect="tool_call">{a.tool.name}</span>}
        {a.findings > 0 && <span className="bdg bdg-finding" data-effect="finding" title="open findings">⚠{a.findings}</span>}
        {a.budgetWarning && <span className="bdg bdg-budget" data-effect="budget.warning" title="budget near limit">$</span>}
        {a.escalated && <span className="bdg bdg-esc" data-effect="escalation" title="escalated">!</span>}
        {stalledHere && <span className="bdg bdg-stall" data-effect="task.stalled" title={a.stalled ? "stalled" : "a task you manage is stalled"}>STALL</span>}
        {checkinOn && <span className="bdg bdg-checkin" data-effect="manager.checkin" title="manager check-in">✓</span>}
        {a.files.length > 0 && <span className="bdg bdg-files" data-effect="artifact.created" title="files">{a.files.length}</span>}
      </span>
      <span className="nm">{seat.name}</span>
      {a.task && a.task.progress < 1 && seat.kind !== "human" ? (
        <span className="prog" data-effect="task.heartbeat" aria-hidden="true">
          <span style={{ transform: `scaleX(${a.task.progress})` }} />
        </span>
      ) : <span className="rl">{seat.kind === "human" ? seat.role.split(" (")[0] : seat.role}</span>}
      {gates.map((g) => (
        <span key={g.gate} className={`gate-banner ${g.status}`}
          data-effect={g.status === "pending" ? "gate.requested" : "gate.decided"}>
          {g.gate} {g.status === "pending" ? "awaiting review" : g.status}
        </span>
      ))}
    </button>
  );
}

export const Seat = memo(SeatImpl);
