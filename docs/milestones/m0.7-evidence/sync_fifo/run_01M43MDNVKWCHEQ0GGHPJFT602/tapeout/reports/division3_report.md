# Division 3 (Zone 3) report to the VP - sync_fifo, place_route stage

Author: Mason, Director of Physical Implementation. Every number below is taken from the stage reports. I ran no tool; the S2S runtime runs the real checks, and I approve no gate.

## 1. Delivered
Synthesis, floorplan, CTS and place-and-route have each produced a report for sync_fifo. The report files carry no dates, so I cannot say what was delivered "yesterday" or against which dated milestone.
- Synthesis: 1960 cells, 26049.984 um2.
- CTS: 74 clock buffers, worst tree skew 0.062196 ns (target 1.0 ns).
- P&R, iteration 10 (final): no problems listed. Route DRC errors 0, antenna nets/pins 0/0, disconnected pins 0, max slew/cap/fanout violations 0/0/0. Wirelength 65447 um, placed utilization 0.380144.
- Final parameters: FP_CORE_UTIL 30, PL_TARGET_DENSITY_PCT 65, MAX_FANOUT_CONSTRAINT 6, CTS_SINK_CLUSTERING_SIZE 9, GRT_ANTENNA_ITERS 15, GRT_ANTENNA_MARGIN 30.

## 2. Timing (iteration 10, 9 corners)
| Item | Value |
|---|---|
| Worst setup slack | 0.24286306986222908 ns (max_ss_100C_1v60) |
| Best setup slack | 4.671610341905403 ns (min_ff_n40C_1v95) |
| Worst hold slack | 0.13843709903600443 ns (min_ff_n40C_1v95) |
| Best hold slack | 1.0087289067333807 ns (max_ss_100C_1v60) |
| nom_tt setup / hold | 3.446966587504062 / 0.3735724058056228 ns |
| nom_ss setup / hold | 0.37514481471987016 / 1.0023965274887343 ns |
| nom_ff setup / hold | 4.603886291398691 / 0.14113616230750536 ns |

Setup and hold slack are positive in all 9 corners in the tool data.

## 3. At risk, and why
1. Thin setup margin. The worst setup slack fell from 1.1149406158340678 ns (iteration 6) to 0.24286306986222908 ns (iteration 10) as utilization dropped and buffering grew. The worst path is the read path, flop to rd_data. Pre-layout, one flop with fanout 128 drove the 16:1 read mux (clock-to-Q 3.645585 ns of 6.444210 ns). The output delay of 3.000 ns is an unreviewed DEFAULT and sets this margin directly.
2. Thin hold margin at the ff corners: 0.13843709903600443 ns (min_ff) and 0.14113616230750536 ns (nom_ff).
3. Unexplained buffer counts. CTS inserted 512 hold buffers and 697 timing repair buffers against 74 clock buffers. The data gives no cause. Chronos and Orion are to confirm whether this is expected.
4. Fragile clean result. Antenna violations did not fall steadily across iterations 6 to 9, and two parameters changed together at iteration 8. The clean antenna and fanout result at iteration 10 may be sensitive to parameters. Iterations 9 and 10 exceeded the default 8-iteration budget and were recorded as CEO decisions (iteration 10 is CEO decision D1, experiment PNR-SYNCFIFO-0011).
5. Stale floorplan report. floorplan_report.json describes the first floorplan (45% utilization choice, floorplan utilization 0.469972, die 66020.3 um2, core 57585.2 um2, 0 power grid violations, 79 pins), not the final FP_CORE_UTIL 30 run. A floorplan report for the final run is needed.
6. Missing data. No global-routing congestion figure was provided. Synthesis gave no cell-class breakdown, macro count, flop count or TNS. Post-CTS hold is reported only for the 3 nominal corners. The equivalence-check (eqy) result was not provided to me.
7. Placement failed twice with GPL-0302 (iterations 1 and 5, same parameters as the runs that completed). The data does not show how those failures were resolved.

What I am doing: asking Chronos and Orion to explain the buffer counts and to re-check timing and hold margins after the final route; asking for a floorplan report for the final run. Neither is done yet.

## 4. Quality and gate readiness
- Tool data for iteration 10 lists no problems. I do not call any check passed: the runtime decides pass or fail.
- Gate readiness: not claimed. I do not approve gates. Open items 1 to 6 above go with this design to the gate review.
- DFT (Tess): plan only. The Phase 0 flow has no scan insertion or ATPG, so no scan was inserted and no fault coverage exists. The spec has no test pins, so the die is not externally testable by scan as built. Expected state elements: 529 flops. The proposed scan pins need a spec change and G1 approval.
- Escaped defects: none reported in the inputs.

## 5. Cost
Run spend by agent (USD): Orion 0.057283, Tick 0.036656, Grid 0.010223, Sienna 0.00139, Sentinel 0.0, Tess 0.0. Total 0.105552 USD (sum of these figures). No budget or weekly forecast is in the inputs, so I cannot state spend against budget or give a forecast.

## 6. Decisions needed from the human
1. Output delay of 3.000 ns (DEFAULT, G1 review). Options: (a) confirm 3.000 ns; (b) set it from the real consumer of the FIFO. Recommendation: (b) before sign-off, because it sets the 0.24286306986222908 ns setup margin.
2. DFT test pins. Options: (a) accept no scan in Phase 0 and rely on functional test; (b) approve a spec change adding scan_en, scan_in and scan_out (1 or 4 chains). Recommendation: (a) for Phase 0, and put (b) on the Phase 1 agenda. This is your decision to make.
3. Hold and repair buffers (512 hold, 697 repair). Options: (a) accept pending Chronos and Orion review; (b) block until explained. Recommendation: (b) before any gate, because the cause is unknown.
