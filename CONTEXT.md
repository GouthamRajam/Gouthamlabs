# S2S — CONTEXT (the seed). Read this first, every session. ~1 page.

This is the whole idea in one page. The full spec (docs/MASTER_SPEC.md, ~28k words) is a
REFERENCE, not something to load all at once. Load only the one section a task needs.

## What S2S is (one sentence)
An AI design team that takes a written chip spec to a tape-out-ready GDSII layout,
proves every step with real EDA tools, and lets human experts approve at 4 gates.

## The one invariant that makes it trustworthy (this is the point)
**Real tools decide pass/fail. The AI never does.**
An agent may be wrong. It cannot get a wrong thing past a real tool. A stage advances
only when a deterministic tool (simulator, formal checker, DRC, LVS, STA, equivalence)
is run and passes, and the result is recorded so anyone can re-run it. This is the
"Trust Layer". It is the direct answer to "AI hallucinates": hallucination can't pass.

## The flow (10 stages, grouped into zones)
Z1 Spec+Arch → Z2A RTL → Z2B build tests → Z2C close verification → Z3 synth/floorplan/
place&route → Z4 signoff/GDSII. Verification (Z2B+Z2C) is the biggest effort (~35%).
2A and 2B run in parallel from the same spec; tests are written WITHOUT reading the RTL,
so design and tests can't share the same mistake.

## Humans
4 gates: G1 spec, G2 RTL freeze, G3 signoff, G4 tape-out. Phase 0 auto-approves gates
(no money, no fab). A human is required only to spend money, change a frozen spec, or
send a design to a real foundry.

## Phases
- Phase 0 (now): 5 small DIGITAL blocks (counter8, uart, sync_fifo, alu8, spi_master),
  on the free SKY130 process with free open-source tools. Goal: each reaches a clean
  GDSII with no human edits. This proves the machine works. Not products.
- Phase 1: a small RISC-V core → clean GDS → passes RISC-V compliance tests → open
  shuttle (real silicon). First "it's real" proof.
- Phase 2+: customer chips on commercial nodes (customer brings their tools/PDK), then
  up the node ladder toward leading edge. Each node unlocked only after real silicon at
  the previous one.

## What it's built from (Phase 0, all free)
OpenLane 2, Yosys, OpenROAD, OpenSTA, Verilator, Icarus, cocotb, SymbiYosys, eqy, Magic,
KLayout, Netgen; SkyWater SKY130 PDK. Agents design the chip from the spec using these
standard cells and tools — they don't reinvent transistors.

## The differentiator vs ChipAgents / Cognichip
Full spec-to-GDSII (not just front-end), fab/DFM/yield knowledge built in, tool-neutral,
on-prem, and every result reproducible with evidence packets.

## Hard rules for anyone (human or AI) building this
1. Never fake a tool result. A check passes only when the real tool ran and passed.
2. Never weaken a test, loosen a constraint, or add a waiver to make something pass.
3. Build ONE milestone at a time. Acceptance tests (real runs) define "done".
4. Change only what the task needs.
5. If unsure, stop and ask. Don't guess and build on the guess.

## Phase gates & the two numbers that decide everything (see PHASE_GATES.md, Part 26)
Build Phases 0-2 only (prove the AI on small chips + a RISC-V core). Do NOT build Phase 3
(commercial tools, advanced nodes) until a human marks the gate PASSED in PHASE_GATES.md.
Track from the first real run: cost-per-design (must beat offshore) and human-touch-per-
design (must fall). Blast-radius rule: never tape out expensive silicon until a cheap
shuttle chip works first. PDK rules stay inside the tool, never in a prompt.

## Honest limits (state these, never hide them)
- Pre-silicon testing catches most bugs, not all. First silicon is the final proof.
- Agent "20 years experience" personas are prompting devices, not real skill. Quality
  comes from the tools, the checks, and human review — not from the model's confidence.
- Phase 0 open-source sign-off ≈ an open shuttle bar, NOT a commercial-node bar.
