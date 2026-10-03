// Event schema (MASTER_SPEC Part 11.1) and types (Part 11.2), as sent by the backend.

export const EVENT_TYPES = [
  "agent.status", "task.started", "plan", "tool_call", "tool_result", "artifact.created",
  "check.passed", "check.failed", "handoff", "finding", "gate.requested", "gate.decided",
  "task.completed", "budget.warning", "escalation", "stage.changed", "task.heartbeat",
  "task.stalled", "manager.checkin", "budget.alert", "research.brief",
] as const;
export type EventType = (typeof EVENT_TYPES)[number];

export const STATUSES = ["idle", "thinking", "working", "waiting", "blocked", "reviewing"] as const;
export type Status = (typeof STATUSES)[number];

export interface S2SEvent {
  id: string;
  ts: string; // ISO 8601, UTC
  run_id: string | null;
  design_id: string | null;
  team: string | null;
  agent_id: string | null;
  agent_name: string | null;
  stage: string | null;
  task_id: string | null;
  type: EventType;
  status: string | null;
  summary: string;
  detail: Record<string, unknown>;
  to_agent_id: string | null;
  progress: number | null;
  stream_id?: string;
}

export type Mode = "live" | "replay" | "demo";

// The 10 stages of Part 6.1 shown in the pipeline bar; backend stage names map onto them
// (Zone 2B test build and 2C closure are both stage 4, "Verify").
export const PIPELINE = [
  { label: "Spec", zone: "Z1" }, { label: "Arch", zone: "Z1" }, { label: "RTL", zone: "Z2A" },
  { label: "Verify", zone: "Z2B·C" }, { label: "Synth", zone: "Z3" }, { label: "DFT", zone: "Z3" },
  { label: "Floor", zone: "Z3" }, { label: "P&R", zone: "Z3" }, { label: "Signoff", zone: "Z4" },
  { label: "GDSII", zone: "Z4" },
] as const;
export const STAGE_INDEX: Record<string, number> = {
  spec: 0, architecture: 1, rtl: 2, test_build: 3, verification: 3, synthesis: 4, dft: 5,
  floorplan: 6, place_route: 7, signoff: 8, gdsii: 9, done: 10,
};
