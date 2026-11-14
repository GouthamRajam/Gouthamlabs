# DFM Scorecard - alu8 (alu8_top) - G3

Source: reports/dfm_tool.json (KLayout 0.29.4, SKY130A rules, policy: near-limit 5%, density window 20 um / step 10 um, density flag at 90% of max, antenna flag at 80%). Severities are as set by the tool rules and are unchanged.

## Overall
**0 high, 2 medium, 5 low.** No high-severity yield risk. Two medium items are worth fixing before tape-out if schedule allows; the low items are informational.

## Ranked items (by real yield impact)
| Rank | ID | Sev | Layer / check | Finding | Owner |
|---|---|---|---|---|---|
| 1 | DFM-003 | medium | met1 line end | 35 line ends at near-min spacing (open/bridge litho risk) | Orion |
| 2 | DFM-001 | medium | li density | 7 windows near max; worst 0.569 vs 0.60 (94.9%) | Orion |
| 3 | DFM-004 | low | met1 near-limit | 51.6% of edges (3843/8940) near min W/S | Orion |
| 4 | DFM-005 | low | met2 near-limit | 81.1% (1254 edges) near min width; none near min space | Orion |
| 5 | DFM-002 | low | li near-limit | 100% near min width (cell-intrinsic); 257 near min space | Orion |
| 6 | DFM-006 | low | met3 near-limit | 62.2% (148 edges); layer 2.9% dense | Orion |
| 7 | DFM-007 | low | met4 near-limit | 36.7% (8 edges) | Orion |

## Recommended actions
1. **DFM-003:** open the 35 met1 line-end gaps to >= 0.147 um or add end extensions (hotspots listed in tool report).
2. **DFM-001:** reduce li density in the central 20-70 um windows below 0.54.
3. Low items: apply non-default wider rules to non-critical met1/met2 nets only if routing margin allows. Not required for G3.

## Checks with no finding (from tool output)
- Long parallel runs at min spacing: 0 on all layers.
- Isolated narrow lines: 0 on all layers.
- Antenna: worst net at 37.33% of limit (flag threshold 80%).
- Max density: met1-met5 windows well below 0.6 (worst met4 0.206).
- Single-cut vias: mcon 852, via 875, via2 79, via3 8 single-cut connections; tool found **0** locations where a redundant cut fits, so no actionable item.

## Open points for human review
- Tool reports density_window_min = 0.0 on every layer; minimum-density compliance is not assessed in this report.
- redundant_via_fits = 0 on every via layer; confirm this reflects layout reality, not a check limitation.

Raw log: var/artifacts/runs/run_01M44DR7XRWAQ9XY53AG8SRJCM/logs/dfm_klayout.log
