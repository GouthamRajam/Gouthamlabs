# Division 4 (Signoff & Manufacturing) report to the VP: alu8, stage gdsii

From: Sloane, Director of Signoff & Manufacturing (Zone 4). Task task_01M44DR7YNTGBGD9DFGVD61549.
Every number below is copied from the input reports. I approve no gates. **G4 (real silicon) is your decision.**

## 1. What was delivered
- Signoff results for alu8 on the final streamed GDS (run run_01M44DR7XRWAQ9XY53AG8SRJCM, gds_sha256 1ca961c967d9...).
- Tape-out checklist: **16 of 16 items marked done**, including G3 approved (gate_01M44EQ71TZYHCF6FPGZDHXEPS).
- Tape-out readiness score: **Baseline A (open SKY130 shuttle) 95.3%**, **Baseline B (commercial production) 64.1%**.

## 2. Signoff results (quality)
| Area | Result (from reports) |
|---|---|
| Timing (OpenSTA, 9 corners) | All 9 corners `passed: true`; setup TNS 0.0 ns and hold TNS 0.0 ns everywhere; no DRV violators. Worst setup slack 3.276 ns (max_ss_100C_1v60); worst hold slack 0.4196 ns (min_ff_n40C_1v95). Clock period 13.333333 ns. |
| DRC | Magic 0 violations, KLayout 0 violations. |
| LVS | "Circuits match uniquely": devices 243/243, nets 261/261. |
| Antenna | 0 net and 0 pin violations over 247 nets; worst net13 at 37.33% of limit (ratio 149.31 vs 400.0). |
| Power (vectorless, 0.2 activity) | Total 0.0002593128 W (tt), 0.0002075033 W (ss), 0.0002985172 W (ff). No power budget in the spec. |
| IR drop (static) | Worst 0.000207 V, average 4.54e-05 V, limit 0.09 V (5% of 1.8 V). EM not analyzed. |
| DFM scorecard | High 0, medium 2, low 5. |

Escaped defects: none reported in the inputs.

## 3. What is at risk, and what I am doing
1. **Two medium DFM items (yield, not correctness).** DFM-003: 35 met1 line ends at near-minimum spacing. DFM-001: 7 li windows within 10% of the PDK max density 0.6 (up to 0.569). Owner Orion. Action: asking Orion for a fix-or-accept proposal with cost and schedule before G4.
2. **Density numbers need explaining.** pv_signoff lists layer density m5 1.0, m3 0.9709549895759344, m4 0.9667335964672477, while DFM-006 describes met3 as 2.9% density. These cannot both be the same measure. Checklist item 9 says density rules are met, but I want Fabian/Orion to state what the pv_signoff figures mean before you rely on them.
3. **Power cross-check mismatch.** OpenLane flow power 0.00020245423365850002 W vs OpenSTA tt total 0.0002593128 W; corner and activity behind the OpenLane figure are not stated (Volta open issue).
4. **Timing evidence gaps.** sta_tool.json does not record netlist stage or parasitics source (REQ-014 needs post-route STA); I/O delays of 4.0 ns are DEFAULT values pending customer confirmation (Chronos open issues).
5. **Coverage gaps vs commercial tape-out (Baseline B).** DFT/ATPG is plan only (2.5 of 5 in A, 0.0 in B). Signal integrity, reliability (aging/ESD/latch-up) and foundry-certified signoff are "not run". No OCV/AOCV, no EM, no foundry-certified DRC/LVS decks. These close only in Phase 1 with commercial tools. Note: the readiness gaps list says "fix and re-run the check (this phase)" for the three not-run items, while their row notes say "out of open-flow scope"; I am asking the owner to correct that wording.

## 4. Cost
Run spend by agent (USD): Rex 0.004262, Proof 0.00128, Orion 0.00071, Calla 0.000681, Sienna 0.000311, Grid 0.00022, Gideon 0.000214, Tick 0.000204, Chronos 7.6e-05, Fabian 4.5e-05, Volta 2.9e-05; Mason, Sentinel, Tess 0.0.
**Budget and weekly forecast: not in the inputs.** I cannot report spend vs budget until Penny supplies the division budget.

## 5. Decisions needed from you
**D1. G4 for real silicon (open SKY130 shuttle).**
- Option A: Approve G4 now. All 16 checklist items done; open-flow signoff clean; Baseline A 95.3%.
- Option B: Hold G4 until (a) the density figures in pv_signoff are explained and (b) the two medium DFM items are fixed or formally accepted by you.
- Option C: Do not submit.
- **My recommendation: Option B.** The risk is small but unexplained numbers should not go to silicon; I expect this to be a short hold.

**D2. Commercial production path (Baseline B 64.1%).** Not possible in Phase 0 (needs commercial tools, foundry decks and ATPG). Recommendation: treat this tape-out as a shuttle/prototype only; decide Phase 1 scope separately.

**D3. Customer I/O budget.** Confirm or replace the DEFAULT 4.0 ns input/output delays. Recommendation: confirm before G4; current worst setup slack is 3.276 ns.

Pre-silicon only: no physical silicon has been manufactured or tested.
