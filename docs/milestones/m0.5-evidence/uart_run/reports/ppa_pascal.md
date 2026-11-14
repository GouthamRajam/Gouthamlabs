# PPA review: uart (stage: architecture)

**Status:** analytical estimate only. No tool was run and no past synthesis results exist, so there is no calibration. Everything below is unverified.

## 1. Calibration statement
No synthesis data from earlier runs is available. Error band for this model:
- Cell count: -25% / +25%
- Logic depth: +/-4 levels
- Power: within a factor of ~3 (order of magnitude only)

First Yosys/OpenSTA results should replace these numbers.

## 2. Area (cells) bottom-up
| Module | Flops | Comb. cells (est.) | Total (est.) | Notes |
|---|---|---|---|---|
| sync2 | 2 | 2 | 4 | reset-to-1 logic |
| baud_gen | 16 (+16 if changed-div detect) | 60-110 | 76-140 | counter, zero clamp, compare/reload |
| uart_tx | ~3 FSM + 4 tick + 8 shift + 1 parity + 1 tx = 17 | 60-90 | 77-107 | mux for load/shift, parity xor |
| uart_rx | ~3 FSM + 4 tick + 8 shift + 3 sample + 4 outputs/flags ≈ 22 | 80-120 | 100-140 | majority, parity check, WAIT_HIGH |
| uart_top | 0 | ~0-5 | ~5 | constant 0 tie for overrun_err |
| **Total** | ~57-73 | ~200-330 | **~260-400 base, up to ~520 with changed-div detect** | |

arch.yaml: 420 cells. This sits inside my range, so it is plausible. Area at ~20 um2 per flop and ~5-6 um2 avg per gate is roughly 2,500-3,500 um2 of cell area, before utilization.

## 3. Logic depth at 50 MHz
| Path | arch.yaml depth | My estimate | Comment |
|---|---|---|---|
| baud_gen | 9 | 6-14 | Depends on the 16-bit compare/reload; 16-bit equality ~5 levels, magnitude compare ~8-12 |
| uart_tx | 8 | 5-9 | FSM next-state plus shift mux plus parity |
| uart_rx | 9 | 6-10 | majority-of-3 plus FSM plus counter compare |
| Input paths (tx_valid, tx_data, baud_div, parity_mode) | n/a | +input delay | no input delay constraints are given in the spec |

Timing budget: 20 ns period. At 0.15-0.25 ns/level (typical corner, hd, fanout included) plus ~0.5 ns clk-Q/setup, even 14 levels is about 3-4 ns. Real slack is likely 80%+ of period, higher than the stated 35%. The 50 MHz target looks easily met. Slack margin figure is conservative but unsupported.

## 4. Power assumptions
Not in arch.yaml and no spec target.
| Item | Assumption | Estimate |
|---|---|---|
| Flops | ~65, clock pin cap ~2 fF each, 1.8 V, 50 MHz | clock tree ~ 10-20 uW |
| Logic | ~300 cells, activity 10% | ~10-30 uW |
| Leakage (tt, 25C) | ~ 1 nW/cell order | < 1 uW |
| **Total** | | **~20-60 uW dynamic (factor ~3 uncertainty)** |

The baud counter dominates toggling at small baud_div. Real activity needs simulation (VCD/SAIF).

## 5. Trade-off table
| Option | Cells (est.) | Depth (est.) | Meets REQ-005 timing | Risk |
|---|---|---|---|---|
| A. arch.yaml as written (compare/reload on change) | ~420 | 9-14 | Yes (large margin) | depth claim of 9 may be violated for baud_gen |
| B. Down-counter, reload on zero, clamp registered | ~330-380 | 6-8 | Yes | REQ-023 recovery relies on reload at zero, which can take up to 65535 cycles after a change; REQ-023 allows 11*16*65535 so this is acceptable |
| C. B plus changed-baud_div detect | ~400-480 | 6-9 | Yes | extra 16 flops for little benefit |

Recommendation (for the architect to decide): option B appears sufficient for REQ-023, since the acceptance window is 11*16*65535 cycles, and it avoids the wide magnitude comparator. This is a suggestion; I am not changing arch.yaml.

## 6. Conclusions
- 420 cells: plausible, no change proposed.
- Depth 9: plausible for tx/rx, at risk for baud_gen depending on the implementation.
- 35% slack: unsupported, likely very conservative.
- No option fails the spec; no escalation is needed.

All figures to be re-checked against the first synthesis and STA run.
