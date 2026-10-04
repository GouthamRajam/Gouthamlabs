# DFM Scorecard: counter8 (G3)

Source: reports/dfm_tool.json, from KLayout 0.29.4 `dfm.py` (2.0 s; log `logs/dfm_klayout.log`). This is a ranking only. Severities are as reported by the tool and are unchanged.

**Totals:** 0 high, 2 medium, 5 low.

## Ranked items

| Rank | ID | Sev | Layer | Finding | Fix | Owner |
|---|---|---|---|---|---|---|
| 1 | DFM-003 | medium | met1 | 15 line ends at near-min spacing (bridge/open after litho pull-back). The last 2 sites look like a duplicate. | Increase end spacing or add end extension | Orion |
| 2 | DFM-001 | medium | li | 2 windows at 0.5565 vs 0.6 max density (92.8%): little CMP margin | Spread li routing in [10,10,30,30], [20,10,40,30] | Orion |
| 3 | DFM-004 | low | met1 | 52.7% near-limit, incl. 574 near-min-space edges | NDR spacing on non-critical nets | Orion |
| 4 | DFM-005 | low | met2 | 74.9% near-limit, width only, 0 near-space; layer very sparse | Optional widening | Orion |
| 5 | DFM-002 | low | li | 100% near-limit, mostly std-cell min-width li | No cell change | Orion |
| 6 | DFM-006 | low | met3 | 26.1% near-limit, width only | None required | Orion |
| 7 | DFM-007 | low | met4 | 0% near-limit | None | Orion |

## Other checks (from tool output, no item raised)

- **Antenna:** worst is 19.31% of the limit; the flag threshold is 80%.
- **Long parallel runs at min space:** 0 on all layers.
- **Isolated narrow lines:** 0 on all layers.
- **Single-cut vias:** mcon 308/308, via 275/350, via2 23/83, via3 0/60. redundant_via_fits = 0 on every layer, so no fix is actionable now.
- **Max density:** every window is below 90% of max except the two li windows in DFM-001.

## Open questions for a human

1. **DFM-003 count:** the two hotspots near (15.14, 44.16) are probably one feature counted twice.
2. **Near-limit metric:** confirm how the near-limit fraction is defined. For met1, 0.5271 does not equal the edge-count ratio of 0.409, so it is probably length-weighted.
3. **Minimum density:** windows reach 0.0 density on several layers, and no min-density item was raised. Decide whether block-level fill or a min-density check is in scope.

## Verdict for G3

No high-severity DFM risk was found. The two medium items, DFM-003 and DFM-001, are the only ones worth a layout iteration. All low items are informational.
