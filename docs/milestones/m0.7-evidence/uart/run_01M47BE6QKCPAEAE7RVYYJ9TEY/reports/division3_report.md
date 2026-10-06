# Division 3 (Zone 3) report to the VP: uart, place and route

From: Mason, Director of Physical Implementation. Every number below is copied from the reports; I computed no new values and ran no tools. No gate is approved here.

## 1. Delivered
- Synthesis: 736 cells, 8363.0208 um2 (reports/synth_report.json).
- Floorplan: die 23296.2 um2, core 18517.8 um2, utilization 0.469189 (45% core utilization choice), 0 power grid violations, 45 pins placed (reports/floorplan_report.json).
- Clock tree: 39 clock buffers, worst tree skew 0.039857 ns (max_ss_100C_1v60) against a 2.0 ns target, 9 corners reported (reports/cts_report.json).
- Place and route: 3 iterations. Iteration 3 is the final record: 0 route DRC errors, 0 antenna violating nets and pins, 0 max fanout / slew / cap violations, 0 disconnected pins, wirelength 20101 um, utilization 0.503243 (reports/pnr_report.json).
- DFT: a plan only. No scan insertion, no ATPG and no coverage number exist (dft/dft_plan.md).

## 2. Iteration history
| Iter | Change | Max fanout violations |
|---|---|---|
| 1 | PL_TARGET_DENSITY_PCT 55.0, CTS_DISTANCE_BETWEEN_BUFFERS 0 | 3 |
| 2 | PL_TARGET_DENSITY_PCT 60 | 1 (clkbuf_0_clk/X, fanout 16, limit 10) |
| 3 | CTS_DISTANCE_BETWEEN_BUFFERS 25 | 0 |

The recorded experiment PNR-UART-0013 predicted 0 violators at 60% density. Iteration 2 got only part of that, and zero was reached only after the buffer-distance change in iteration 3.

## 3. Timing (iteration 3, post-route, ns)
- Setup worst slack: 5.670498897604016 at max_ss_100C_1v60. Typical corner (nom_tt_025C_1v80): 9.747848137917238. All 9 corners positive.
- Hold worst slack: 0.1081844089377841 at min_ff_n40C_1v95. nom_ff_n40C_1v95: 0.11045037419512992. All 9 corners positive.

## 4. At risk, why, and what I am doing
1. **Unreconciled hold violation (main risk).** The CTS report shows hold slack -0.002920 ns at nom_ff_n40C_1v95 after CTS, with 80 hold buffers already inserted. The same figure appears pre-layout in the synthesis report. The iteration 3 route record shows +0.11045037419512992 ns at that corner. Our inputs do not say whether these are the same netlist stage, so I do not call the violation fixed. Action: ask Chronos to re-run STA on the final routed netlist and confirm all 9 corners, with Orion on hold repair if it is still negative. Nothing is waived.
2. **Equivalence check (eqy):** no result was in the inputs. RTL-to-netlist equivalence is unproven and remains blocking.
3. **Buffer count:** 172 timing-repair buffers and 80 hold buffers look large for this design. Area impact is unreviewed. Orion to review.
4. **Missing data:** no congestion or overflow figure in any report. CTS hold and setup slack for the min_* and max_* corners were not supplied. Neither is claimed clean.
5. **Bookkeeping:** the "changes" and "params" fields of iterations 1 and 2 in the PnR record disagree. The iteration table above follows the params. This should be corrected.
6. **DFT:** no scan or ATPG step exists in the current open flow, so there is no manufacturing coverage number. The plan proposes scan_en, scan_in, scan_out (and optional test_mode) pins. These are an interface change that needs your approval at G1 and a spec update. Scan-shift hold must be checked by PnR, not waived.
7. **Pending human review:** the PDK and library choice is a DEFAULT awaiting G1 review. The 30% default input delay on rx with no false path is also still open.

## 5. Quality and gate readiness
- Escaped defects: none reported in the inputs.
- Gate readiness: not ready to recommend. The route-stage facts are clean, but the hold discrepancy (item 1), the missing equivalence result (item 2) and the absent DFT coverage are open. Gate approval is yours; I make no claim that any check passed. The runtime runs the real checks.

## 6. Cost (run spend by agent, USD, from reports/division_cost.json)
Sienna 0.101799; Rex 0.021756; Orion 0.009525; Tick 0.00163; Calla 0.001303; Fabian 0.000198; Chronos 0.000155; Grid 0.000148; Volta 0.000057; Mason, Sentinel and Tess 0.0. No budget figure or weekly forecast is in the inputs, so I cannot state spend against budget. I will not guess one.

## 7. Decisions needed from you
1. **Hold discrepancy.** Options: (a) accept a Chronos STA re-run on the final routed netlist before any gate decision; (b) ask Orion for another hold-repair iteration. Recommendation: (a) first, then (b) only if a negative slack remains.
2. **Equivalence check.** Options: (a) require an eqy run before the gate; (b) defer it. Recommendation: (a), since unproven equivalence is blocking.
3. **Scan test pins (interface change).** Options: (a) approve new scan pins at G1; (b) share existing pins through a test_mode mux; (c) defer DFT beyond Phase 0. Recommendation: (c) for now. The open flow cannot insert scan or run ATPG, and I will not report DFT coverage without tool output.
4. **Buffer area review.** Options: (a) have Orion review the 172 and 80 buffer counts now; (b) review at sign-off. Recommendation: (a).
