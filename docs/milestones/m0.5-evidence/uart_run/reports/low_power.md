# Low-power review: uart (stage rtl)

Scope: recommendations only. No RTL changed. No tools run, so **no power numbers are claimed**.

## Summary table

| # | Recommendation | Module | Expected effect | Risk | Verdict |
|---|---|---|---|---|---|
| 1 | Reduce baud_gen per-cycle activity: use equality compare for the normal wrap and keep a reload guard for baud_div changes; or skip the `baud_div-1` subtract by precomputing/registering the limit | baud_gen | Probably the largest saving: the 16-bit counter, adder, subtractor and >= comparator toggle every cycle | Medium: must keep REQ-006/007/008 exact and REQ-023 no-hang behaviour | Evaluate after activity data |
| 2 | Enable-based clock gating (ICG) of tick-gated state in uart_tx/uart_rx (tick_cnt, shreg, bit_idx) | uart_tx, uart_rx | Small; the enable is mostly low, but only about 15-20 flops per block | Medium: CTS/STA/CDC impact, ICG overhead may exceed gain | Not recommended unless data shows benefit |
| 3 | Hold or isolate baud_div changes from the comparator when no traffic is active | baud_gen | Depends on how often the baud_div input toggles | High: may alter REQ-023 behaviour | Needs human decision |
| 4 | Operand isolation of parity XOR trees | uart_tx, uart_rx | Negligible (8-input XOR) | Low | Not worth it |
| 5 | Power domains / power gating | all | Not applicable to design this small; sky130 flow support unconfirmed | High | Not recommended |

## Observations from the RTL

- baud_gen: `limit_w` (zero check plus 16-bit decrement), `wrap_w` (16-bit >=), `cnt_d` (16-bit increment plus mux) are all evaluated every clock. With the default behaviour the counter is always running, even when no frame is being sent or received, so this is the dominant continuous dynamic power. The tick output is combinational from `wrap_w`, so it can glitch.
- uart_tx: when idle the FSM holds, but `tx_q <= 1` is re-assigned each cycle, which causes no toggle. Registers update only on tick16 or accept; activity is low.
- uart_rx: `prev_q` and the 2-flop synchronizer toggle only with rx. The `samp_q` and `tick_cnt_q` update only on tick16 when not idle. In IDLE, `tick_cnt_q`, `bit_idx_q` and `perr_q` are written each cycle with constants, so no real toggling.
- sync2: must stay as is (CDC); do not gate.
- rx_data_q only changes at frame completion, which is already good for power.

## Data needed to quantify

1. SAIF/VCD from RTL or gate-level simulation of the testbench loopback at baud_div 1, 27, 65535, parity modes 0, 1, 2, plus long idle periods.
2. Realistic activity on baud_div, parity_mode, tx_data inputs (static versus toggling).
3. A synthesized netlist for sky130_fd_sc_hd and a power report (leakage, internal, switching) per module, before and after each change.
4. Idle fraction of the intended application.

## Verification needed if any change is accepted

- RTL owner approval; full regression (REQ-006/007/008/023/024), formal equivalence against the current RTL, STA at 20 ns, CDC lint, and coverage re-run.

## Not done

No tool runs; nothing here has been confirmed to pass.
