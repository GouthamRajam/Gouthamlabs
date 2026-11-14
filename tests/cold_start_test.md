# Cold-Start Acceptance Test — Pillar D Gate

**Purpose:** Verify that a fresh agent with NO conversation history, given only the repo,
can reconstruct project status and continue real work using the knowledge store.

## Setup

1. Start a fresh agent session (no prior conversation context)
2. Point it at this repository (clone or checkout)
3. Instruct it: "Read docs/START_HERE.md, then answer the following questions and
   perform the task below."

## Questions (5 checks, binary pass/fail)

### (a) Reconstruct current status

**Prompt:** "What is the current state of the project? Which phases have passed, which
are open, and what milestones within the current phase are complete?"

**Ground truth** (from PHASE_GATES.md):
- Phase 0: CLOSED (CEO decision 2026-10-07). 3 of 5 blocks clean, sync_fifo FAIL
  (antenna + timing), spi_master CONDITIONAL (clock fanout)
- Phase 1: OPEN. P1.1 (RV32I compliance 39/39) CONFIRMED. P1.3 (synthesis + DFT) COMPLETE.
  P1.4 (P&R → signoff → GDSII) is next.
- Phase 1.5: PLANNED (docs/PHASE1_5_PLAN.md). Not started (except Pillar D scaffold).
- Phase 2, Phase 3: NOT STARTED.

**Pass criterion:** Names Phase 0 as closed, Phase 1 as open with P1.1 and P1.3 done,
and identifies P1.4 or P&R as the next step.

### (b) Explain the antenna blocker

**Prompt:** "What was the antenna violation problem in Phase 0, and why did each
attempted fix fail?"

**Ground truth** (from PHASE_GATES.md + knowledge/failures/antenna_post_drt.yaml):
- sync_fifo had 2 met1 side-area antenna violations after detailed routing
- Approach 1: Diode-insertion + broad re-route → 2 → 7 violations (TritonRoute creates
  new violations while fixing old ones)
- Approach 2: Net-scoped ECO route with dont_touch → 2 → 4 violations on different nets
- Root cause: OpenLane 2.3.10 repairs antennas only on the global route; it cannot see
  the layer split the detailed route creates
- The architecturally correct fix: pre-DRT diode insertion

**Pass criterion:** Names both attempted approaches (diode+reroute AND net-scoped ECO),
states both made things worse (not better), and identifies the root cause as post-DRT
repair limitation in OpenLane.

### (c) Explain the NOP-patch and Sail proof

**Prompt:** "Why is the NOP-patch applied to the RV32I compliance tests legitimate, and
how was compliance verified independently?"

**Ground truth** (from knowledge/decisions/nop_patch_and_sail.yaml + DECISIONS.md):
- Zeros (0x00000000) are at jump targets and ARE reachable (not unreachable padding)
- 0x00000000 is a designated illegal instruction per RISC-V ISA spec
- Any correct implementation traps on it → test FAIL
- The zeros are a GAS (GNU assembler) defect in .p2align with .option push/pop nesting
- NOP-patch converts zeros to what GAS should have emitted (0x00000013 = NOP)
- Compliance verified against Sail RISC-V v0.15 (RISC-V International official model)
- Result: 39/39 MATCH, 0 mismatches
- 7 of 39 tests needed patching, 32 did not

**Pass criterion:** States zeros are at jump targets (reachable, not unreachable), GAS
defect, compliance confirmed 39/39 against Sail (the independent golden model).

### (d) Name the next gated step

**Prompt:** "What is the next step the project must complete, and what gates must it pass?"

**Ground truth** (from PHASE_GATES.md):
- Next step: P1.4 — Place & Route → signoff → GDSII for PicoRV32
- Gates: DRC clean, LVS match, antenna clean (with pre-DRT fix), timing met (OCV derated),
  equivalence maintained
- After Phase 1 closes: Phase 1.5 (hardening + autonomy proof, 5 pillars)

**Pass criterion:** Names P1.4 (or P&R/signoff/GDSII) as the next step.

### (e) Continue one real task

**Prompt:** "Using only information in the repo, describe the specific steps you would
take to begin P1.4 (place & route for PicoRV32). Name the input files, the tools, and
the key parameter decisions, referencing knowledge store entries where relevant."

**Ground truth:** The agent should reference:
- Input: designs/picorv32/synth_dft/picorv32_synth.v (or the scan-inserted version)
- Tools: OpenLane 2 / OpenROAD (available in s2s-eda Docker image)
- Key decision: pre-DRT antenna diode insertion (k001-antenna-blocker)
- Sky130 PDK constraints
- OCV derated timing requirement (k006-ocv-derated-sta)

**Pass criterion:** Produces a valid action plan (not a hallucinated tool result) that
references the antenna blocker knowledge and uses the correct input files.

## Grading

| Check | Weight | Pass criterion |
|-------|--------|----------------|
| (a)   | 1      | Phase 0 closed, Phase 1 open, P1.1+P1.3 done |
| (b)   | 1      | Both approaches named, both worsened, root cause identified |
| (c)   | 1      | Zeros reachable + GAS defect + 39/39 Sail confirmed |
| (d)   | 1      | P1.4 / P&R / GDSII named as next |
| (e)   | 1      | Valid plan referencing antenna knowledge + correct inputs |

**Pass threshold: 5/5.** Any score < 5 means the knowledge store needs improvement.

## Running the test

1. The grader is a human (or a separate agent with access to this rubric and DECISIONS.md)
2. The test subject is a fresh agent with NO prior conversation
3. Each answer is graded independently against ground truth
4. Partial credit: none. Each check is binary pass/fail.
5. The test is re-run after knowledge store updates to verify improvement.
