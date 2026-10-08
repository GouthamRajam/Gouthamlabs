# START HERE — Bootstrap Entry Point for Fresh Agents

**Read this document FIRST in any new session.** It is a routing table, not a duplicate.

## 1. What is this project?

Read `CONTEXT.md` (root of repo). One page. Gives you the idea, the invariant, the flow,
the phases, the hard rules.

## 2. What has been done? What's next?

Read `PHASE_GATES.md` (root of repo). It lists every phase gate, its status (PASSED /
open / not started), and what happened at each. The current state of the project is
defined by which gates are checked.

## 3. What decisions were made and why?

Read `docs/DECISIONS.md`. Every non-obvious decision with date, rationale, and
alternatives considered. This is the ground truth for "why was X done this way?"

## 4. Engineering knowledge (experiments, failures, methods)

Browse `knowledge/index.yaml` for the master index. Each entry has a topic, summary,
evidence pointers, and a lesson learned. Key entries for cold-start:

- **k001**: Antenna violations don't converge post-detailed-route (the Phase 0 blocker)
- **k002**: NOP-patch legitimacy and Sail compliance proof
- **k003**: BMC equivalence is bounded (depth 10), not unbounded
- **k007**: Eight equivalence approaches that failed before BMC worked

Subdirectories:
- `knowledge/failures/` — root-cause analyses of significant failures
- `knowledge/decisions/` — structured decision records
- `knowledge/methods/` — known-good recipes (synthesis, P&R, verification)

## 5. Design artifacts

- `designs/picorv32/` — the RISC-V core (RTL + synthesis/DFT artifacts)
- `var/artifacts/` — run outputs from Phase 0 (5 small blocks)
- `docs/milestones/` — milestone reports (M0.1 through P1.3)

## 6. The spec (reference only)

`docs/MASTER_SPEC.md` (~28k words). Load only the section a task needs, never all of it.

## 7. Phase 1.5 plan

`docs/PHASE1_5_PLAN.md` — the hardening + autonomy proof required before Phase 2.
Includes this document's cold-start acceptance test (Pillar D gate).
