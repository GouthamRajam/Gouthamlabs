# Division 3 (Physical Implementation, Zone 3) report: spi_master, place_route stage

To: Human VP. From: Mason, Director of Physical Implementation. Every number below is copied from the stage reports; I ran no tool.

## Delivered
- Synthesis (iteration it1): 486 cells, 5574.096 um2.
- Floorplan: die 16277.3 um2, core 12061.6 um2, utilization 0.479564, power grid violations 0, 65 pins placed.
- Clock tree: 9 clock buffers, worst tree skew 0.007598 ns against a 2.0 ns target (the spec gives no skew target; the tool data does). 79 hold buffers and 178 timing-repair buffers were also inserted.
- Place and route (iteration 1 of the default budget of 8): route DRC errors 0, antenna violating nets 0, antenna violating pins 0, disconnected pins 0, max slew violations 0, max cap violations 0. Wirelength 13351 um, utilization after routing 0.559855.
- DFT: a plan only (dft/dft_plan.md). No scan insertion, ATPG or coverage was run, and no coverage is claimed.

## Timing (independent STA, 9 corners)
- Worst setup slack: 8.938063875351261 ns (max_ss_100C_1v60). All 9 corners are positive.
- Worst hold slack: 0.1040085824683123 ns (min_ff_n40C_1v95). All 9 corners are positive.
- Right after CTS, hold at nom_ff_n40C_1v95 was only 0.013112872270280695 ns. The final STA shows 0.10580808750866945 ns at that corner.

## At risk, why, and what I am doing
1. Hold margin is the thinnest number in the design (0.104 ns worst, final STA). Scan shift paths are flop-to-flop and the DFT plan calls them the likeliest hold violations. I will have hold checked on scan paths before any scan is accepted (a Phase 1 item).
2. Equivalence (RTL vs netlist) was not in the inputs. It is not proven and still blocks the synthesis stage.
3. Max fanout limit 10 is exceeded on 8 clock-tree buffer outputs (fanout 11 to 17). The tool data allows them under a clock-tree rule (limit 20). I have not accepted or waived anything; a human should confirm the rule is acceptable.
4. Gaps in the data: no congestion or overflow figure; post-CTS slack only for the 3 nominal corners; no clock transition data. The final REQ-021 decision belongs to the runtime checks.
5. The spec marks PDK/library choice, IO delays and area values as DEFAULT and needing G1 review.
6. The open flow has no scan insertion or ATPG step, so the delivered netlist and GDSII will contain no scan chains.

## Quality and gate readiness
- Escaped defects: none are reported in the inputs. First-pass yield: the PnR run needed 1 iteration and made no parameter changes.
- I do not approve gates. This report gives no gate verdict; the real checks and your sign-off decide it. The open items above (equivalence, hold margin, fanout rule) are what I would want closed first.

## Cost
- Spend by agent (USD): Sienna 0.050392, Orion 0.002589, Tick 0.000544, Grid 0.000153, Sentinel 0.0, Tess 0.0. Total 0.053678.
- No budget figure is in the inputs, so I cannot state spend vs budget or a weekly forecast.

## Decisions needed from you
1. Clock-tree fanout (8 nets at 11 to 17 vs limit 10). Options: (a) accept the clock-tree rule (limit 20); (b) require a re-run with a tighter fanout setting. Recommendation: (a), if you confirm the rule is acceptable, since the tool data marks these as allowed and no other pin violates.
2. DFT test pins (scan_en, scan_in, scan_out) change the spec interface. Options: (a) add new pins; (b) share existing pins, which adds a mux and affects REQ-022 IO timing; (c) defer to Phase 1. Recommendation: (c) for now, and decide at Phase 1 planning. This is a human decision.
3. DEFAULT spec values (PDK, IO delays, area) need G1 review. Recommendation: review them before relying on this stage's results.
