# UART Release Notes (tapeout package)

## 1. What this package is
- Design: `uart` v1 - UART transmitter and receiver, 8N1 with configurable parity (none/even/odd), 16-bit baud divisor, 16x oversampling receive, framing and parity error flags (spec/spec.yaml).
- Target: SkyWater SKY130 (`sky130A`), library `sky130_fd_sc_hd`, single clock `clk` at 50 MHz, synchronous active-low reset `rst_n`.
- The PDK and library choice is marked DEFAULT in the spec ("needs G1 review"); the checklist records G1 as approved (item 1).
- This is a Phase 0 package: open-source tools and the open SKY130 PDK only. No silicon was manufactured or tested; all results are pre-silicon.

## 2. Signoff status: tape-out checklist (16 of 16 items marked done)

| # | Item | Evidence recorded |
|---|------|-------------------|
| 1 | Spec approved at G1 | gate gate_01M426W2J15PW16EQ7RXDR3TBQ |
| 2 | RTL frozen at G2; no changes since | checks rtl_frozen_at_g2, constraints_not_loosened |
| 3 | Regression 100% passing on frozen RTL | M0.6 check regression_100pct |
| 4 | Equivalence RTL vs final netlist proven | check eqy_rtl_vs_final |
| 5 | Setup and hold met at all corners | check sta_all_corners (9 corners) |
| 6 | Zero DRC (Magic and KLayout) on final GDS | checks drc_magic_final_gds, drc_klayout_final_gds, package_drc_* |
| 7 | LVS clean on final GDS | checks lvs_final_gds, package_lvs |
| 8 | Antenna clean | check antenna_final |
| 9 | Density rules met | check density_rules |
| 10 | DFM scorecard: zero high-severity open items | check dfm_no_high_severity |
| 11 | Power and IR within limits | checks power_estimated, ir_drop_within_limit |
| 12 | Pin list matches spec | check pins_match_spec |
| 13 | All Sentinel findings closed or human-overruled | all Sentinel reviews passed |
| 14 | reproduce.sh re-runs cleanly in a fresh container | check reproduce_clean_container |
| 15 | versions.lock and hashes recorded | tapeout/versions.lock, MANIFEST.sha256 |
| 16 | G3 approved | gate gate_01M47Z5CHDMPRWZ304M8D6CQMB (approved) |

This document reports the checklist as recorded in `reports/tapeout_checklist.json`; it does not re-run or independently confirm any check.

## 3. Readiness numbers and baselines
Source: `reports/tapeout_readiness.json`. Two baselines are shown; neither is a foundry certification.

| Baseline | Meaning | Score |
|----------|---------|-------|
| A | Open SKY130 shuttle requirements (weights total 97) | **95.3%** |
| B | Commercial production tape-out on a real foundry PDK (weights total 106) | **64.1%** |

Partial credit factor: 0.5 (applies to the DFT row only).

| Check | Weight | Result | Earned A | Earned B | Note |
|-------|-------:|--------|---------:|---------:|------|
| Functional sim (RTL + gate-level) | 12 | clean | 12.0 | 12.0 | |
| Coverage | 8 | clean | 8.0 | 8.0 | |
| Formal properties + RTL/netlist equivalence | 10 | clean | 10.0 | 10.0 | |
| DRC (Magic + KLayout, open decks) | 14 | clean | 14.0 | 7.0 | |
| LVS (Magic + Netgen) | 14 | clean | 14.0 | 7.0 | |
| Antenna | 4 | clean | 4.0 | 4.0 | |
| Density / fill | 4 | clean | 4.0 | 4.0 | |
| Setup + hold STA, 9 corners (OpenSTA) | 12 | clean | 12.0 | 6.0 | no OCV/AOCV, no SI-aware timing |
| Power estimate | 4 | clean | 4.0 | 2.0 | 20% input activity; no power budget in spec |
| IR drop / EM (static) | 4 | clean | 2.0 | 2.0 | static IR only; EM not analyzed |
| DFT scan + ATPG | 5 | partial | 2.5 | 0.0 | plan only in Phase 0 |
| Signal integrity / crosstalk | 3 | not run | excluded | 0.0 | out of open-flow scope |
| Reliability (aging, ESD, latch-up) | 3 | not run | excluded | 0.0 | out of open-flow scope |
| Foundry-certified signoff | 3 | not run | excluded | 0.0 | no foundry-certified decks |
| GDS integrity + reproducibility | 6 | clean | 6.0 | 6.0 | |

Baseline A excludes the three "not run" rows from its denominator (97); Baseline B counts them at zero (106). The gap between A and B comes mostly from open-source decks scoring half credit under B for DRC, LVS, STA and power, from the DFT plan-only status, and from the three checks not run.

## 4. DFM scorecard
High 0, medium 2, low 5 (`reports/dfm_scorecard.json`). Nothing here is a confirmed defect.
- DFM-003 (medium): met1, 164 line ends at near-minimum end-to-line spacing.
- DFM-001 (medium): li, 20 windows within 10% of the 0.6 max density (0.5999); li global density is 0.427.
- DFM-004 (low): met1, 52.9% of edge length within 5% of minimum width/spacing.
- DFM-002 (low): li, 100% near-limit; li is drawn at minimum width by construction, so this is expected.
- DFM-005 (low): met2, 81.4% near-limit width edges, zero near-limit spacing edges.
- DFM-006 (low): met3, 66.7%, based on only 1092 edges.
- DFM-007 (low): met4, 21.8%, based on only 44 edges.

## 5. Known limits
- DRC and LVS used open-source Magic, KLayout and Netgen decks. A foundry's certified decks (e.g. Calibre) were not run and may differ.
- Timing: OpenSTA over 9 PDK corners; no OCV/AOCV and no SI-aware timing.
- Power and IR were estimated at 20% switching activity; IR is static only and EM was not analyzed.
- DFT is a plan only; there is no scan insertion and no ATPG fault coverage number.
- Not assessed: signal integrity/crosstalk, aging/ESD/latch-up reliability, foundry-certified signoff.
- Spec note: the 50 MHz clock and the PDK/library choice are marked as defaults needing G1 review. `overrun_err` is a constant 0 output kept for future extension (REQ-022).

## 6. Open items
- Each gap above closes with a Phase 1 step: certified DRC/LVS decks, OCV/AOCV and SI-aware STA, vector-based power, full IR/EM, scan + ATPG (commercial tools). Signal integrity, reliability and foundry signoff are listed as "fix and re-run the check (this phase)" in the readiness gaps.
- Spec open questions: whether a register bus (APB/AXI/Wishbone) is required instead of plain ports; whether a frame with a framing error should still assert `rx_valid` (spec assumes yes, with `frame_err=1`).
- DFM-001 and DFM-003 (medium) are open suggestions to the layout owner (spread routing; extend line ends).
- Arithmetic note: summing the per-row earned values gives 92.5/97 (95.36%) for A and 68.0/106 (64.15%) for B; the reported 95.3% and 64.1% appear truncated rather than rounded. The reported figures are used above unchanged.
