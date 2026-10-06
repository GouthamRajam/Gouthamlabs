# Division 4 (Signoff and Manufacturing, Zone 4) report: spi_master

To: human VP. Stage: gdsii. Source: the eight reports listed in the task. Nothing was re-run by me.

## 1. Hard checks (verdict: CONDITIONAL PASS)

**CONDITION, read first:** timing and DRV pass only under the approved clock-net max-fanout limit of 20 (config/signoff.yaml cts.clock_max_fanout). Eight clock-tree buffer outputs (clkbuf_3_0 to clkbuf_3_7) have fanout 11 to 17, above the SDC limit of 10. Under a flat SDC max-fanout limit of 10 this design FAILS. The same 8 entries appear in all 9 corners.

| Hard check | Status | Detail |
|---|---|---|
| DRC (Magic + KLayout, final GDS) | PASS | Magic 0, KLayout 0 violations |
| LVS (Netgen, final GDS) | PASS | Circuits match uniquely (684 devices, 723 nets) |
| Antenna | PASS | 0 net / 0 pin violations, 692 nets checked |
| Timing, all corners (setup, hold, DRV) | PASS (conditional) | 9/9 corners; worst setup +8.9381 ns (max_ss_100C_1v60); worst hold +0.104 ns (min_ff_n40C_1v95); TNS 0 |
| Equivalence RTL vs final netlist | PASS | eqy_rtl_vs_final |
| No human edits to artifacts | NOT CHECKED | no automated edit-detection exists yet; hash/provenance check is in the Phase 1 plan |

Result as reported: 5 of 5 checks passed, with the conditional timing pass above; the sixth item, no human edits, is not checked. Hold margin of 0.104 ns is the thinnest margin in the design and the data does not list the limiting hold paths.

## 2. Phase 0 gate

PHASE_GATES.md status: **QUALIFIED PASS**, marked by the human CEO, 2026-10-06. This is NOT a clean or unconditional pass. For spi_master it is a conditional pass (5/5) only under the clock-net fanout limit of 20. Explicitly deferred to Phase 1: EM analysis and full IR/EM (Phase 0 has static IR only), DFT scan insertion and ATPG, and the artifact hash/provenance check.

## 3. Tape-out package

Checklist: 16 of 16 items done, including spec approved at G1, RTL frozen at G2, regression, equivalence, STA, DRC, LVS, antenna, density, DFM (zero high severity), power and IR, pin list, Sentinel findings, reproduce.sh in a fresh container, versions.lock and hashes, and G3 approved (gate_01M48RVBQACX41SHEYXGWPKCZQ). Final GDS sha256: fc4eecba71494124a0c36c7ab32b7e820a3d2ab26ef5fe1140dddf2490b000d3, verdict: clean on the final streamed GDS. G4 (real silicon) is not approved; see decisions.

## 4. Other signoff results

- **Power** (20% input activity, no power budget in spec): tt 0.0005809897 W, ss 0.0004625672 W, ff 0.0006728195 W. OpenLane total 0.0005702339112758636 W; the reports do not say why it differs from the tt figure.
- **Static IR:** measured and passed. Worst drop 0.000411 V, average 0.00011 V, limit 0.09 V (5% of 1.8 V). EM: not analysed.
- **DFM scorecard:** high 0, medium 2, low 5. Medium items: DFM-003, 103 met1 line ends at near-minimum spacing; DFM-001, 20 li windows within 10% of the 0.6 max density (worst window 0.583). Owner: Orion.
- **Antenna worst case:** 50.97% of limit (net _115_, met1 side area).

## 5. Readiness figures (derived, not a pass criterion)

These are partial-credit derived figures. The hard checks above decide pass or fail, not these numbers.

- Baseline A (open SKY130 shuttle requirements): 92.7% derived (90.0 of 97.0 weighted points), partial credit dft = 0.0, ir_em = 0.5.
- Baseline B (commercial production tape-out, real foundry PDK): 64.1% derived (68.0 of 106.0).
- Scope labels: DFT: deferred, not measured, 0 fault coverage (0.0 of 5 points). Static IR: measured, passed; EM: not analysed (2.0 of 4 points in A). Signal integrity, reliability and foundry-certified signoff: not run, excluded from Baseline A as beyond open tools.
- No physical silicon was made or tested; all results are pre-silicon, from open SKY130 tools, not foundry-certified decks.

## 6. Risks

1. Clock fanout exception (fails under a flat limit of 10): needs human acceptance. Mitigation if not accepted: re-run CTS with smaller sink clusters.
2. Hold slack 0.104 ns, no hold path list, no OCV/SI-aware timing.
3. IO delays and other SDC values are placeholders (DEFAULT) per the STA report.
4. DFT not measured; EM not analysed; IR source locations and corner not documented.
5. Yield exposure: DFM-003 line ends and DFM-001 li density, both medium.

## 7. Cost

Total run spend 0.089963 USD (my sum of the per-agent figures). Largest: Sienna 0.075562, Rex 0.008309, Orion 0.002589, Proof 0.001698. No budget figure is in the cost report, so spend vs budget and a weekly forecast cannot be stated.

## 8. Decisions needed from the human

1. **Accept the clock-net fanout limit of 20 for spi_master?** Options: (a) accept and record it; (b) require a CTS re-run to bring leaf fanout to 10 or below. Recommendation: your call; I will not waive it myself. If real silicon is the goal, (b) removes the condition.
2. **G4 (real silicon):** this is a human decision. Options: (a) approve G4 with the conditions in sections 1 and 2 accepted; (b) hold G4 until Phase 1 closes DFT, EM and the provenance check. Recommendation: (b) if the die is to be fabricated, since DFT has 0 measured fault coverage and the no-human-edits check is not run.
3. **Medium DFM items (DFM-003, DFM-001):** fix before G4 or accept? Recommendation: ask Orion for a fix estimate first.
