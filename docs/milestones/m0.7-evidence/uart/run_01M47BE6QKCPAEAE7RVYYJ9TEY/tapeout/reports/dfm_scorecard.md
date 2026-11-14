# DFM Scorecard - uart (G3 / A.15)

Source: reports/dfm_tool.json (KLayout 0.29.4, policy: near-limit 5%, density window 20 um, antenna flag 80%). Severities are the tool's and are unchanged.

**Totals:** high 0, medium 2, low 5. Items ranked: 7 of 7.

## Ranked items

| Rank | ID | Sev | Layer / check | Finding | Fix | Owner |
|---|---|---|---|---|---|---|
| 1 | DFM-003 | medium | met1 line end | 164 line ends at near-minimum end-to-line spacing; litho shortening can open or bridge | Add end extension / more end spacing | Orion |
| 2 | DFM-001 | medium | li density | 20 windows at up to 0.5999 vs 0.6 max; no CMP margin (global 0.427) | Spread li routing out of those windows | Orion |
| 3 | DFM-004 | low | met1 near-limit | 52.9% of edges near min (8174 width, 7973 space) | Non-default rules on non-critical nets, if room | Orion |
| 4 | DFM-002 | low | li near-limit | 100% near min width; expected for minimum-width li stubs | Monitor only | Orion |
| 5 | DFM-005 | low | met2 near-limit | 81.4%, width only, 0 spacing edges, 6.7% density | Optional widening | Orion |
| 6 | DFM-006 | low | met3 near-limit | 66.7% of only 1092 edges, no spacing edges | Monitor | Orion |
| 7 | DFM-007 | low | met4 near-limit | 21.8% of 44 edges | None | Orion |

## Other checks (from tool output)

- **Antenna:** worst case is 72.17% of the limit, below the 80% flag threshold. Margin exists but is not large.
- **Redundant vias:** the tool found 0 single-cut connections where a redundant via fits (mcon, via, via2, via3), so no via item is raised. Many connections are single-cut (e.g. via 3436 of 3691), but the tool reports no room for a second cut.
- **Long parallel runs at min spacing:** 0 on all layers.
- **Isolated narrow lines:** 0 on all layers.
- **Density:** met1 to met4 are well below the 0.6 max (met1 window max 0.371); only li is near the limit.

## Reviewer notes

- Act on DFM-003 and DFM-001 only. They are the real manufacturing exposure.
- The five low items are near-limit statistics. None has a confirmed defect, and they are not promoted.
- DFM-005 to DFM-007 have no hotspot locations in the tool output; ranking uses the layer statistics.
- This scorecard ranks tool output only. Pass/fail of the underlying checks is decided by the real tool runs, not by this document.
