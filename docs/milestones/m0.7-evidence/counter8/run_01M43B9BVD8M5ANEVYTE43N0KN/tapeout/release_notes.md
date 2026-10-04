# counter8: Release Notes

## 1. What this package is

- **Design:** `counter8`, spec version 1. An 8-bit up/down counter with synchronous active-low reset (`rst_n`), `enable`, `load` and an 8-bit `load_data`. It has one registered 8-bit output, `count`, whose reset value is `8'h00`.
- **Technology:** SkyWater SKY130 (`sky130A`, open PDK) with the `sky130_fd_sc_hd` standard-cell library. The PDK release is not pinned (see Open items).
- **Clock target:** one clock, `clk`, at 100 MHz (10 ns period).
- **Scope:** 13 requirements, REQ-001 to REQ-013. Out of scope: flags, saturating mode, asynchronous reset, multiple clocks or synchronizers, step sizes other than 1, low-power modes, scan/DFT insertion, and power or area targets.
- **Package contents:** final GDS, netlist, constraints, signoff reports, evidence packets, `tapeout/versions.lock`, `MANIFEST.sha256` (SHA-256 of every file) and `reproduce.sh`. Use the manifest for exact file hashes.
- **Nature of results:** pre-silicon only. No physical silicon was made or tested.

## 2. Signoff status: tape-out checklist

The checklist (`reports/tapeout_checklist.json`) records **16 of 16 items done**. Each item names its evidence, listed below as recorded. These are references to the runtime's checks, not tool output copied into these notes.

| # | Item | Done | Evidence |
|---|------|------|----------|
| 1 | Spec approved at G1 | yes | gate `gate_01M425E4G39JDJ05SQHFFT0H18` |
| 2 | RTL frozen at G2; no changes since | yes | checks `rtl_frozen_at_g2`, `constraints_not_loosened` |
| 3 | Regression 100% passing on frozen RTL | yes | M0.6 check `regression_100pct` |
| 4 | Equivalence RTL vs final netlist proven | yes | check `eqy_rtl_vs_final` |
| 5 | Setup and hold met at all corners | yes | check `sta_all_corners` (9 corners) |
| 6 | Zero DRC (Magic and KLayout) on final GDS | yes | checks `drc_magic_final_gds`, `drc_klayout_final_gds`, `package_drc_*` |
| 7 | LVS clean on final GDS | yes | checks `lvs_final_gds`, `package_lvs` |
| 8 | Antenna clean | yes | check `antenna_final` |
| 9 | Density rules met | yes | check `density_rules` |
| 10 | DFM scorecard: zero high-severity open items | yes | check `dfm_no_high_severity` |
| 11 | Power and IR within limits | yes | checks `power_estimated`, `ir_drop_within_limit` |
| 12 | Pin list matches spec | yes | check `pins_match_spec` |
| 13 | All Sentinel findings closed or human-overruled | yes | all Sentinel reviews passed |
| 14 | reproduce.sh re-runs cleanly in a fresh container | yes | check `reproduce_clean_container` |
| 15 | versions.lock and hashes recorded | yes | `tapeout/versions.lock`, `MANIFEST.sha256` |
| 16 | G3 approved | yes | gate `gate_01M43M71B7G9VHFEG9XE6TBMM5` (approved) |

## 3. Readiness numbers and baselines

The same evidence is scored against two baselines (`reports/tapeout_readiness.json`). Partial credit is 0.5.

| Baseline | Meaning | Score |
|----------|---------|-------|
| **A** | Open SKY130 shuttle requirements | **95.3%** (92.5 of 97 weight points; the 3 'not run' rows are excluded) |
| **B** | Commercial production tape-out on a real foundry PDK | **64.1%** (68 of 106 weight points; 'not run' rows count as 0) |

The two numbers answer different questions. 95.3% measures readiness for an open shuttle. 64.1% measures how far this open-tool flow is from a commercial production signoff. Do not read 95.3% as commercial readiness.

| Check | Weight | Result | Tool | Earned A | Earned B | Note |
|-------|--------|--------|------|----------|----------|------|
| Functional sim (RTL + gate-level) | 12 | clean | cocotb/Verilator/Icarus | 12 | 12 | |
| Coverage (line, toggle, functional) | 8 | clean | Verilator coverage + waveform bins | 8 | 8 | |
| Formal properties + RTL/netlist equivalence | 10 | clean | SymbiYosys, eqy | 10 | 10 | |
| DRC | 14 | clean | Magic + KLayout (SKY130 decks) | 14 | 7 | open decks, not foundry-certified |
| LVS | 14 | clean | Magic extraction + Netgen | 14 | 7 | open decks, not foundry-certified |
| Antenna | 4 | clean | OpenROAD check_antennas | 4 | 4 | |
| Density / fill | 4 | clean | KLayout PDK density deck | 4 | 4 | |
| Setup + hold STA, all PDK corners | 12 | clean | OpenSTA (9 corners) | 12 | 6 | no OCV/AOCV, no SI-aware timing |
| Power estimate | 4 | clean | OpenSTA report_power | 4 | 2 | 20% input activity; no power budget in spec |
| IR drop / EM (static) | 4 | clean | OpenROAD PSM | 2 | 2 | static IR only; EM not analyzed |
| DFT scan + ATPG fault coverage | 5 | partial | plan only (dft_plan.md) | 2.5 | 0 | plan only in Phase 0 |
| Signal integrity / crosstalk | 3 | not run | - | n/a | 0 | out of open-flow scope |
| Reliability (aging, ESD, latch-up) | 3 | not run | - | n/a | 0 | out of open-flow scope |
| Foundry-certified signoff (Calibre-class) | 3 | not run | - | n/a | 0 | no foundry-certified decks |
| GDS integrity + reproducibility | 6 | clean | KLayout read-back + reproduce.sh | 6 | 6 | |

## 4. Known limits

- **PDK and decks:** open SKY130 with open-source Magic, KLayout and Netgen decks. A foundry's certified decks (Calibre-class) were not run, and their results may differ.
- **Timing:** OpenSTA at the PDK's typical, slow and fast corners (9 corners). There is no on-chip variation modeling (OCV/AOCV) and no SI-aware timing.
- **Power and IR:** power is estimated at 20% input switching activity, and the spec sets no power budget. Only static IR was analyzed; EM was not.
- **DFT:** plan only. Scan was not inserted (it is out of scope in the spec) and there is no ATPG fault-coverage number.
- **Not assessed:** signal integrity and crosstalk, reliability (aging, ESD, latch-up) and foundry-certified signoff.
- **Pre-silicon only:** all results come from simulation and layout tools.

The readiness gaps close with: foundry-certified DRC and LVS decks; OCV/AOCV and SI-aware timing; vector-based power with silicon-correlated models; full static and dynamic IR and EM with a package model; and scan insertion with ATPG. All of these are Phase 1 work with commercial tools.

## 5. Open items

**DFM (`reports/dfm_scorecard.json`): 0 high, 2 medium, 5 low.** All have owner Orion.

- **DFM-003 (medium):** 15 met1 line ends are at near-minimum spacing. The last two listed locations nearly coincide, so the real count may be 14. Suggested fix: extend spacing or add end extensions.
- **DFM-001 (medium):** 2 li windows are at 0.5565 density against the PDK maximum of 0.6 (92.8%), which leaves little CMP margin. Suggested fix: spread routing in these windows.
- **DFM-004, 005, 002, 006, 007 (low):** share of routing near minimum width or spacing. met1 52.7%, with 574 near-minimum-spacing edges, is the main bridging-sensitive population. met2 is 74.9% and met3 26.1%, both minimum width only. li is 100%, mostly standard-cell geometry. met4 is 0%.

**Spec and process:**

- The spec still carries DEFAULT - needs G1 review markers on these items: load works while enable=0; the up_down encoding; wrap-around on overflow and underflow (REQ-007, REQ-008); control priority (REQ-010); and the unpinned PDK release. G1 is recorded as approved. Confirm these defaults were accepted there.
- The spec has three open questions. (1) Is load acceptable while enable=0? (2) Does the customer need a carry or overflow flag? None is included. (3) Which sky130A release and STA corners apply? The 9-corner STA set is the flow's choice, not one the spec defines.
- Readiness data inconsistency: three 'not run' checks are marked out of open-flow scope, but their gap entries say 'fix and re-run the check (this phase)'. These are not Phase 0 actions. The readiness report needs a correction.

## 6. Where to find the evidence

- Checklist: `reports/tapeout_checklist.json`
- Readiness scoring: `reports/tapeout_readiness.json`
- DFM scorecard: `reports/dfm_scorecard.json`
- Spec: `spec/spec.yaml`
- Tool versions and file hashes: `tapeout/versions.lock`, `MANIFEST.sha256`
- Rebuild: `reproduce.sh`
