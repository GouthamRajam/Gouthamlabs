# Low-power review: counter8 (RTL stage)

**Scope:** recommendations only. No RTL modified, no tools run, no power numbers claimed. Note: spec out_of_scope lists clock gating/low-power modes and power targets, so everything below needs a human decision.

## Where power goes (structural view)
- 8 flops on `clk` (clock pin and internal clock load toggle every cycle regardless of activity).
- Next-state mux: hold / +1 / -1 / load_data, driven by the 2-bit `op` from cnt_ctrl.
- Incrementer and decrementer both evaluate every cycle whatever `op` is selected.
- Counting up/down toggles bit0 every step, bit1 every 2nd, etc. (average about 2 toggles per step), so the count flops themselves toggle little.

## Recommendations

| # | Technique | Expected effect | Risk | Recommendation |
|---|-----------|-----------------|------|----------------|
| 1 | Clock gating with an ICG (sky130_fd_sc_hd__dlclkp), gate enable = `~rst_n \| load \| enable` | Removes clock toggling on 8 flops and the hold-mux recirculation during hold cycles. Benefit scales with the hold-cycle fraction; unquantified. At 8 flops the ICG area/clock-tree overhead may cancel the gain. | Reset is synchronous, so the gate must open when rst_n=0 (REQ-001/002/003). Adds clock-gating setup check, CTS complexity, and a skew risk. Verification must re-run. | Defer; only if the hold fraction is shown high and a power target is set. |
| 2 | Operand isolation on the +1 and -1 paths (AND-gate the adder inputs when op does not select them) | Reduces glitch/toggle in the unused adder. Likely small: a 8-bit inc/dec is about tens of cells, and isolation gates add their own switching and area. | Low functional risk, but timing on the isolation control; synthesis may already optimize. | Not recommended at this size. |
| 3 | Merge inc/dec into one adder (count + {7{~up_down}},1) | Fewer cells and less duplicate switching; gain is small. | Changes RTL structure; needs RTL owner agreement, equivalence check and full regression. It is an area/timing tradeoff, not primarily power. | Optional; RTL owner's decision. |
| 4 | Hold `load_data` inputs stable externally | None in RTL. | n/a | System-level note only. |

## Data needed to quantify
1. SAIF or VCD from a representative workload (not only the 100000-cycle random test): the fraction of cycles in hold (enable=0, load=0), load, up and down.
2. Per-flop clock-pin and per-net toggle counts; a post-synthesis netlist with the sky130 liberty for power estimation (e.g. OpenSTA/OpenROAD report_power with the activity file).
3. Baseline power report vs. gated version at the same activity, same corner, for a measured comparison.
4. Customer power target (none in spec).

## Verification impact if any change is adopted
Re-run the exhaustive reset/load/hold/priority checks (REQ-001..010), the formal reset property, the 100000-cycle reference compare, STA including clock-gating checks, and an equivalence check.

## Conclusion
No change is recommended now. The design is tiny, there is no power target, and gating is out of scope; the only candidate with real potential is #1, contingent on measured hold-cycle activity.
