# PPA review: counter8 (stage: architecture)

**Status:** hand estimate only. No tools were run and no past synthesis results exist, so the model is **uncalibrated**. Error bands are my judgement, not measured.

## Spec targets
- Clock: 100 MHz (10 ns). Area and power targets: none (out of scope in spec).

## Trade-off / estimate table
| Item | arch.yaml | Pascal estimate | Error band | Assumption |
|---|---|---|---|---|
| Flops | not stated | 8 (dfxtp_1, about 20 um2 each, about 160 um2) | +/-0 | count only state, 8 bits |
| Combinational cells | n/a | 60-110 | -10%/+60% | per-bit 4:1 mux, ripple +1/-1, sync reset gating |
| Total cells | 70 | 68-118 (central about 90) | -10%/+60% | no buffers/fillers/taps counted |
| Area (logic+flops) | none | about 600-1000 um2 | +/-50% | sky130_fd_sc_hd cell areas |
| Logic depth | 10 | 6-9 (about 12 if ctrl decode in series) | +/-3 levels | ripple carry 8 bits |
| Path delay (tt) | about 2 ns | about 2-4 ns incl. clk-to-Q and setup | +/-50% | 0.15-0.4 ns per level |
| Slack at 10 ns | 60% | about 60-80% tt; about 40-70% slow corner | +/-20 pts | corner not pinned |
| Dynamic power | none | about 10-60 uW | about 3x | 100 MHz, 1.8 V, 10-20% activity |
| Leakage | none | below 1 uW typical | about 3x | tt, 25 C |

## Findings
1. **Timing:** even with a 10-level pessimistic path, delay is far below 10 ns. REQ-011 looks low risk. Input-to-count combinational paths are none by construction (REQ-012), as count is a flop output.
2. **Cell count:** 70 is at or below the low end of my range. Not a failure (no area target), but do not use 70 as a baseline for later comparison.
3. **Depth:** 10 levels vs my 6-9. Unclear whether the control decode is included.
4. **Margin:** 60% is stated without derivation.
5. **Input hold/setup:** inputs are treated as synchronous; input delays are not given, so IO constraints need to be defined in the flow.

## Calibration
No past synthesis runs exist. After the first yosys+OpenSTA run, I will compare cell count, area and WNS against this table and tighten the bands.

## Recommendation
Proceed with the architecture; no option change needed. Update ppa_estimate to a range and confirm via synthesis and STA. I did not run any check; nothing here is claimed as passed.
