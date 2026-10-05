# Tape-out Readiness Report: sync_fifo

**Baseline A (open shuttle): 95.3% · Baseline B (commercial production): 64.1%**

Pre-silicon: no number here proves working silicon, only that the design passes the checks that were run.

## Rubric

| Check | Weight | Result | Earned A | Earned B | Tool (version) | Evidence |
|---|---|---|---|---|---|---|
| Functional sim (RTL + gate-level) | 12 | clean | 12 | 12 | cocotb/Verilator/Icarus | regression_100pct (M0.6), gls_final_netlist |
| Coverage (line, toggle, functional) | 8 | clean | 8 | 8 | Verilator coverage + waveform bins | coverage_* (M0.6) |
| Formal properties + RTL/netlist equivalence | 10 | clean | 10 | 10 | SymbiYosys, eqy | formal_3_meaningful, formal_vacuity (M0.6), eqy_rtl_vs_final |
| DRC | 14 | clean | 14 | 7 | Magic + KLayout (SKY130 decks) | checks drc_magic_final_gds, drc_klayout_final_gds, package_drc_* |
| LVS | 14 | clean | 14 | 7 | Magic extraction + Netgen | checks lvs_final_gds, package_lvs |
| Antenna | 4 | clean | 4 | 4 | OpenROAD check_antennas | check antenna_final |
| Density / fill | 4 | clean | 4 | 4 | KLayout PDK density deck | check density_rules |
| Setup + hold STA, all PDK corners | 12 | clean | 12 | 6 | OpenSTA (9 corners) | check sta_all_corners (9 corners) |
| Power estimate | 4 | clean - 20% input activity; no power budget in spec | 4 | 2 | OpenSTA report_power | power_estimated |
| IR drop / EM (static) | 4 | clean - static IR only; EM not analyzed | 2 | 2 | OpenROAD PSM | ir_drop_within_limit |
| DFT scan + ATPG fault coverage | 5 | partial - plan only in Phase 0 | 2.5 | 0 | plan only (dft_plan.md) | dft_plan_complete |
| Signal integrity / crosstalk | 3 | not run - out of open-flow scope | n/a | 0 | - |  |
| Reliability (aging, ESD, latch-up) | 3 | not run - out of open-flow scope | n/a | 0 | - |  |
| Foundry-certified signoff (Calibre-class) | 3 | not run - no foundry-certified decks | n/a | 0 | - |  |
| GDS integrity + reproducibility | 6 | clean | 6 | 6 | KLayout read-back + reproduce.sh | gds_readback, reproduce_clean_container |

Partial = 0.5 of the weight. A counts 97 weight points (the three n/a checks are excluded); B counts 106.

## Gaps

- **DRC** (clean): closes with foundry-certified DRC deck (Phase 1, commercial tools)
- **LVS** (clean): closes with foundry-certified LVS deck (Phase 1, commercial tools)
- **Setup + hold STA, all PDK corners** (clean): closes with OCV/AOCV and SI-aware timing (Phase 1, commercial STA)
- **Power estimate** (clean): closes with vector-based power with silicon-correlated models (Phase 1)
- **IR drop / EM (static)** (clean): closes with full static/dynamic IR and EM with package model (Phase 1, commercial tools)
- **DFT scan + ATPG fault coverage** (partial): closes with scan insertion + ATPG fault coverage (Phase 1, commercial ATPG)
- **Signal integrity / crosstalk** (not run): closes with fix and re-run the check (this phase)
- **Reliability (aging, ESD, latch-up)** (not run): closes with fix and re-run the check (this phase)
- **Foundry-certified signoff (Calibre-class)** (not run): closes with fix and re-run the check (this phase)

## Assumptions

```
ASSUMPTIONS
- PDK: SkyWater SKY130 (open), library sky130_fd_sc_hd. Not a commercial foundry PDK.
- DRC/LVS: open-source Magic, KLayout and Netgen decks. A foundry's own certified
  decks (e.g. Calibre) were not run and may differ.
- Timing: OpenSTA at the PDK's typical/slow/fast corners. No on-chip variation
  (OCV/AOCV), no SI-aware timing. Clock target as stated per design.
- Power/IR: estimated at 20% switching activity unless simulation activity was used;
  IR/EM analysis limited to what the open flow supports.
- DFT: plan only in Phase 0; no ATPG fault coverage number.
- Not assessed (out of open-flow scope): signal integrity/crosstalk, aging/ESD/
  latch-up reliability, foundry-certified signoff.
- No physical silicon was manufactured or tested. All results are pre-silicon,
  from simulation and layout tools.
- Baseline A = open SKY130 shuttle requirements. Baseline B = commercial production
  tape-out on a real foundry PDK.
```

## Evidence

- evidence packet: `tapeout/evidence/index.json`
- reproduce: `tapeout/reproduce.sh`
- checklist: `tapeout/reports/tapeout_checklist.md`
- manifest: `tapeout/MANIFEST.sha256`
