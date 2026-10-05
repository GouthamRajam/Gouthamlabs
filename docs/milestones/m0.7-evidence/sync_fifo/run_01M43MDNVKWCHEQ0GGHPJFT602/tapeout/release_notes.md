# Release Notes: sync_fifo tape-out package

## 1. What this package is
- Design: `sync_fifo`, spec version 1. A single-clock synchronous FIFO, 16 entries x 32 bits, with full, empty and almost-full flags and sticky overflow/underflow flags.
- Process: SkyWater SKY130A, library sky130_fd_sc_hd. Target clock 100 MHz (10 ns). The PDK, library and clock choices are marked DEFAULT or "needs G1 review" in the spec. The G1 record is the checklist item 1 evidence.
- Flow: open-source tools only (Phase 0). The package is a GDSII layout with netlist, constraints, signoff reports, evidence packets, `versions.lock`, `reproduce.sh` and a hash manifest (`MANIFEST.sha256`).
- Everything here is pre-silicon. No silicon was manufactured or tested. This is not a commercial foundry tape-out.

## 2. Signoff status: tape-out checklist (16 of 16 items marked done)

| # | Item | Evidence |
|---|------|----------|
| 1 | Spec approved at G1 | gate gate_01M42AVNQYD7MYFFCM47YHHNH2 |
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
| 16 | G3 approved | gate gate_01M46WTQ03T9DHDT99KPN5MTAP (approved) |

These statuses are copied from `reports/tapeout_checklist.json`. This document does not re-run or re-verify any check.

## 3. Readiness numbers and baselines

| Baseline | Meaning | Score | Weights |
|----------|---------|-------|---------|
| A | Open SKY130 shuttle requirements | **95.3%** | 97 total |
| B | Commercial production tape-out on a real foundry PDK | **64.1%** | 106 total |

Partial credit for a partial result is 0.5 of the row weight. Checks that were not run are excluded from the baseline A denominator and score 0 in baseline B.

| Check | Weight | Result | Earned A | Earned B |
|-------|--------|--------|----------|----------|
| Functional sim (RTL + gate-level) | 12 | clean | 12.0 | 12.0 |
| Coverage (line, toggle, functional) | 8 | clean | 8.0 | 8.0 |
| Formal properties + RTL/netlist equivalence | 10 | clean | 10.0 | 10.0 |
| DRC (Magic + KLayout, SKY130 decks) | 14 | clean | 14.0 | 7.0 |
| LVS (Magic extraction + Netgen) | 14 | clean | 14.0 | 7.0 |
| Antenna | 4 | clean | 4.0 | 4.0 |
| Density / fill | 4 | clean | 4.0 | 4.0 |
| Setup + hold STA, 9 corners | 12 | clean | 12.0 | 6.0 |
| Power estimate | 4 | clean | 4.0 | 2.0 |
| IR drop / EM (static) | 4 | clean | 2.0 | 2.0 |
| DFT scan + ATPG fault coverage | 5 | partial | 2.5 | 0.0 |
| Signal integrity / crosstalk | 3 | not run | n/a | 0.0 |
| Reliability (aging, ESD, latch-up) | 3 | not run | n/a | 0.0 |
| Foundry-certified signoff (Calibre-class) | 3 | not run | n/a | 0.0 |
| GDS integrity + reproducibility | 6 | clean | 6.0 | 6.0 |

Baseline B is lower because open-source decks and estimates earn half credit on DRC, LVS, STA and power under a commercial standard. The three not-run checks and DFT earn nothing there.

## 4. DFM scorecard
0 high, 3 medium, 6 low (9 items). The checklist records "zero high-severity open items" as met. The medium items are:
- DFM-003: 304 met1 line ends at near-minimum end-to-line spacing.
- DFM-001: 20 li density windows within 10% of the 0.6 maximum (peak 0.5828).
- DFM-005: 1 met2 line end at near-minimum spacing.

The low items are near-limit geometry statistics on li, met1, met2, met3, met4 and met5. Examples: li is 100% near minimum width by construction, and met1 is 47.3% near limit. All nine items are owned by Orion and remain open as suggestions. None blocks the checklist.

## 5. Known limits
- DRC and LVS used open-source Magic, KLayout and Netgen decks. Foundry-certified decks (for example Calibre) were not run and may differ.
- Timing is OpenSTA at the PDK corners (9 corners). There is no OCV/AOCV and no SI-aware timing.
- Power is estimated at 20% input activity, and the spec has no power budget. IR is static only and EM was not analyzed.
- DFT is a plan only (`dft_plan.md`). There is no scan insertion and no ATPG fault coverage number.
- Not run, out of open-flow scope: signal integrity/crosstalk, reliability (aging, ESD, latch-up), foundry-certified signoff.
- Spec points still marked DEFAULT or "needs G1 review": almost-full threshold of 12, synchronous reset, simultaneous push/pop at full and empty, sticky overflow/underflow, and first-word-fall-through reads. They were listed as open questions in the spec.

## 6. Open items
- DFM-003, DFM-001 and DFM-005 (medium) and the six low items are not fixed.
- Phase 1 items to close the gaps: foundry-certified DRC and LVS decks, OCV/AOCV and SI-aware STA, vector-based power, full IR/EM with a package model, scan insertion and ATPG.
- Signal integrity, reliability and foundry-certified signoff are marked "fix and re-run the check (this phase)" in the readiness report. No result exists for them.
