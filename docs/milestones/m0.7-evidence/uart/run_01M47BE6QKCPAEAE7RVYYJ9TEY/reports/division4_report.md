# Division 4 (Zone 4) Report to the VP: uart, stage gdsii

From Sloane, Director of Signoff & Manufacturing. Pre-silicon results from open SKY130 tools only. Nothing here approves a gate.

## 1. Hard checks (the pass criterion)

**Verdict: PASS, 5 of 5 hard checks passed. One further item is NOT CHECKED (see the condition below).**

| Hard check | Result | Detail |
|---|---|---|
| DRC, Magic + KLayout, final GDS | PASS | Magic 0, KLayout 0 violations |
| LVS (Netgen, final GDS) | PASS | Circuits match uniquely: 952 devices, 980 nets |
| Antenna | PASS | 0 net / 0 pin violations, 955 nets checked; worst is 72.17% of its limit (met1, net41) |
| Timing, all corners | PASS | 9 of 9 corners; worst setup +5.6705 ns (max_ss_100C_1v60); worst hold +0.1082 ns (min_ff_n40C_1v95); TNS 0; no DRV violators |
| RTL vs final netlist equivalence | PASS | check eqy_rtl_vs_final |
| No human edits to artifacts | **NOT CHECKED** | No automated hash/provenance check exists yet; planned for Phase 1. Not counted in the 5 of 5. |

**Condition to read first:** the hard-check pass does not cover the "no human edits" item, and the hold margin at the fast corners (0.1082 to 0.1130 ns) is positive but thin. The timing report asks a human to judge whether it is sufficient. Final GDS sha256: 9a263f8b35cc9df16c171fa6317eba31caa18906494cdfaf991b5b572e69c039.

Other signoff results:
- Power (20% input activity, no spec power budget): total 0.0007882774 W at tt, 0.0006277686 W at ss, 0.0009117265 W at ff.
- Static IR: worst drop 0.00087 V, average 0.000153 V, limit 0.09 V (5% of 1.8 V). Measured and passed. EM is not analysed.
- DFM scorecard: 0 high, 2 medium, 5 low. Mediums: 164 met1 line ends at near-minimum spacing (DFM-003) and 20 li windows at 0.5999 against the 0.6 max density (DFM-001). Both are owned by Orion.

## 2. Phase 0 gate

**QUALIFIED PASS, marked by the human CEO on 2026-10-06. This is NOT a clean or unconditional pass.** For uart: full hard-check pass (5/5). Explicitly deferred to Phase 1: EM analysis and full IR/EM, DFT scan insertion + ATPG (no fault coverage measured), and the artifact hash/provenance check.

## 3. Tape-out package

Checklist: 16 of 16 items done, including regression, equivalence, STA, DRC, LVS, antenna, density, DFM, power/IR, pin list, Sentinel findings, reproduce.sh in a fresh container, versions.lock and hashes. G3 is approved. No G4 record is in my inputs.

## 4. Readiness (derived figures, not the pass criterion)

| Baseline | Derived value | Earned / weight |
|---|---|---|
| A (open SKY130 shuttle) | 92.7% | 90 / 97 |
| B (commercial production tape-out) | 64.1% | 68 / 106 |

Partial-credit values: dft 0.0, ir_em 0.5, other 0.5. Scope labels:
- DFT: deferred, not measured, 0 fault coverage; earns 0 of 5.
- IR/EM: static IR measured and passed; EM not analysed (2 of 4).
- Signal integrity, reliability and foundry-certified signoff: not run, excluded from Baseline A, counted as 0 in Baseline B.

## 5. Risks and what I am doing

- **Thin fast-corner hold margin** (+0.1082 ns). The report does not say whether the clock was ideal or propagated, which affects confidence. Needs a human judgement.
- **rx input** is constrained with a 6 ns input delay instead of a false path; treatment of this asynchronous input needs a human decision.
- **IR conditions** (corner, source locations, PDN model) are not documented. EM is unchecked.
- **Data mismatches to resolve:** li density is 0.427 in the DFM scorecard but 0.5733 in the PV report; OpenLane power total (0.0008120654 W) differs from the tt STA total (0.0007882774 W). Neither is explained in the data.
- **Tool limits:** open DRC/LVS decks, not foundry-certified; no OCV or SI-aware timing; no real silicon was made or tested.

## 6. Cost

Per-agent run spend sums to about USD 0.1875. Largest: Sienna 0.127171, Rex 0.044168, Orion 0.009525. No budget figure was supplied, so I cannot state spend against budget.

## 7. Decisions needed from you

1. **G4 (real silicon):** approve or hold. This is your decision. My recommendation: hold G4 until decisions 2 and 3 are made, because the Phase 0 pass is qualified and not production assurance.
2. **Hold margin** (+0.1082 ns at fast corners): accept, or ask for hold-fix work and re-run. Recommendation: have Chronos confirm clock propagation first, then decide.
3. **rx constraint:** keep 6 ns input delay, or change to a false path. Recommendation: decide before G4.
4. **DFM mediums:** accept as informational, or send to Orion. Recommendation: accept for Phase 0 and log for Phase 1.
5. **Deferred items** (EM, DFT, hash/provenance check): confirm they stay in Phase 1 scope.
