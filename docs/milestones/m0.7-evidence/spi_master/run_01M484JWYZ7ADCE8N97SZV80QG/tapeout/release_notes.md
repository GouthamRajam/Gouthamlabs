# spi_master Release Notes (Phase 0, open SKY130)

## 1. What this package is

Tape-out package for `spi_master` (spec version 2): an SPI master, modes 0-3, 8/16-bit MSB-first transfers, programmable SCK divider (N = max(clk_div,4), so f_sck = 50/(2N) MHz, at most 6.25 MHz), automatic or manual chip select, and a transfer-complete interrupt.

- PDK / library: sky130A, sky130_fd_sc_hd (a DEFAULT choice in the spec, flagged "needs G1 review"; the checklist records G1 as approved).
- Clock: single domain `clk`, 50 MHz target (20 ns). `miso` is the only asynchronous input (2-flop synchronizer).
- This is a pre-silicon, open-flow (Phase 0) result. No silicon was manufactured or tested.

## 2. Signoff status: tape-out checklist (16 of 16 items marked done)

Status below is as recorded in `reports/tapeout_checklist.json`; the evidence column names the check or record it points to.

| # | Item | Done | Evidence |
|---|------|------|----------|
| 1 | Spec approved at G1 | yes | gate gate_01M43CJMXHCYT6W84TZCSA35Y1 |
| 2 | RTL frozen at G2; no changes since | yes | checks rtl_frozen_at_g2, constraints_not_loosened |
| 3 | Regression 100% passing on frozen RTL | yes | M0.6 check regression_100pct |
| 4 | Equivalence RTL vs final netlist proven | yes | check eqy_rtl_vs_final |
| 5 | Setup and hold met at all corners | yes | check sta_all_corners (9 corners) |
| 6 | Zero DRC (Magic and KLayout) on final GDS | yes | checks drc_magic_final_gds, drc_klayout_final_gds, package_drc_* |
| 7 | LVS clean on final GDS | yes | checks lvs_final_gds, package_lvs |
| 8 | Antenna clean | yes | check antenna_final |
| 9 | Density rules met | yes | check density_rules |
| 10 | DFM scorecard: zero high-severity open items | yes | check dfm_no_high_severity |
| 11 | Power and IR within limits | yes | checks power_estimated, ir_drop_within_limit |
| 12 | Pin list matches spec | yes | check pins_match_spec |
| 13 | All Sentinel findings closed or human-overruled | yes | all Sentinel reviews passed |
| 14 | reproduce.sh re-runs cleanly in a fresh container | yes | check reproduce_clean_container |
| 15 | versions.lock and hashes recorded | yes | tapeout/versions.lock, MANIFEST.sha256 |
| 16 | G3 approved | yes | gate gate_01M48RVBQACX41SHEYXGWPKCZQ (approved) |

## 3. Tape-out readiness numbers, with both baselines

Two scores are reported because "ready" depends on the target. Both come from `reports/tapeout_readiness.json`.

| Baseline | Meaning | Score | Weight base |
|----------|---------|-------|-------------|
| A | Open SKY130 shuttle requirements | **95.3%** | 97 |
| B | Commercial production tape-out on a real foundry PDK | **64.1%** | 106 |

Baseline A leaves out three checks (signal integrity, reliability, foundry-certified signoff) as not applicable, so its weight base is 97 instead of 106. Baseline B counts them as zero. Partial credit for a partial check is 0.5. Scores are shown to one decimal as reported in the data file (summing the per-check rows gives 92.5/97 for A and 68/106 for B).

| Check | Weight | Result | Earned A | Earned B |
|-------|-------:|--------|---------:|---------:|
| Functional sim (RTL + gate-level) | 12 | clean | 12.0 | 12.0 |
| Coverage (line, toggle, functional) | 8 | clean | 8.0 | 8.0 |
| Formal properties + RTL/netlist equivalence | 10 | clean | 10.0 | 10.0 |
| DRC (Magic + KLayout, SKY130 decks) | 14 | clean | 14.0 | 7.0 |
| LVS (Magic extraction + Netgen) | 14 | clean | 14.0 | 7.0 |
| Antenna | 4 | clean | 4.0 | 4.0 |
| Density / fill | 4 | clean | 4.0 | 4.0 |
| Setup + hold STA, 9 PDK corners | 12 | clean | 12.0 | 6.0 |
| Power estimate | 4 | clean | 4.0 | 2.0 |
| IR drop / EM (static) | 4 | clean | 2.0 | 2.0 |
| DFT scan + ATPG fault coverage | 5 | partial | 2.5 | 0.0 |
| Signal integrity / crosstalk | 3 | not run | n/a | 0.0 |
| Reliability (aging, ESD, latch-up) | 3 | not run | n/a | 0.0 |
| Foundry-certified signoff (Calibre-class) | 3 | not run | n/a | 0.0 |
| GDS integrity + reproducibility | 6 | clean | 6.0 | 6.0 |

Why B is lower: DRC, LVS, STA, and power are earned at half weight under B because only open-source decks and tools were used, not foundry-certified or commercial ones. Those gaps close in Phase 1 with commercial tools (see section 5).

## 4. DFM scorecard

0 high, 2 medium, 5 low (`reports/dfm_scorecard.json`). Checklist item 10 (zero high-severity items) is consistent with this.

| ID | Severity | Finding |
|----|----------|---------|
| DFM-003 | medium | met1: 103 line ends at near-minimum end-to-line spacing (litho pull-back could open or bridge them) |
| DFM-001 | medium | li: 20 windows within 10% of the 0.6 max density (worst window 0.583) |
| DFM-004 | low | met1: 53.6% of edge length within 5% of min width/spacing |
| DFM-002 | low | li: 100.0% of edge length near min width (inherent to min-width li routing); only 582 near min space |
| DFM-005 | low | met2: 81.2% near limit; no near-min-space edges, max density 0.151 |
| DFM-006 | low | met3: 59.7% near limit, on 107 shapes, very low density |
| DFM-007 | low | met4: 24.6% near limit, on 6 shapes |

Suggested fixes in the scorecard (owner Orion): extend spacing or add end extensions at the met1 line ends, spread routing in the dense li windows, and use non-default wider/spaced rules on non-critical nets. These are not applied in this package.

## 5. Known limits

- Open-source decks only: DRC/LVS used Magic, KLayout, and Netgen decks. Foundry-certified decks (Calibre-class) were not run and may differ.
- Timing: OpenSTA at 9 PDK corners. No OCV/AOCV and no SI-aware timing.
- Power/IR: power estimated at 20% input activity (no power budget in the spec); IR is static only and EM was not analyzed.
- DFT: plan only (`dft_plan.md`); no scan insertion and no ATPG fault coverage number.
- Not assessed (out of open-flow scope): signal integrity/crosstalk, aging/ESD/latch-up reliability, foundry-certified signoff.
- Functional scope (from the spec): max SCK 6.25 MHz; single chip select; parallel control port, no register bus; no FIFOs or queued transfers; no interrupt masking.
- Several spec values are placeholders marked "DEFAULT - needs G1 review": PDK/library choice, clk_div<4 clamping (REQ-006), CS-high timing (REQ-009), IO delays 10 ns input / 5 ns output (REQ-022), and the 20,000 um2 area cap (REQ-023).

## 6. Open items

1. Spec open questions remain unanswered in `spec/spec.yaml`: whether 6.25 MHz max SCK is acceptable (25 MHz would need a different MISO capture scheme), whether a register bus (APB/Wishbone) is needed, and whether one chip select is enough.
2. Phase 1 gaps (from the readiness data): foundry-certified DRC and LVS decks; OCV/AOCV and SI-aware STA; vector-based power with silicon-correlated models; full static/dynamic IR and EM with a package model; scan insertion and ATPG.
3. Signal integrity, reliability, and foundry-certified signoff are listed as "not run"; the readiness data records "fix and re-run the check (this phase)" as the closing action, though its notes also describe them as out of open-flow scope.
4. DFM medium items DFM-003 and DFM-001 are open and unfixed.

## 7. Basis of these notes

Every statement above comes from `spec/spec.yaml`, `reports/tapeout_checklist.json`, `reports/tapeout_readiness.json`, and `reports/dfm_scorecard.json`. No tool was run to write this document; pass/fail states are as recorded in those files. File hashes are in `MANIFEST.sha256` and `tapeout/versions.lock`.
