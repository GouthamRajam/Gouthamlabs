// Seats and rooms of the office floor, built from config/management.yaml (via
// src/generated/org.json). Part 12.2: one table per zone (1, 2A, 2B, 2C, 3, 4) with its
// manager at the head; rooms for Quality & Program Office, Platform, Finance, Research
// (and Customer, Phase 2+); human desks with gate banners.
import data from "@/generated/org.json";

export type SeatKind = "director" | "manager" | "lead" | "human";

export interface Seat {
  id: string; // agent id (= agent name) or "human:<id>"
  name: string;
  initials: string;
  role: string;
  kind: SeatKind;
  roomId: string;
  divisionId: string;
  teamId?: string;
  mission?: string;
  phase: number; // 0 = active in Phase 0
  approves?: string[]; // humans: gates/approvals
  owns?: string; // humans: what they own
  managerId?: string; // nearest manager/director agent
}

export interface Room {
  id: string;
  label: string;
  kind: "zone" | "group" | "room" | "humans";
  divisionId: string;
  column: 1 | 2 | 3;
  head?: string; // seat id at the head of the table
  seats: string[];
  phase: number;
  children?: string[]; // nested rooms (Division 2 holds tables 2A, 2B, 2C)
}

interface YTeam { id: string; name: string; lead: string; instances: number; phase?: number; mission?: string }
interface YDept { id: string; name: string; zone?: string; manager?: string; teams: YTeam[] }
interface YDiv {
  id: string; name: string; zone?: string; human_owner?: string; director?: string; phase?: number;
  teams?: YTeam[]; departments?: YDept[];
}
interface YHuman { id: string; name: string; title: string; approves: string[]; owns: string }

const org = data.org as unknown as { ceo: string; humans: YHuman[]; divisions: YDiv[] };
export const SLA = data.sla as Record<string, number>;
export const GATES_CFG = data.gates as { mode: string };

const initials = (name: string) =>
  name.replace(/[^A-Za-z ]/g, "").split(/\s+/).filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase()
  || name.slice(0, 2).toUpperCase();

const seatInitials = (name: string) => {
  const parts = name.split(/[\s-]+/).filter(Boolean);
  return parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.slice(0, 2).toUpperCase();
};

const seats: Record<string, Seat> = {};
const rooms: Record<string, Room> = {};

function addSeat(s: Omit<Seat, "initials"> & { initials?: string }) {
  if (!seats[s.id]) seats[s.id] = { initials: s.initials ?? seatInitials(s.name), ...s } as Seat;
  return s.id;
}

const COLUMN: Record<string, 1 | 2 | 3> = {
  div1: 1, div2: 1, div3: 2, div4: 2, div5: 2, div6: 3, div9: 3, div8: 3, div7: 3,
};
const SHORT: Record<string, string> = {
  div1: "Zone 1 · Architecture & Spec", div3: "Zone 3 · Physical Implementation",
  div4: "Zone 4 · Signoff & Manufacturing", div5: "Div 5 · Quality & Program Office",
  div6: "Div 6 · Platform Engineering", div7: "Div 7 · Customer & Business",
  div8: "Div 8 · Finance & FinOps", div9: "Div 9 · Research, Intel & Sourcing",
};

for (const d of org.divisions) {
  const phase = d.phase ?? 0;
  const zoneDiv = Boolean(d.zone);
  const teamSeats = (teams: YTeam[], roomId: string, managerId?: string) =>
    teams.map((t) => addSeat({
      id: t.lead, name: t.lead, role: t.name, kind: "lead", roomId, divisionId: d.id, teamId: t.id,
      mission: t.mission, phase: t.phase ?? phase, managerId,
    }));

  if (d.departments?.length) {
    // Division 2: a group with its director, holding one table per department/zone.
    const children: string[] = [];
    for (const dep of d.departments) {
      const head = dep.manager ? addSeat({
        id: dep.manager, name: dep.manager, role: `Manager, ${dep.name}`, kind: "manager",
        roomId: dep.id, divisionId: d.id, phase, managerId: d.director,
        mission: `Manages ${dep.name}: assigns ready work within SLA, checks every running task, unblocks or escalates`,
      }) : undefined;
      rooms[dep.id] = {
        id: dep.id, label: `Zone ${dep.zone} · ${dep.name}`, kind: "zone", divisionId: d.id, column: COLUMN[d.id],
        head, seats: [...(head ? [head] : []), ...teamSeats(dep.teams, dep.id, dep.manager)], phase,
      };
      children.push(dep.id);
    }
    const director = d.director ? addSeat({
      id: d.director, name: d.director, role: `Director, ${d.name}`, kind: "director", roomId: d.id,
      divisionId: d.id, phase, mission: `Owns ${d.name}: goals, capacity and cross-department conflicts`,
    }) : undefined;
    rooms[d.id] = {
      id: d.id, label: `Div 2 · ${d.name}`, kind: "group", divisionId: d.id, column: COLUMN[d.id],
      head: director, seats: director ? [director] : [], phase, children,
    };
    continue;
  }
  // Single-table divisions. The director sits at the head (in Platform/Finance the director
  // also leads a team: one seat).
  const head = d.director ? addSeat({
    id: d.director, name: d.director, role: `Director, ${d.name}`, kind: "director", roomId: d.id,
    divisionId: d.id, phase, mission: `Owns ${d.name}: goals, capacity and delivery`,
  }) : undefined;
  const leads = teamSeats(d.teams ?? [], d.id, d.director).filter((id) => id !== head);
  if (head && seats[head].kind === "director") {
    const ownTeam = (d.teams ?? []).find((t) => t.lead === head);
    if (ownTeam) { seats[head].teamId = ownTeam.id; seats[head].mission = ownTeam.mission ?? seats[head].mission; }
  }
  rooms[d.id] = {
    id: d.id, label: SHORT[d.id] ?? d.name, kind: zoneDiv ? "zone" : "room", divisionId: d.id,
    column: COLUMN[d.id] ?? 3, head: head ?? leads[0], seats: [...(head ? [head] : []), ...leads], phase,
  };
  if (phase > 0) rooms[d.id].label += ` (Phase ${phase}+)`;
}

rooms.humans = {
  id: "humans", label: "Human leaders · approve gates", kind: "humans", divisionId: "ceo", column: 3,
  seats: org.humans.map((h) => addSeat({
    id: `human:${h.id}`, name: h.name, initials: initials(h.name === "Goutham" ? "Goutham Rajam" : h.name),
    role: h.title, kind: "human", roomId: "humans", divisionId: "ceo", phase: 0, approves: h.approves,
    owns: h.owns, mission: `Owns: ${h.owns}. Approves: ${h.approves.join(", ")}`,
  })), phase: 0,
};

export const SEATS = seats;
export const ROOMS = rooms;
export const ROOM_ORDER: Record<1 | 2 | 3, string[]> = {
  1: ["div1", "div2"],
  2: ["div3", "div4", "div5"],
  3: ["div6", "div9", "div8", "div7", "humans"],
};
export const AGENT_IDS = Object.keys(seats);

/** Human desks that approve a gate (G1..G4). */
export const approversOf = (gate: string): string[] =>
  Object.values(seats).filter((s) => s.kind === "human" && s.approves?.includes(gate)).map((s) => s.id);

/** Division id for a team id or agent id (for feed/WS filters). */
export function divisionOf(agentOrTeam: string | null | undefined): string | undefined {
  if (!agentOrTeam) return undefined;
  const seat = seats[agentOrTeam];
  if (seat) return seat.divisionId;
  const lead = Object.values(seats).find((s) => s.teamId === agentOrTeam);
  return lead?.divisionId;
}

export const DIVISIONS = org.divisions.map((d) => ({ id: d.id, name: d.name, phase: d.phase ?? 0 }));
export const ORG = org;
