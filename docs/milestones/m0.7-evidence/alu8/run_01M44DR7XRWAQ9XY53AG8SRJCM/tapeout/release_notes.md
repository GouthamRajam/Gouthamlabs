# alu8 — Tape-out Release Notes

## 1. What this package is
- **Design:** `alu8` (spec version 1): 8-bit synchronous ALU with a registered 8-bit result and registered N/Z/C/V flags. Operations: ADD, SUB, AND, OR, XOR, SHL, SHR, CMP (op codes 0-7, all defined).
- **Clock / reset:** one clock `clk`, target 75 MHz (period 13.333 ns), rising edge; synchronous active-low reset `rst_n`.
- **Technology:** open SkyWater **sky130A** PDK, standard cell library **sky130_fd_sc_hd**. Phase 0: open-source tools only.
- **Package contents (per checklist item 15):** final GDS, final netlist, constraints, signoff reports, evidence packets, `tapeout/versions.lock`, `MANIFEST.sha256` (SHA-256 of every file), `reproduce.sh`, and these release notes.
- **Not included:** no physical silicon was manufactured or tested. Every result below is pre-silicon, from simulation and layout tools.

## 2. Signoff status — tape-out checklist (Appendix B.9)
All 16 items are marked done in `reports/tapeout_checklist.json`. This file only reports that status; the linked check results hold the evidence.

| # | Item | Evidence kind | Done | Evidence |
|---|------|---------------|------|----------|
| 1 | Spec approved at G1 | gate record | yes | gate `gate_01M43C276RCFZE7W148MKQDK6Q` |
| 2 | RTL frozen at G2; no changes since | hash comparison | yes | checks `rtl_frozen_at_g2`, `constraints_not_loosened` |
| 3 | Regression 100% passing on frozen RTL | packet stage 4 | yes | M0.6 check `regression_100pct` |
| 4 | Equivalence RTL vs final netlist proven | eqy report | yes | check `eqy_rtl_vs_final` |
| 5 | Setup and hold met at all corners | STA reports | yes | check `sta_all_corners` (9 corners) |
| 6 | Zero DRC (Magic and KLayout) on final GDS | DRC reports | yes | checks `drc_magic_final_gds`, `drc_klayout_final_gds`, `package_drc_*` |
| 7 | LVS clean on final GDS | Netgen report | yes | checks `lvs_final_gds`, `package_lvs` |
| 8 | Antenna clean | report | yes | check `antenna_final` |
| 9 | Density rules met | report | yes | check `density_rules` |
| 10 | DFM scorecard: zero high-severity open items | Fabian report | yes | check `dfm_no_high_severity` |
| 11 | Power and IR within limits | Volta reports | yes | checks `power_estimated`, `ir_drop_within_limit` |
| 12 | Pin list matches spec | comparison report | yes | check `pins_match_spec` |
| 13 | All Sentinel findings closed or human-overruled | findings list | yes | all Sentinel reviews passed |
| 14 | reproduce.sh re-runs cleanly in a fresh container | CI log | yes | check `reproduce_clean_container` |
| 15 | versions.lock and hashes recorded | manifest | yes | `tapeout/versions.lock`, `MANIFEST.sha256` |
| 16 | G3 approved | gate record | yes | gate `gate_01M44EQ71TZYHCF6FPGZDHXEPS` (approved) |

**Checklist completion: 16 / 16 items marked done.**

## 3. Tape-out readiness — both baselines
Source: `reports/tapeout_readiness.json`. Partial credit = 0.5 × weight.

| Baseline | Meaning | Score | Weight total |
|----------|---------|-------|--------------|
| **A** | Open SKY130 shuttle requirements | **95.3 %** | 97 |
| **B** | Commercial production tape-out on a real foundry PDK | **64.1 %** | 106 |

These two numbers answer different questions. Baseline A says how ready this package is for an open SKY130 shuttle. Baseline B says how far it is from a commercial production tape-out. **The Baseline B score of 64.1 % means this package is not production-signoff-ready.**

| Check | Weight | Result | Tool | Earned A | Earned B | Note |
|-------|-------:|--------|------|---------:|---------:|------|
| Functional sim (RTL + gate-level) | 12 | clean | cocotb/Verilator/Icarus | 12.0 | 12.0 | |
| Coverage (line, toggle, functional) | 8 | clean | Verilator coverage + waveform bins | 8.0 | 8.0 | |
| Formal properties + RTL/netlist equivalence | 10 | clean | SymbiYosys, eqy | 10.0 | 10.0 | |
| DRC | 14 | clean | Magic + KLayout (SKY130 decks) | 14.0 | 7.0 | open decks, not foundry-certified |
| LVS | 14 | clean | Magic extraction + Netgen | 14.0 | 7.0 | open decks, not foundry-certified |
| Antenna | 4 | clean | OpenROAD check_antennas | 4.0 | 4.0 | |
| Density / fill | 4 | clean | KLayout PDK density deck | 4.0 | 4.0 | |
| Setup + hold STA, all PDK corners | 12 | clean | OpenSTA (9 corners) | 12.0 | 6.0 | no OCV/AOCV, no SI-aware timing |
| Power estimate | 4 | clean | OpenSTA report_power | 4.0 | 2.0 | 20% input activity; no power budget in spec |
| IR drop / EM (static) | 4 | clean | OpenROAD PSM | 2.0 | 2.0 | static IR only; EM not analyzed |
| DFT scan + ATPG fault coverage | 5 | partial | plan only (dft_plan.md) | 2.5 | 0.0 | plan only in Phase 0 |
| Signal integrity / crosstalk | 3 | not run | - | n/a | 0.0 | out of open-flow scope |
| Reliability (aging, ESD, latch-up) | 3 | not run | - | n/a | 0.0 | out of open-flow scope |
| Foundry-certified signoff (Calibre-class) | 3 | not run | - | n/a | 0.0 | no foundry-certified decks |
| GDS integrity + reproducibility | 6 | clean | KLayout read-back + reproduce.sh | 6.0 | 6.0 | |
| **Total** | | | | **92.5 / 97** | **68.0 / 106** | |

Under Baseline A, the three "not run" rows are excluded (earned A = n/a), so the weight total is 97 instead of 106.

## 4. DFM scorecard (`reports/dfm_scorecard.json`)
High: **0** · Medium: **2** · Low: **5**. All items are owned by Orion; none are high severity (checklist item 10).

| Rank | ID | Severity | Finding |
|-----:|----|----------|---------|
| 1 | DFM-003 | medium | met1: 35 line ends at near-minimum spacing (lithography open/bridge risk) |
| 2 | DFM-001 | medium | li: 7 density windows within 10% of the 0.6 max (up to 0.569, 94.9% of limit) in the 20-70 µm core |
| 3 | DFM-004 | low | met1: 51.6% of routing edge length near min width/spacing (3843 / 8940 edges) |
| 4 | DFM-005 | low | met2: 81.1% near min width (1254 / 6224 edges) |
| 5 | DFM-002 | low | li: 100% near min (mostly intrinsic to std-cell li) |
| 6 | DFM-006 | low | met3: 62.2% near min (148 edges, sparse layer) |
| 7 | DFM-007 | low | met4: 36.7% near min (8 edges) |

## 5. Known limits
- **PDK and decks:** open SKY130 PDK. DRC and LVS use the open Magic, KLayout and Netgen decks. A foundry's certified decks (e.g. Calibre) were not run and may give different results.
- **Timing:** OpenSTA at the PDK's typical, slow and fast corners (9 corners). No on-chip variation (OCV/AOCV) and no SI-aware timing. The spec's I/O timing assumes 0 ns external input/output delay because no budget was given.
- **Power / IR:** power is estimated at 20% input switching activity, and the spec has no power budget. IR is static only, and EM was not analyzed. Because of this, the IR/EM row earns only 2 of 4 points even under Baseline A.
- **DFT:** there is a plan only. No scan insertion and no ATPG fault-coverage number.
- **Not assessed:** signal integrity/crosstalk, reliability (aging, ESD, latch-up), and foundry-certified signoff.
- **Pre-silicon only:** no silicon was built or measured.
- **Functional scope (from spec):** no arithmetic shift, rotate, multiply, divide, carry-in, bus interface, valid/enable handshake, deeper pipelining, X/Z input handling, CDC, or power modes.

## 6. Open items
1. **Production gaps (Baseline B), Phase 1 / commercial tools:**
   - foundry-certified DRC and LVS decks
   - OCV/AOCV and SI-aware STA
   - vector-based power with silicon-correlated models
   - full static/dynamic IR and EM with a package model
   - scan insertion and ATPG
2. **Not-run checks:** signal integrity, reliability and foundry signoff. `tapeout_readiness.json` lists their closure as "fix and re-run the check (this phase)", but its own row notes say these are out of open-flow scope. A human needs to decide which is right; until then, treat them as not closable in Phase 0.
3. **DFM medium items:** DFM-003 (met1 line ends) and DFM-001 (li density margin) remain open and are owned by Orion. Neither blocks the checklist, and neither has been fixed.
4. **Spec defaults:** `spec/spec.yaml` still lists six open questions marked "DEFAULT - needs G1 review":
   - CMP result behaviour
   - shift semantics
   - SUB/CMP carry convention
   - opcode encoding
   - flag_z reset value
   - I/O delay budget

   G1 is recorded as approved (checklist item 1). These release notes do not say whether each default was explicitly confirmed. The customer should confirm them against the delivered behaviour.

## 7. Traceability
- Inputs:
  - `spec/spec.yaml` (sha256:c31399d29dc2)
  - `reports/tapeout_checklist.json` (sha256:c1e0e7807c11)
  - `reports/tapeout_readiness.json` (sha256:a3b37279b183)
  - `reports/dfm_scorecard.json` (sha256:8ad0f2f2cd0b)
- Full file hashes are in `MANIFEST.sha256`; tool versions are in `tapeout/versions.lock`.
- These notes restate the checklist and readiness data only. They make no new pass/fail claim. Pass/fail is decided by the real check results named in the evidence column.
