# Division 4 (Zone 4) report: alu8, stage gdsii

From: Sloane, Director of Signoff & Manufacturing. To: human VP. Source: the eight reports/*.json files listed in the task. Every number below is quoted from them, or is a plain sum or count of them where stated.

## 1. Signoff results (hard checks decide, not percentages)

Hard checks (tapeout_readiness.json): verdict PASS, 5 of 5 passed, conditions: none.

| Hard check | Status | Detail |
|---|---|---|
| DRC = 0 (Magic + KLayout, final GDS) | PASS | Magic 0, KLayout 0 violations |
| LVS (Netgen, final GDS) | PASS | Circuits match uniquely; 243 devices, 261 nets, layout = schematic |
| Antenna | PASS | 0 net / 0 pin violations, 247 nets checked; worst is net13 at 37.33% of its limit (ratio 149.31 vs 400.0) |
| Timing, all corners (setup, hold, DRV) | PASS | 9 of 9 corners; worst setup +3.276 ns (max_ss_100C_1v60); worst hold +0.4196 ns (min_ff_n40C_1v95); TNS 0.0 ns in every corner; no DRV violators |
| Equivalence RTL vs final netlist | PASS | check eqy_rtl_vs_final |
| No human edits to artifacts | NOT CHECKED | No automated edit-detection check exists yet; hash/provenance check is in the Phase 1 plan |

Condition to state prominently: the hard-check verdict lists 5 checks as passed; the "no human edits" item is NOT CHECKED, not passed. It is not counted in the 5.

Supporting results: GDS is clean on the final streamed GDS (pv_signoff verdict). DFM scorecard has 0 high, 2 medium, 5 low items (see Risks). Static IR: worst drop 0.000207 V, average 4.54e-05 V, against a limit of 0.09 V (5% of 1.8 V). Power (OpenSTA, 20% vectorless activity, no power budget in spec): 0.0002593128 W at tt_025C_1v80, 0.0002075033 W at ss_100C_1v60, 0.0002985172 W at ff_n40C_1v95.

## 2. Phase 0 gate

phase0_gate status: QUALIFIED PASS, marked by the human CEO, 2026-10-06 (source PHASE_GATES.md). It is NOT a clean or unconditional pass. For alu8 the hard-check result is a full pass (5 of 5). Explicitly deferred to Phase 1: EM analysis and full IR/EM (Phase 0 has static IR only); DFT scan insertion and ATPG (no fault coverage measured); the artifact hash/provenance check.

## 3. Tape-out package

Tape-out checklist: 16 of 16 items marked done, including spec approved at G1, RTL frozen at G2, regression passing, RTL-vs-netlist equivalence, 9-corner STA, DRC, LVS, antenna, density, DFM with zero high-severity items, power and IR, pin list, Sentinel findings closed, reproduce.sh in a fresh container, versions.lock and hashes recorded, and G3 approved (gate gate_01M44EQ71TZYHCF6FPGZDHXEPS). Final GDS sha256: 1ca961c967d9d3e01dbc9c6043c2db848d238930de5b4d37ae25aaa900a75768.

## 4. Readiness figures (derived, not a pass criterion)

These are derived figures (derived: true) built from weights and partial credit. They do not decide pass or fail; section 1 does.

- Baseline A (open SKY130 shuttle requirements): 92.7%, from 90.0 earned of 97.0 weight.
- Baseline B (commercial production tape-out on a real foundry PDK): 64.1%, from 68.0 earned of 106.0 weight.
- Partial credit used: dft 0.0, ir_em 0.5, other 0.5.
- DFT scan + ATPG: deferred, not measured, 0 fault coverage; earned 0.0 of weight 5 in both baselines.
- IR drop / EM (static): static IR measured and passed; EM not analysed; earned 2.0 of weight 4.
- Excluded from Baseline A (open tools cannot do them): signal integrity/crosstalk, reliability (aging, ESD, latch-up), foundry-certified signoff; each earns 0.0 in Baseline B.
- These are pre-silicon results from simulation and layout tools. No physical silicon was made or tested.

## 5. Risks

- DFM: 0 high, 2 medium, 5 low. Medium: DFM-003, 35 met1 line ends at near-minimum spacing; DFM-001, 7 li density windows near the PDK max of 0.6 (up to 0.569, 94.9% of limit). Both owned by Orion. Low items are near-minimum width/spacing shares, for example met2 81.1%, li 100.0%, met1 51.6%.
- Open-tool limits: EM, dynamic IR, crosstalk, reliability and foundry-certified decks are not covered. Open DRC/LVS decks may differ from a foundry's own decks.
- Timing: the I/O delay budget (4.0 ns in/out) and 0.25 ns uncertainty are default values pending customer confirmation. The tool data does not state the netlist stage or parasitics source, and the worst-path cell detail is not available.
- Power/IR: the OpenLane power total (0.00020245423365850002 W) does not match the OpenSTA tt_025C_1v80 total (0.0002593128 W); the cause is unconfirmed. The IR run does not state its corner, net or source locations, and only one IR result exists.
- Hash/provenance ("no human edits") is not checked.

## 6. Cost

Per-agent run spend (USD): Rex 0.004262, Proof 0.00128, Orion 0.00071, Calla 0.000681, Sienna 0.000311, Grid 0.00022, Gideon 0.000214, Tick 0.000204, Chronos 0.000076, Fabian 0.000045, Volta 0.000029; Sentinel, Tess, Sloane, Mason 0.0. Sum of these: $0.008032 (derived). No budget figure is in the inputs, so spend vs budget and a weekly forecast are not stated.

## 7. Decisions needed from the human

1. G4 (release for real silicon) is a human decision; I do not approve gates. Options: (a) approve G4 for the Baseline A open shuttle with the QUALIFIED PASS conditions accepted (EM, DFT/ATPG and provenance deferred); (b) hold G4 until Phase 1 closes the deferred items (EM, DFT scan + ATPG, hash/provenance check); (c) approve G4 with extra conditions you name. Recommendation: (b) if the part is for anything beyond a learning shuttle; (a) is reasonable only if you accept that DFT fault coverage is 0 and EM is unanalysed.
2. Confirm the I/O delay budget and clock uncertainty with the customer (currently defaults). Recommendation: confirm before G4.
3. Ask Volta to confirm the OpenLane vs OpenSTA power difference and the IR run scope. Recommendation: yes, low cost.
4. Medium DFM items (DFM-003, DFM-001): accept as-is or send to Orion. Recommendation: accept for Phase 0 and record the decision, since there are 0 high-severity items.
