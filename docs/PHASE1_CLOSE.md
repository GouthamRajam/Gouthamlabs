# Phase 1 Close — Spec-to-GDSII on SKY130

**Date:** 2026-10-08
**Design:** PicoRV32 — 32-bit RISC-V core (RV32I)
**Process:** SkyWater SKY130 (sky130_fd_sc_hd standard cells)
**Tools:** Open-source only (Yosys, OpenROAD/OpenLane, OpenSTA, iverilog, SymbiYosys, Netgen, Magic, KLayout, Sail RISC-V)

---

## Summary

Phase 1 delivers a DRC-clean, LVS-verified, timing-signed-off GDSII of a
compliant RV32I RISC-V core on the SkyWater SKY130 open PDK, using
exclusively open-source tools. The design passes 39/39 RV32I instruction
tests against the Sail RISC-V official golden model, synthesizes to 8,374
cells, routes cleanly at 35% utilization with zero DRC/LVS/antenna
violations across all signoff checks, and meets timing at 20 MHz across
all 9 PVT corners with zero setup and hold violations. Vector-based power
(from gate-level VCD) is 2.606 mW. The RTL is hand-authored — not
agent-generated — and Phase 1 proves the spec-to-silicon flow end to end.
Known caveats are logged below; none block the Phase 1 gate.

---

## GDSII Deliverable

| Item | Value |
|------|-------|
| File | `picorv32.gds` (Magic stream-out) |
| Size | 38,524,806 bytes (37 MB) |
| SHA-256 | `2e48988f23ceca76ba2ba32b4598f744bad562dcfc97c3c29a2345a0a6f755a4` |
| KLayout GDS | `picorv32.klayout.gds` (17 MB, SHA-256 `8910174f...4175`) |
| GDSII version | 3 |
| Library name | picorv32 |
| Cell structures | 172 |
| Cell references | 42,943 |
| Polygons | 534,452 |
| File integrity | ENDLIB record present, properly terminated |

The Magic and final GDS files have identical SHA-256 hashes — they are
the same artifact. The KLayout GDS differs only in stream-out options
(denser encoding).

---

## Signoff Evidence

### DRC — PASS

| Tool | Violations |
|------|------------|
| Magic DRC | **0** |
| KLayout DRC | **0** (all 200+ SKY130 rule categories checked) |
| Routing DRC (OpenROAD) | **0** |

### LVS — PASS

| Metric | Value |
|--------|-------|
| Tool | Netgen |
| Result | **Circuits match uniquely** |
| Devices (layout) | 12,267 |
| Nets (layout) | 10,740 |
| Pin lists | Equivalent |

### Antenna — PASS

| Check | Violations |
|-------|------------|
| Post-DRT antenna (step 46) | **0** |
| Pre-DRT GRT antenna (step 39) | **0** |

Strategy: pre-DRT heuristic diode insertion (11,631 diodes) +
GRT-based iterative repair.

### STA — PASS (all 9 corners)

| Corner | Setup WNS | Hold WNS |
|--------|-----------|----------|
| nom_tt_025C_1v80 | 0 | 0 |
| nom_ff_n40C_1v95 | 0 | 0 |
| nom_ss_100C_1v60 | 0 | 0 |
| min_tt_025C_1v80 | 0 | 0 |
| min_ff_n40C_1v95 | 0 | 0 |
| min_ss_100C_1v60 | 0 | 0 |
| max_tt_025C_1v80 | 0 | 0 |
| max_ff_n40C_1v95 | 0 | 0 |
| max_ss_100C_1v60 | 0 | 0 |

Clock: 20 MHz (50 ns period). WNS = 0 means no timing violations.

### Power

| Method | Internal | Switching | Leakage | Total |
|--------|----------|-----------|---------|-------|
| VCD-annotated (gate-level) | 1.873 mW | 0.732 mW | 73.3 nW | **2.606 mW** |
| Statistical (P1.4 signoff) | 2.227 mW | 1.161 mW | 0.142 µW | **3.387 mW** |

VCD-annotated power is from OpenSTA 3.1.0 with real gate-level simulation
VCD (134 cycles, 49,934 pin activities annotated). Statistical power is
from P1.4 signoff (default activity assumptions).

### IR Drop — PASS

| Net | Worst Drop | % of VDD |
|-----|------------|----------|
| VPWR | 0.142 mV | 0.01% |
| VGND | 0.146 mV | 0.01% |

Power grid violations: 0 (VPWR and VGND).

---

## RV32I Compliance

| Level | Method | Result |
|-------|--------|--------|
| RTL | 39/39 tests vs Sail RISC-V v0.15 (official golden model) | **PASS** |
| Gate (bounded equivalence) | BMC depth 10, SymbiYosys + z3, RTL vs synthesized netlist | **No counterexample** |
| Gate (functional smoke) | iverilog on post-P&R netlist, 9 instruction checks | **PASS** |

Full RV32I compliance is proven at RTL level (39/39 MATCH against the
RISC-V International official golden model). The gate-level connection is
via bounded equivalence check (depth 10, covering 2+ full instruction
executions) plus a representative functional smoke test on the physical
netlist.

---

## Physical Summary

| Metric | Value |
|--------|-------|
| Die area | 297,307 µm² |
| Core utilization | 35% (FP_CORE_UTIL) |
| Total instances | 26,252 |
| Logic cells | ~14,621 |
| Antenna diodes | 11,631 (44.3% of instances) |
| Standard cell library | sky130_fd_sc_hd |
| Metal layers used | li1, met1, met2, met3, met4 |
| Clock frequency | 20 MHz |

---

## Milestone Chain

| Milestone | Status | Key Result |
|-----------|--------|------------|
| P1.1 | COMPLETE | RV32I compliance: 39/39 vs Sail RISC-V v0.15 |
| P1.3 | COMPLETE | Synthesis (8,374 cells) + DFT (83.1% ATPG) + bounded equivalence + STA |
| P1.4 | COMPLETE | Full P&R: 0 DRC, 0 antenna, LVS match, timing clean (9 corners) |
| P1.5 | COMPLETE | VCD power (2.606 mW), IR drop (0.01%), gate-level smoke PASS |
| P1.6 | COMPLETE | GDS verified, integrity cross-checked, Phase 1 packaged and closed |

---

## Known Caveats (Honest Record)

1. **Diode overhead (44.3%):** The heuristic diode insertion is
   conservative — it targets all nets >90 µm Manhattan length, not just
   the ~50 that would violate antenna rules. This is a Phase 1.5 efficiency
   target, not a correctness issue. The design passes all antenna checks.

2. **Bounded equivalence (not unbounded):** The RTL-to-gate equivalence
   check covers BMC depth 10 (2+ full instruction executions) but is not
   a full unbounded proof. Yosys register-file re-encoding (32×32 2D array
   → 1024 individual FFs) prevents the k-induction step from converging.
   Structural equivalence approaches (eqy, equiv_make, equiv_opt,
   equiv_induct) all failed on register-file signal matching.

3. **Hand-authored RTL:** The PicoRV32 RTL is hand-authored by Clifford
   Wolf, not agent-generated. Phase 1 proves the spec-to-silicon flow;
   Phase 1.5 Pillar A was intended to address agent-generated RTL but
   the s2s_rv32i RTL was also hand-authored (by Claude in a Code session),
   not generated by the S2S agent pipeline. See DECISIONS.md provenance
   audit (2026-10-09). A true pipeline-generated result is still needed.

4. **Gate-level smoke, not full gate compliance:** The gate-level test is
   a 9-check functional smoke test, not the full 39-test RV32I suite.
   Full compliance is proven at RTL and linked via bounded equivalence.

5. **ATPG coverage (83.1%):** Random-pattern-only ATPG. Directed ATPG
   (PODEM/D-algorithm) for higher coverage is a Phase 1.5 item.

6. **VCD power scope:** The VCD-annotated power is from a short
   representative program (134 cycles). Compute-intensive workloads would
   show higher switching power.

---

## Deliverable Set Location

All Phase 1 evidence is in the repository and P1.4 run artifacts:

| Deliverable | Location |
|-------------|----------|
| GDSII (primary) | `p1.4_pnr/pnr/runs/p1_4_r3/final/gds/picorv32.gds` |
| GDSII (KLayout) | `p1.4_pnr/pnr/runs/p1_4_r3/final/klayout_gds/picorv32.klayout.gds` |
| Post-P&R netlist | `p1.4_pnr/pnr/runs/p1_4_r3/final/nl/picorv32.nl.v` |
| SPEF parasitics | `p1.4_pnr/pnr/runs/p1_4_r3/final/spef/{nom,min,max}/` |
| SDC constraints | `p1.4_pnr/pnr/runs/p1_4_r3/final/sdc/` |
| SDF timing | `p1.4_pnr/pnr/runs/p1_4_r3/final/sdf/` |
| LEF | `p1.4_pnr/pnr/runs/p1_4_r3/final/lef/` |
| Magic DRC report | `p1.4_pnr/pnr/runs/p1_4_r3/63-magic-drc/reports/` |
| KLayout DRC report | `p1.4_pnr/pnr/runs/p1_4_r3/64-klayout-drc/reports/` |
| LVS report | `p1.4_pnr/pnr/runs/p1_4_r3/69-netgen-lvs/reports/` |
| Antenna reports | `p1.4_pnr/pnr/runs/p1_4_r3/46-openroad-checkantennas-1/reports/` |
| IR drop report | `p1.4_pnr/pnr/runs/p1_4_r3/56-openroad-irdropreport/irdrop.rpt` |
| Metrics | `p1.4_pnr/pnr/runs/p1_4_r3/final/metrics.json` |
| VCD power report | `p1.5_analyses/vcd_power_report.txt` |
| VCD power script | `p1.5_analyses/vcd_power.tcl` |
| Gate-level VCD | `p1.5_analyses/gate_sim.vcd` |
| Gate-level testbench | `p1.5_analyses/gate_compliance_tb.v` |
| Cell models | `p1.5_analyses/sky130_cells_pnr.v` |
| P1.1 milestone | `docs/milestones/P1.1.md` (in repo) |
| P1.3 milestone | `docs/milestones/P1.3.md` (in repo) |
| P1.4 milestone | `docs/milestones/P1.4.md` (in repo) |
| P1.5 milestone | `docs/milestones/P1.5.md` (in repo) |
| Decision log | `docs/DECISIONS.md` (in repo) |

---

## Trust Layer Compliance

- GDS hash recorded from the actual file, not claimed.
- DRC/LVS/antenna results read from real tool reports, not fabricated.
- All signoff checks show 0 violations — no waivers applied.
- Compliance proven at RTL with independent golden model (Sail), not our own emulator.
- Gate-level test honestly labeled as smoke test, not full compliance.
- Power reported from real VCD-annotated analysis and real statistical analysis.
- All known caveats logged — nothing hidden.
- Phase 0 constraint met: open-source tools only, open SKY130 PDK only.
- No rules weakened, no fabricated results, no overclaiming "production."

---

**PHASE 1: COMPLETE.**

A compliant RV32I core has been taken from specification to verified GDSII
on the SkyWater SKY130 open process, using exclusively open-source EDA tools.
Every signoff check passes with zero violations. The design is not
production-ready (see caveats), but Phase 1's goal — proving the
spec-to-silicon flow end to end with honest, verifiable results — is met.
