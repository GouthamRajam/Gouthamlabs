# Division 4 report (Signoff & Manufacturing, Zone 4): uart, stage gdsii

From: Sloane, Director of Signoff & Manufacturing. To: VP Physical Design & Signoff (human). All numbers come from the reports named in brackets.

## Bottom line
All signoff checks the open flow can run are clean, the G3 gate is recorded as approved, and the tape-out checklist shows 16 of 16 items done. G4 (real silicon) is your decision. The evidence is pre-silicon and open-tool only; several checks that matter for production were not run (see Risks). I am not approving G4.

## Signoff results
- **Timing [sta_signoff]:** 9 of 9 corners passed. Setup and hold TNS are 0.0 ns and there are no DRV violators. Worst setup slack is 5.6705 ns (max_ss_100C_1v60); typical corner is 9.7478 ns. Worst hold slack is 0.1082 ns (min_ff_n40C_1v95); fast-corner hold is 0.1082 to 0.1130 ns. Clock period is 20.0 ns (50 MHz).
- **Power [power_report]:** total 0.0007882774 W (tt), 0.0006277686 W (ss), 0.0009117265 W (ff), at 20% default input activity. OpenLane reports 0.0008120654 W; the cause of the difference from the tt figure is not given.
- **IR drop [ir_report]:** worst 0.00087 V, average 0.000153 V, limit 0.09 V (5% of 1.8 V).
- **Physical verification [pv_signoff]:** Magic DRC 0, KLayout DRC 0, LVS errors 0 ("Circuits match uniquely", 952 devices and 980 nets in both layout and schematic). Antenna: 0 net and 0 pin violations on 955 nets; worst is 72.17% of limit (net41, met1). Verdict: clean on the final streamed GDS (sha256 9a263f8b35cc9df16c171fa6317eba31caa18906494cdfaf991b5b572e69c039).
- **DFM [dfm_scorecard]:** high 0, medium 2, low 5. Medium: DFM-003, 164 met1 line ends at near-minimum spacing; DFM-001, 20 li windows at 0.5999 against the 0.6 max density. Both are owned by Orion. No hotspot is a confirmed defect.

## Tape-out package status [tapeout_checklist, tapeout_readiness]
- Checklist: 16 of 16 done, including regression, RTL-vs-netlist equivalence, STA, DRC, LVS, antenna, density, power/IR, pin list, reproduce.sh in a clean container, and G3 approved (gate_01M47Z5CHDMPRWZ304M8D6CQMB).
- Readiness score: 95.3% against Baseline A (open SKY130 shuttle) and 64.1% against Baseline B (commercial production tape-out on a real foundry PDK). The gap is the point: the design is shuttle-ready on open tools, not production-ready.

## Risks and what is not covered
1. **Hold margin is thin at fast corners** (0.1082 to 0.1130 ns). Positive, but Chronos asks a human to judge it. Clock ideal vs propagated for this run is not stated, and that affects hold confidence.
2. **rx input** is constrained with a 6 ns input delay instead of a false path; this needs a human decision. Input and output delays (6.000 ns) are SDC defaults, not from the spec.
3. **Not run, out of open-flow scope:** signal integrity/crosstalk, reliability (aging, ESD, latch-up), foundry-certified signoff. DFT is plan only (partial credit, no ATPG coverage number). EM is not analyzed.
4. **Open-tool limits:** DRC/LVS use open decks, not foundry-certified ones; STA has no OCV/AOCV or SI-aware timing; power is at default activity with no workload vectors; IR conditions (corner, source locations, PDN model) are not documented.
5. **DFM:** the 2 medium items are open (met1 line ends, li density windows). met1 has 52.9% of edges near limit, li 100% (expected by construction), met2 81.4%.
6. No physical silicon has been made or tested. All results are pre-silicon.

## Cost [division_cost]
Recorded run spend across 14 agents sums to USD 0.187512. Largest: Sienna 0.127171, Rex 0.044168, Orion 0.009525. No budget figure was supplied in the inputs, so I cannot state spend against budget or a weekly forecast.

## Decisions needed from you
1. **G4 (real silicon).** Options: (a) approve for an open SKY130 shuttle run; (b) hold until open items are closed; (c) reject. Recommendation: (a) only if the target is an open shuttle, since that is what the evidence supports (95.3% vs Baseline A). For a commercial production tape-out (64.1% vs Baseline B), do not approve until Phase 1 foundry-certified decks and tools close the gaps.
2. **Hold margin sign-off.** Options: accept 0.1082 ns as is, or ask Chronos for hold-buffer margin and a propagated-clock re-check. Recommendation: have the propagated-clock status confirmed before G4, then accept if hold stays positive.
3. **rx constraint.** Options: keep the 6 ns input delay, or declare a false path. Recommendation: decide with the spec owner; I will not change constraints myself.
4. **Two medium DFM items.** Options: accept as known risk, or send to Orion to spread routing and add line-end extension. Recommendation: accept for a shuttle; fix for production.
