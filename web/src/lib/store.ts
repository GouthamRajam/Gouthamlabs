// Live Office state. Every event goes through applyEvent(); each of the 21 event types
// produces a visible change (Part 12.4 #1). The visual effect of each type follows the
// "Live Office effect" column of Part 11.2.
import { create } from "zustand";
import { approversOf, SEATS } from "./org";
import { type EventType, type Mode, type S2SEvent, type Status, STAGE_INDEX, STATUSES } from "./types";

export const FEED_LIMIT = 500; // Part 11.3: keep the last 500 events in memory
const SEEN_LIMIT = 20000;

export type BubbleKind = "think" | "work" | "ok" | "bad" | "review" | "wait";

export interface AgentState {
  status: Status;
  bubble?: { text: string; kind: BubbleKind; type: EventType; at: number };
  task?: { id: string; title: string; stage: string | null; progress: number; evidence?: string };
  plan?: string;
  flash?: { kind: "ok" | "bad" | "money"; at: number };
  tool?: { name: string; at: number };
  checkin?: { by?: string; at: number };
  findings: number;
  budgetWarning: boolean;
  escalated: boolean;
  stalled: boolean;
  stallsFlagged: string[]; // (managers) ids of stalled tasks flagged to this agent; cleared on progress
  gates: { gate: string; status: "pending" | "approved" | "rejected"; at: number }[];
  files: string[];
  tools: string[];
  checks: { passed: number; failed: number };
  messages: { dir: "sent" | "received"; other: string; text: string; ts: string }[];
  timeline: S2SEvent[]; // newest first
  lastType?: EventType;
}

export interface Handoff { id: string; from: string; to: string; at: number }
export interface Toast { id: string; text: string; kind: "bad" | "wait"; at: number }

export interface OfficeState {
  mode: Mode;
  connection: "connecting" | "open" | "closed" | "offline";
  replay?: { runId: string; speed: number; playing: boolean; position: number; total: number };
  // stageIndex: current stage (pipeline position); complete: the run finished (stages before
  // stageIndex are done, none is current). A partial run (e.g. spec..architecture) is not
  // shown as all 10 stages done.
  run: { id?: string; design?: string; stage?: string; stageIndex: number; complete?: boolean };
  agents: Record<string, AgentState>;
  counters: { toolRuns: number; checksPassed: number; checksFailed: number; openFindings: number; pendingGates: number };
  spendUsd?: number;
  financeFlashAt?: number;
  feed: S2SEvent[]; // newest first
  handoffs: Handoff[];
  toasts: Toast[];
  selected: string | null;
  seen: Set<string>; // event ids already applied (stream + backfill de-duplication); mutable, capped
  applied: number;
}

const blankAgent = (): AgentState => ({
  status: "idle", findings: 0, budgetWarning: false, escalated: false, stalled: false, stallsFlagged: [], gates: [], files: [],
  tools: [], checks: { passed: 0, failed: 0 }, messages: [], timeline: [],
});

const initialAgents = (): Record<string, AgentState> =>
  Object.fromEntries(Object.keys(SEATS).map((id) => [id, blankAgent()]));

export const initialState = (mode: Mode): OfficeState => ({
  mode, connection: mode === "demo" ? "offline" : "connecting", run: { stageIndex: -1 },
  agents: initialAgents(), counters: { toolRuns: 0, checksPassed: 0, checksFailed: 0, openFindings: 0, pendingGates: 0 },
  feed: [], handoffs: [], toasts: [], selected: null, seen: new Set(), applied: 0,
});

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());
const str = (v: unknown) => (typeof v === "string" ? v : undefined);
const push = <T,>(list: T[], item: T, max: number) => [item, ...list].slice(0, max);
const uniq = (list: string[], item?: string) => (item && !list.includes(item) ? [...list, item] : list);

function kindOf(type: EventType, ev: S2SEvent): BubbleKind {
  switch (type) {
    case "plan": case "research.brief": return "think";
    case "check.passed": case "task.completed": case "gate.decided": return "ok";
    case "check.failed": case "escalation": case "task.stalled": return "bad";
    case "finding": return "review";
    case "handoff": case "gate.requested": case "budget.warning": return "wait";
    default: return ev.status === "blocked" ? "bad" : "work";
  }
}

/** Apply one event. Returns the new state; untouched agents keep their object identity. */
export function applyEvent(s: OfficeState, ev: S2SEvent): OfficeState {
  if (s.seen.has(ev.id)) return s;
  s.seen.add(ev.id);
  if (s.seen.size > SEEN_LIMIT) for (const old of [...s.seen].slice(0, s.seen.size - SEEN_LIMIT)) s.seen.delete(old);
  const t = now();
  const agents = { ...s.agents };
  const counters = { ...s.counters };
  let { handoffs, toasts, run, spendUsd, financeFlashAt } = s;
  const touched = new Set<string>();
  const edit = (id: string | null | undefined, fn: (a: AgentState) => AgentState) => {
    if (!id || !agents[id]) return;
    agents[id] = fn(touched.has(id) ? agents[id] : { ...agents[id] });
    touched.add(id);
  };
  const say = (id: string | null | undefined, text: string) =>
    edit(id, (a) => ({ ...a, bubble: { text, kind: kindOf(ev.type, ev), type: ev.type, at: t } }));
  const d = ev.detail ?? {};
  const actor = ev.agent_id;

  edit(actor, (a) => ({ ...a, timeline: push(a.timeline, ev, 50), lastType: ev.type }));

  switch (ev.type) {
    case "agent.status": {
      const st = (STATUSES as readonly string[]).includes(ev.status ?? "") ? (ev.status as Status) : "idle";
      edit(actor, (a) => ({ ...a, status: st }));
      break;
    }
    case "task.started": {
      const title = ev.summary.replace(/^[^:]+:\s*/, "");
      edit(actor, (a) => ({ ...a, status: "working", stalled: false,
        task: { id: ev.task_id ?? "", title, stage: ev.stage, progress: 0 } }));
      say(actor, title);
      break;
    }
    case "plan":
      edit(actor, (a) => ({ ...a, plan: ev.summary }));
      say(actor, ev.summary);
      break;
    case "tool_call": {
      const tool = str(d.tool) ?? "tool";
      counters.toolRuns += 1;
      edit(actor, (a) => ({ ...a, tool: { name: tool, at: t }, tools: uniq(a.tools, tool) }));
      break;
    }
    case "tool_result":
      edit(actor, (a) => ({ ...a, tools: uniq(a.tools, str(d.tool)) }));
      say(actor, ev.summary);
      break;
    case "artifact.created":
      edit(actor, (a) => ({ ...a, files: uniq(a.files, str(d.path) ?? ev.summary) }));
      break;
    case "check.passed":
    case "check.failed": {
      const ok = ev.type === "check.passed";
      if (ok) counters.checksPassed += 1; else counters.checksFailed += 1;
      edit(actor, (a) => ({ ...a, flash: { kind: ok ? "ok" : "bad", at: t },
        checks: { passed: a.checks.passed + (ok ? 1 : 0), failed: a.checks.failed + (ok ? 0 : 1) } }));
      break;
    }
    case "handoff": {
      const to = ev.to_agent_id;
      if (actor && to) handoffs = [...handoffs.filter((h) => t - h.at < 2500), { id: ev.id, from: actor, to, at: t }];
      edit(actor, (a) => ({ ...a, messages: push(a.messages, { dir: "sent", other: to ?? "?", text: ev.summary, ts: ev.ts }, 30) }));
      edit(to, (a) => ({ ...a, messages: push(a.messages, { dir: "received", other: actor ?? "?", text: ev.summary, ts: ev.ts }, 30) }));
      say(actor, ev.summary);
      break;
    }
    case "finding":
      counters.openFindings += 1;
      edit(ev.to_agent_id ?? actor, (a) => ({ ...a, findings: a.findings + 1 }));
      say(actor, ev.summary);
      break;
    case "gate.requested":
    case "gate.decided": {
      const gate = str(d.gate) ?? "G?";
      const decided = ev.type === "gate.decided";
      const status = !decided ? "pending" : str(d.decision) === "reject" ? "rejected" : "approved";
      for (const h of approversOf(gate)) {
        edit(h, (a) => ({ ...a, status: decided ? "idle" : "waiting",
          gates: [...a.gates.filter((g) => g.gate !== gate), { gate, status, at: t }] }));
      }
      counters.pendingGates = Math.max(0, counters.pendingGates + (decided ? -1 : 1));
      say(actor, ev.summary);
      break;
    }
    case "task.completed":
      edit(actor, (a) => ({ ...a, task: a.task ? { ...a.task, progress: 1 } : a.task, stalled: false }));
      say(actor, ev.summary);
      break;
    case "budget.warning":
      edit(actor, (a) => ({ ...a, budgetWarning: true }));
      say(actor, ev.summary);
      break;
    case "escalation": {
      edit(ev.to_agent_id && agents[ev.to_agent_id] ? ev.to_agent_id : actor, (a) => ({ ...a, escalated: true }));
      toasts = [...toasts.filter((x) => t - x.at < 8000), { id: ev.id, text: ev.summary, kind: "bad" as const, at: t }].slice(-4);
      break;
    }
    case "stage.changed": {
      const to = str(d.to) ?? ev.stage ?? undefined;
      if (ev.run_id && ev.run_id !== run.id) run = { stageIndex: -1 }; // a different run: fresh pipeline
      if (to === "done") run = { ...run, id: ev.run_id ?? run.id, stage: to, complete: true,
        stageIndex: run.stageIndex >= 0 && !run.complete ? run.stageIndex + 1 : run.stageIndex };
      else run = { ...run, id: ev.run_id ?? run.id, stage: to, complete: false,
        stageIndex: to ? STAGE_INDEX[to] ?? run.stageIndex : run.stageIndex };
      say(actor, ev.summary);
      break;
    }
    case "task.heartbeat": {
      const p = typeof ev.progress === "number" ? ev.progress : 0;
      edit(actor, (a) => ({ ...a, stalled: false,
        task: { ...(a.task ?? { id: ev.task_id ?? "", title: ev.stage ?? "task", stage: ev.stage }), progress: p,
          evidence: str(d.evidence_signal) } }));
      break;
    }
    case "task.stalled":
      edit(actor, (a) => ({ ...a, stalled: true }));
      if (ev.task_id) edit(ev.to_agent_id, (a) => ({ ...a, stallsFlagged: uniq(a.stallsFlagged, ev.task_id!) }));
      say(actor, ev.summary);
      break;
    case "manager.checkin":
      edit(actor, (a) => ({ ...a, checkin: { by: actor ?? undefined, at: t } }));
      break;
    case "budget.alert": {
      const spent = typeof d.spent_usd === "number" ? d.spent_usd : undefined;
      if (spent !== undefined) spendUsd = spent;
      financeFlashAt = t;
      edit(actor ?? "Penny", (a) => ({ ...a, flash: { kind: "money", at: t } }));
      say(actor ?? "Penny", ev.summary);
      break;
    }
    case "research.brief":
      say(actor, ev.summary);
      break;
  }
  if ((ev.type === "task.heartbeat" || ev.type === "task.completed") && ev.task_id) {
    for (const [id, a] of Object.entries(agents)) {
      if (a.stallsFlagged.includes(ev.task_id)) edit(id, (x) => ({ ...x, stallsFlagged: x.stallsFlagged.filter((t) => t !== ev.task_id) }));
    }
  }
  if (ev.run_id && ev.run_id !== run.id && ev.type !== "stage.changed") run = { ...run, id: ev.run_id };

  return {
    ...s, agents, counters, handoffs, toasts, run, spendUsd, financeFlashAt,
    feed: push(s.feed, ev, FEED_LIMIT), applied: s.applied + 1,
  };
}

interface Actions {
  reset: (mode: Mode) => void;
  apply: (ev: S2SEvent) => void;
  applyMany: (evs: S2SEvent[]) => void;
  select: (id: string | null) => void;
  set: (p: Partial<OfficeState>) => void;
}

export const useOffice = create<OfficeState & Actions>((set) => ({
  ...initialState("demo"),
  reset: (mode) => set(() => initialState(mode)),
  apply: (ev) => set((s) => applyEvent(s, ev)),
  applyMany: (evs) => set((s) => evs.reduce(applyEvent, s as OfficeState)),
  select: (id) => set(() => ({ selected: id })),
  set: (p) => set(() => p),
}));
