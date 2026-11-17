# START HERE — Bootstrap Entry Point for Fresh Agents

**Read this document FIRST in any new session.** It is a routing table, not a duplicate.

## 1. What is this project?

Read `CONTEXT.md` (root of repo). One page. Gives you the idea, the invariant, the flow,
the phases, the hard rules.

## 2. What has been done? What's next?

Read `PHASE_GATES.md` (root of repo). It lists every phase gate, its status (PASSED /
open / not started), and what happened at each. The current state of the project is
defined by which gates are checked. Only a human marks a gate.

**Source-of-truth order when documents disagree:** `PHASE_GATES.md`, then the newest dated
entry in `docs/DECISIONS.md`, then a milestone report. Milestone reports in `docs/milestones/`
are point-in-time and some were superseded (see knowledge entry **k010**). Never quote status
from one of them alone.

## 3. What decisions were made and why?

Read `docs/DECISIONS.md`. Every non-obvious decision with date, rationale, and
alternatives considered. This is the ground truth for "why was X done this way?"
Lines are long; use `grep -n` for a topic, then read only those lines.

## 4. Engineering knowledge (experiments, failures, methods)

Browse `knowledge/index.yaml` for the master index. Each entry has a topic, summary,
evidence pointers, and a lesson learned. Key entries for cold-start:

- **k012**: Phase 1.5 pillar status snapshot (what is met, partial, not met)
- **k009**: Provenance: committed s2s_rv32i and s2s_uart RTL are hand-authored, not pipeline-generated
- **k001**: Antenna violations don't converge post-detailed-route (the Phase 0 blocker)
- **k008**: The antenna fix that worked: pre-DRT heuristic diodes + lower utilization (P1.4)
- **k002**: NOP-patch legitimacy and Sail compliance proof
- **k003**: BMC equivalence is bounded (depth 10), not unbounded
- **k007**: Eight equivalence approaches that failed before BMC worked
- **k010**: Milestone reports are point-in-time; which ones are stale
- **k011**: VCD power, IR-drop bound, and why the gate-level smoke test is not compliance

Subdirectories:
- `knowledge/failures/` — root-cause analyses of significant failures
- `knowledge/decisions/` — structured decision records
- `knowledge/methods/` — known-good recipes (synthesis, P&R, verification)

## 5. Design artifacts

- `designs/picorv32/` — hand-authored RISC-V core (Phase 1 deliverable; clean GDSII)
- `designs/s2s_rv32i/` — RV32I core, hand-authored in an AI coding session (Pillar A; GDSII)
- `designs/uart/rtl/` — hand-authored 3-module UART (Pillar B; GDSII)
- `designs/uart/pipeline_rtl/` — the UART the S2S pipeline generated autonomously (routed DEF; `pnr/stream_out.py` makes a GDS; see k013 for DRC status and open defects)
- `var/artifacts/` — run outputs from the pipeline (content-addressed)
- `docs/trajectories/` — records of pipeline runs; a design with no trajectory was not pipeline-generated
- `docs/milestones/` — milestone reports (M0.1 to M0.7, P1.3 to P1.5, A2)
- `docs/PHASE1_CLOSE.md` — Phase 1 deliverables and known caveats

## 6. The spec (reference only)

`docs/MASTER_SPEC.md` (~28k words). Load only the section a task needs, never all of it.
Part 23.4's P1.x milestone table is NOT the numbering used in practice; see `PHASE_GATES.md`.

## 7. Phase 1.5 plan

`docs/PHASE1_5_PLAN.md` — the hardening + autonomy proof required before Phase 2.
Includes this document's cold-start acceptance test (Pillar D gate); the test itself is
`tests/cold_start_test.md`.

## 8. Environment limits to know

- EDA tools run only in the `s2s-eda` Docker image (`docker build -t s2s-eda eda/`).
- The cloud container's Docker daemon cannot start (no `/var/run/docker.sock`; containerd timeout).
  There, the pinned Magic, Netgen and OpenROAD are unavailable. KLayout (pip/apt, not the pinned
  version) can stream out a GDS and run the PDK DRC deck, but Magic DRC and Netgen LVS cannot run.
  Do not report a check as passed unless the tool actually ran; say which were not run, and label
  results from non-pinned tools as such.
