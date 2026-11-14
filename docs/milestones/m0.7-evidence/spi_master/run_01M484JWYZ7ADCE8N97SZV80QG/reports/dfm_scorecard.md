# DFM Scorecard - spi_master (G3, A.15)

Source: reports/dfm_tool.json (KLayout 0.29.4, policy: near-limit 5%, window 20 um, step 10 um). Severities are as reported by the tool and unchanged.

**Summary:** high 0, medium 2, low 5. Antenna worst case is 50.97% of limit (flag threshold 80%): no antenna concern. Long parallel min-space runs: 0. Isolated narrow lines: 0.

## Ranked items

| Rank | ID | Sev | Layer / check | Why it matters | Fix | Owner |
|---|---|---|---|---|---|---|
| 1 | DFM-003 | medium | met1 line ends (103) | 103 met1 line ends sit at near-minimum end-to-line spacing; litho line-end pull-back can open or bridge them, the only item with a direct defect mechanism. | Extend spacing at these line ends or add an end extension; re-run DRC and DFM after the change. | Orion |
| 2 | DFM-001 | medium | li density (20 windows) | 20 li windows are within 10% of the 0.6 max density (worst window 0.583), leaving little margin for CMP variation. | Spread li routing in the flagged windows. | Orion |
| 3 | DFM-004 | low | met1 near-limit (53.6%) | 53.6% of met1 edge length is near limit, including 4667 near-min-space edges, which raises sensitivity to bridging under process variation. | Use non-default wider/spaced rules on non-critical met1 nets. | Orion |
| 4 | DFM-002 | low | li near-limit (100% edges) | All li edges are near min width (inherent to minimum-width li local routing) but only 582 are near min space, so the real yield exposure is modest. | Use non-default wider/spaced rules on non-critical li nets where area allows. | Orion |
| 5 | DFM-005 | low | met2 near-limit (81.2%) | 81.2% of met2 edges are near min width, but there are no near-min-space edges and density is low (max window 0.151), so bridging risk is small. | Use non-default wider rules on non-critical met2 nets. | Orion |
| 6 | DFM-006 | low | met3 near-limit (59.7%) | 59.7% of met3 edges are near min width on only 107 shapes with very low density; negligible yield impact. | Use non-default wider rules on non-critical met3 nets if convenient. | Orion |
| 7 | DFM-007 | low | met4 near-limit (24.6%) | 24.6% of met4 edges are near min width on only 6 shapes; negligible yield impact. | No action needed beyond optional wider rules on non-critical met4 nets. | Orion |

## Notes
- Redundant vias: the tool found 0 places where a redundant via fits (mcon 2211, via 2110, via2 83, via3 8 single-cut connections), so no action is available.
- Low items are ranked below both medium items and are not promoted; DFM-005 to DFM-007 are informational.
- Max density across metal layers is 0.583 (li); met1-met4 are well below 0.6.
- Locations: see hotspot lists in reports/dfm_tool.json (DFM-005 to DFM-007 have none).
- Raw log: logs/dfm_klayout.log in the run directory.
