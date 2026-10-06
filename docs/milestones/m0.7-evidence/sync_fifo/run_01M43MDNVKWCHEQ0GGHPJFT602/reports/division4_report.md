# Division 4 (Signoff & Manufacturing) report: sync_fifo, stage gdsii

To: human VP. From: Sloane, Director of Signoff & Manufacturing. Source: the eight reports listed at the end. Nothing was re-run by me; all figures are copied from them.

## 1. Signoff results (hard checks first)

**Hard checks: 5 of 5 PASS** (tapeout_readiness.json). No conditions are attached to sync_fifo (conditions list is empty).

| Hard check | Result | Detail |
|---|---|---|
| DRC = 0 (Magic + KLayout, final GDS) | PASS | Magic 0, KLayout 0 violations |
| LVS match (Netgen, final GDS) | PASS | Circuits match uniquely; 2828 devices, 2835 nets |
| Antenna clean | PASS | 0 net / 0 pin violations, 2777 nets checked |
| Timing met, all corners | PASS | 9 of 9 corners; worst setup +0.2429 ns (max_ss_100C_1v60); worst hold +0.1384 ns (min_ff_n40C_1v95); TNS 0 |
| Equivalence RTL vs final netlist | PASS | proven |
| No human edits to artifacts | **NOT CHECKED** | no automated edit-detection exists yet; hash/provenance check is planned for Phase 1 |

The last row is not a pass. It is a known gap.

Other signoff data:
- **Timing:** clock 10.0 ns. Setup margin is thin at the slow (ss, 100C, 1.60 V) corners: 0.2429 ns at max_ss, 0.3751 ns at nom_ss, 0.552 ns at min_ss. Hold margin is thinnest at fast corners: 0.1384 to 0.1438 ns. No DRV violators at any corner. The I/O delays (3.000 ns) and clock uncertainty (0.25 ns) are default values flagged for G1 review.
- **Power (OpenSTA, 20% input activity):** tt 0.005751779 W, ss 0.004539046 W, ff 0.006683403 W. OpenLane total 0.005682576913386583 W. The spec has no power budget, so there is no power pass/fail limit.
- **Static IR:** worst drop 0.00137 V, average 0.000224 V, against a limit of 0.09 V (5% of 1.8 V). Measured and within the limit. **EM is not analysed.**
- **DFM scorecard:** 0 high, 3 medium, 6 low. The medium items are met1 line ends (304), li density windows near the limit (20) and one met2 line end. The checklist item "zero high-severity open items" is recorded as done.
- **Antenna:** worst net is net28 at 64.7% of its limit. Layer densities are recorded in pv_signoff.json.

## 2. Phase 0 gate (tapeout_readiness.json, phase0_gate)

**QUALIFIED PASS, marked by the human CEO on 2026-10-06. It is NOT a clean or unconditional pass.**
- sync_fifo is in the group with a full hard-check pass (5/5), together with counter8, alu8 and uart.
- spi_master is a conditional pass only, under an approved clock-net max-fanout limit of 20. That does not affect sync_fifo.
- Deferred to Phase 1: EM analysis and full IR/EM, DFT scan insertion and ATPG, and the artifact hash/provenance check.

## 3. Tape-out package

Checklist (tapeout_checklist.json): **16 of 16 items done**, including spec approved at G1, RTL frozen at G2, G3 approved (gate_01M46WTQ03T9DHDT99KPN5MTAP), reproduce.sh clean-container check, and versions.lock and hashes recorded. Final GDS sha256: 60a9bff2e9ba88eed16c1db7b86b59da7f4ece142db670055e8f4304d3e60f3f. pv_signoff verdict: clean on the final streamed GDS.

## 4. Readiness figures (derived only; not the pass criterion)

These percentages are derived from weights and partial credit. They are not the pass criterion. The hard checks above are.
- **Baseline A (open SKY130 shuttle): 92.7%** (earned 90.0 of 97.0 weight).
- **Baseline B (commercial production tape-out): 64.1%** (earned 68.0 of 106.0 weight).
- Partial-credit values: dft 0.0, ir_em 0.5, other 0.5.

Scope labels:
- **DFT scan + ATPG:** deferred, not measured, 0 fault coverage, earns 0 of 5.
- **IR/EM (static):** static IR measured and passed; EM not analysed. Earned 2.0 of 4 in both baselines.
- **Excluded from Baseline A** because open tools structurally cannot do them: signal integrity/crosstalk (3), reliability (3), foundry-certified signoff (3). They score 0 in Baseline B.
- All results are pre-silicon. No physical silicon was made or tested.

## 5. Risks

1. **Thin slow-corner setup margin:** 0.2429 ns (2.4% of the period) at max_ss. Met, but a human should decide whether it is adequate. It is driven by the default I/O budget. Any fix such as registering rd_data changes behaviour and is an RTL architecture decision, not mine.
2. **Thin fast-corner hold margin:** 0.1384 ns at min_ff. It is not confirmed whether the figures use propagated post-CTS clocks.
3. **Coverage gaps:** EM, DFT/ATPG, signal integrity, reliability and foundry-certified decks are not done. The open-tool DRC/LVS decks may differ from a foundry's.
4. **No-human-edits check is NOT CHECKED.**
5. **Yield exposure (low severity):** 47.3% of met1 edges are near minimum width/spacing, and 304 met1 line ends are at near-minimum spacing. Owner: Orion.
6. **Unconfirmed IR inputs:** IR corner and voltage-source locations are not documented; power is estimated at 20% activity, not from simulation.

## 6. Cost

Run spend by agent (division_cost.json): Orion $0.057283, Tick $0.036656, Calla $0.031249, Chronos $0.026585, Grid $0.010223, Sienna $0.003758, Proof $0.003543, Rex $0.003025, Gideon $0.001044, Volta $0.000736, Fabian $0.000596; Sentinel, Tess, Mason and Sloane $0.0. **Sum of the listed figures: $0.174698.** No budget figure is in the inputs, so I cannot state spend vs budget or a weekly forecast. I am flagging that gap.

## 7. Decisions needed from the human

**D1. G4 (real silicon).** G4 is a human decision, and I do not approve gates.
- Options: (a) approve G4 on the Phase 0 evidence; (b) hold G4 until the Phase 1 items close (EM, DFT/ATPG, hash/provenance check, foundry-certified decks); (c) approve only for an open SKY130 shuttle (Baseline A scope).
- Recommendation: decide G4 on the 5/5 hard checks, the qualified gate and the stated gaps, not on the percentages. If the target is a real foundry run, option (b) is the safer choice. Option (c) fits the open-shuttle scope the evidence covers.

**D2. Slow-corner setup margin (0.2429 ns).**
- Options: accept as is; or ask the RTL owner for a design change to add margin.
- Recommendation: accept for Phase 0 and record the decision. Revisit after the I/O defaults are reviewed.

**D3. Cost budget.** Please give me the division budget so I can report spend against it.

Sources: reports/sta_signoff.json, power_report.json, ir_report.json, pv_signoff.json, dfm_scorecard.json, tapeout_checklist.json, tapeout_readiness.json, division_cost.json.
