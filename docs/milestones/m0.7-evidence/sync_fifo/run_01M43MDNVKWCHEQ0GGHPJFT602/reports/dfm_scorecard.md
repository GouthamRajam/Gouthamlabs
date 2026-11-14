# DFM Scorecard: sync_fifo (G3, A.15)

Source: reports/dfm_tool.json (KLayout 0.29.4, sha256:12a73199e47d). Severities are the tool's and are unchanged.

## Result

| High | Medium | Low |
|---|---|---|
| 0 | 3 | 6 |

Antenna worst case: 64.7% of limit (flag threshold 80%), no flag. Long parallel runs at min spacing: 0 on all layers. Isolated narrow lines: 0. Redundant-via opportunities: 0 on all via layers.

## Ranked items

| Rank | ID | Sev | Layer / check | Count | Why it matters | Fix | Owner |
|---|---|---|---|---|---|---|---|
| 1 | DFM-003 | medium | met1 line end | 304 | Line-end pullback or bridging at near-min gap. | Extend spacing or add end extension. | Orion |
| 2 | DFM-001 | medium | li density | 20 windows (max 0.5828 vs 0.6) | Little margin for CMP variation. | Spread routing in these windows. | Orion |
| 3 | DFM-005 | medium | met2 line end | 1 | Same litho risk as rank 1, single site. | Extend spacing or end extension. | Orion |
| 4 | DFM-004 | low | met1 near-limit | 47.3% of edges | Busiest layer, most sensitive to variation. | NDR wider/spaced on non-critical nets. | Orion |
| 5 | DFM-002 | low | li near-limit | 100% width, 2963 space edges | Min-width routing by construction. | NDR on non-critical nets. | Orion |
| 6 | DFM-006 | low | met2 near-limit | 84.7% | Mostly default-width edges; 2 near-min space. | NDR on non-critical nets. | Orion |
| 7 | DFM-007 | low | met3 near-limit | 81.0% (372 shapes) | Small population, no near-min space. | NDR on non-critical nets. | Orion |
| 8 | DFM-009 | low | met5 near-limit | 99.5% (4 shapes) | Negligible exposure. | None needed. | Orion |
| 9 | DFM-008 | low | met4 near-limit | 18.0% (11 shapes) | Lowest exposure. | None needed. | Orion |

## Actions for G3

1. Orion: review the 304 met1 line ends (DFM-003) and the one met2 line end (DFM-005); the tool lists 20 sample locations only.
2. Orion: decide whether to rebalance li routing in the 20 windows near the density limit (DFM-001).
3. Items 4 to 9 are informational and are not promoted to action.

## Caveats

- Ranking is engineering judgement from tool counts; no critical-area or litho simulation was run.
- Single-cut vias (mcon 8210, via 8080, via2 236, via3 16, via4 8) cannot be doubled because the tool found no room for redundant cuts.
- No check result here is a pass claim; the S2S runtime runs the real checks.
