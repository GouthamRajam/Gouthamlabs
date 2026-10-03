// Demo mode (Part 12.3): a built-in scripted simulation for pitches, used when no backend is
// connected. Every event is marked detail.simulated = true, the run id starts with "sim_",
// and the UI labels the whole page "Simulation" (Part 12.4 #5). Nothing here is real output.
import type { EventType, S2SEvent } from "./types";

type Step = [delayMs: number, ev: S2SEvent];

// Agents that keep working in the background (regression farm, platform, research, finance),
// so 20+ seats animate at once (Part 12.4 #3).
const BACKGROUND = ["Rex", "Theo", "Mira", "Proto", "Euclid", "Cora", "Dex", "Myra", "Lumen", "Sentinel",
  "Sage", "Proof", "Bolt", "Pixel", "Hook", "Kube", "Quill", "Meter", "Vista", "Lyra", "Scout", "Fermi",
  "Patch", "Scout-Intel", "Grant", "Pipe", "Atlas"];

const STAGES: { stage: string; agent: string; manager: string; tool: string; title: string; file: string; gate?: string }[] = [
  { stage: "spec", agent: "Iris", manager: "Juno", tool: "schema_validator", title: "Write the uart specification", file: "spec/uart.yaml" },
  { stage: "architecture", agent: "Kepler", manager: "Juno", tool: "ppa_estimator", title: "Define the uart micro-architecture", file: "arch/uart_arch.md", gate: "G1" },
  { stage: "rtl", agent: "Ada", manager: "Reid", tool: "verilator_lint", title: "Write lint-clean uart RTL", file: "rtl/uart_tx.sv" },
  { stage: "test_build", agent: "Vera", manager: "Nadia", tool: "cocotb_sim", title: "Build the uart test environment", file: "tb/test_uart.py" },
  { stage: "verification", agent: "Rex", manager: "Rhea", tool: "cocotb_sim", title: "Close uart verification", file: "reports/regression.json", gate: "G2" },
  { stage: "synthesis", agent: "Sienna", manager: "Mason", tool: "yosys_synth", title: "Synthesize uart", file: "netlist/uart.v" },
  { stage: "dft", agent: "Tess", manager: "Mason", tool: "dft_insert", title: "Insert scan chains", file: "netlist/uart_scan.v" },
  { stage: "floorplan", agent: "Grid", manager: "Mason", tool: "openroad", title: "Floorplan and power grid", file: "pnr/uart.def" },
  { stage: "place_route", agent: "Orion", manager: "Mason", tool: "openlane_flow", title: "Place and route uart", file: "pnr/uart_routed.def" },
  { stage: "signoff", agent: "Chronos", manager: "Sloane", tool: "opensta", title: "All-corner timing signoff", file: "signoff/sta.rpt", gate: "G3" },
  { stage: "gdsii", agent: "Gideon", manager: "Sloane", tool: "klayout_drc", title: "Assemble the GDSII package", file: "gds/uart.gds", gate: "G4" },
];

export function demoScript(loop: number): Step[] {
  const runId = `sim_run_${String(loop + 1).padStart(4, "0")}`;
  const steps: Step[] = [];
  let n = 0;
  const ev = (delay: number, type: EventType, agent: string | null, summary: string,
              extra: Partial<S2SEvent> = {}, detail: Record<string, unknown> = {}) => {
    n += 1;
    steps.push([delay, {
      id: `sim_${loop}_${String(n).padStart(4, "0")}`, ts: new Date().toISOString(), run_id: runId,
      design_id: "sim_uart", team: null, agent_id: agent, agent_name: agent, stage: null, task_id: null,
      type, status: null, summary, detail: { ...detail, simulated: true }, to_agent_id: null, progress: null, ...extra,
    }]);
  };
  // `ts` is re-stamped when each event is applied (sources.startDemo)

  for (const a of BACKGROUND) ev(40, "agent.status", a, `${a} is working`, { status: "working" });
  ev(300, "research.brief", "Lyra", "Lyra: brief — two open UART cores with permissive licenses; no IP conflicts",
    {}, { topic: "UART prior art" });

  STAGES.forEach((st, i) => {
    const base = { stage: st.stage, task_id: `sim_task_${i}` };
    ev(500, "stage.changed", "Atlas", `Run entered stage ${st.stage}`, { ...base, task_id: null }, { to: st.stage });
    ev(300, "task.started", st.agent, `${st.agent} started: ${st.title}`, { ...base, status: "working" });
    ev(350, "agent.status", st.agent, `${st.agent} is thinking`, { ...base, status: "thinking" });
    ev(500, "plan", st.agent, `${st.agent} plan: read inputs, ${st.title.toLowerCase()}, run checks, report`, base);
    ev(450, "agent.status", st.agent, `${st.agent} is working`, { ...base, status: "working" });
    ev(250, "tool_call", st.agent, `${st.agent} runs ${st.tool}`, base, { tool: st.tool });
    ev(700, "task.heartbeat", st.agent, `${st.agent}: 40%`, { ...base, progress: 0.4 },
      { evidence_signal: `${st.tool} running` });
    ev(500, "tool_result", st.agent, `${st.tool}: 0 errors`, base, { tool: st.tool, metrics: { errors: 0 } });
    ev(300, "artifact.created", st.agent, `${st.agent} wrote ${st.file}`, base, { path: st.file });

    if (st.stage === "spec") ev(400, "handoff", "Iris", "Iris → Kepler: spec v1 ready for architecture", { ...base, to_agent_id: "Kepler" });
    if (st.stage === "rtl") {
      ev(500, "check.failed", "Ada", "lint: 1 width mismatch (rtl/uart_tx.sv:42)", base, { tool: "verilator_lint" });
      ev(600, "check.passed", "Ada", "lint: clean after fix", base, { tool: "verilator_lint" });
      ev(500, "finding", "Sentinel", "Sentinel: parity bit not covered by any REQ trace", { ...base, to_agent_id: "Ada" },
        { severity: "minor" });
      ev(500, "handoff", "Ada", "Ada → Vera: RTL interface notes", { ...base, to_agent_id: "Vera" });
    } else if (st.stage === "verification") {
      for (let k = 1; k <= 3; k++) ev(500, "check.failed", "Rex", `regression attempt ${k}: 41/42 pass (test_parity_odd)`, base, { tool: "cocotb_sim" });
      ev(400, "escalation", "Rex", "regression failed 3 times in a row; escalated to Hale", { ...base, to_agent_id: "Hale" },
        { rule: "same failure 3 times" });
      ev(500, "handoff", "Dex", "Dex → Ada: bug report — parity inverted on odd setting", { ...base, to_agent_id: "Ada" });
      ev(400, "budget.warning", "Rex", "Rex: tool runs at 84% of task budget", base, { budget: "tool_runs", pct: 84 });
      ev(400, "task.stalled", "Cora", "Cora: no progress for 15 min; flagged to Rhea", { ...base, to_agent_id: "Rhea", status: "blocked" });
      ev(900, "task.heartbeat", "Cora", "Cora: coverage 97%", { ...base, progress: 0.9 }, { evidence_signal: "line coverage 97%" });
      ev(500, "check.passed", "Rex", "regression: 42/42 pass", base, { tool: "cocotb_sim" });
    } else {
      ev(400, "check.passed", st.agent, `${st.stage} checks passed`, base, { tool: st.tool });
    }
    ev(300, "manager.checkin", st.manager, `${st.manager} checked ${st.agent}: 70% (${st.tool} ran)`, { ...base, to_agent_id: st.agent });
    ev(500, "task.heartbeat", st.agent, `${st.agent}: 100%`, { ...base, progress: 1 }, { evidence_signal: "checks passed" });
    ev(300, "task.completed", st.agent, `${st.agent} completed: ${st.title}`, { ...base, progress: 1 });
    ev(200, "agent.status", st.agent, `${st.agent} is idle`, { ...base, status: "idle" });
    if (st.stage === "place_route") {
      ev(400, "budget.alert", "Penny", "Run spend $60.00 reached 80% of its $75 budget", {}, { spent_usd: 60, limit_usd: 75, pct: 80 });
    }
    if (st.gate) {
      ev(400, "gate.requested", "Atlas", `${st.gate} requested after ${st.stage}`, base, { gate: st.gate });
      ev(1600, "gate.decided", "Atlas", `${st.gate} approved (simulated reviewer)`, base, { gate: st.gate, decision: "approve" });
    }
  });
  ev(600, "stage.changed", "Atlas", "Run complete: GDSII package assembled (simulation)", {}, { to: "done" });
  return steps;
}
