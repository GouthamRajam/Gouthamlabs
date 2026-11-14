# Standards report: uart

## Verdict
No mandatory external interface standard applies to the digital UART core. Framing is a de facto convention.

## Standards and conventions
| Item | Applies? | Version / source | Notes |
|---|---|---|---|
| Asynchronous serial framing (8N1, parity, 16x oversampling) | De facto convention, not a formal standard | KB kb-pt-001; https://en.wikipedia.org/wiki/Universal_asynchronous_receiver-transmitter | Idle high; start bit 0; data LSB first; optional parity; stop bit 1. |
| TIA/EIA-232-F (RS-232) | Not applicable | TIA/EIA-232-F (1997), version to be re-verified | Electrical levels only; no on-chip drivers requested. |
| TIA-485-A (RS-485) | Not applicable | Version to be re-verified | Same reason. |
| SKY130 PDK, sky130_fd_sc_hd | Yes (technology) | KB kb-tk-003; https://skywater-pdk.readthedocs.io/en/main/ | Apache-2.0. PDK rules are checked by tools. |
| CDC practice | Yes (design rule) | KB kb-pt-002, kb-fc-003 | Rx input needs a 2-flop synchronizer. Record the crossing in arch.yaml cdc. |
| Register bus (APB/AXI/Wishbone) | Not specified | n/a | Open decision. |

## Rules that matter for design
- Frame: start (0), 8 data bits LSB first, optional parity (even/odd/none), stop (1). The line idles high.
- Parity: even parity makes the total count of 1s in data plus parity even; odd makes it odd.
- Rx: synchronize the async input with 2 flops; detect the falling edge of start; count 8 ticks to the mid-start-bit and re-verify it is still low (glitch rejection); then sample every 16 ticks.
- Framing error: stop bit sampled as 0. Parity error: received parity mismatch.
- Baud: 16x tick from a divisor register. For 50 MHz and 115200 baud, divisor of about 27 gives about 0.4% error (calculation, unverified by tools).
- Tolerance: the receiver must tolerate roughly +-2% or better combined baud mismatch over a 10-bit frame (typical rule of thumb).
- Tx and rx are in the same 50 MHz domain; the only crossing is the rx pin.

## Rules that matter for verification
- Directed tests: all parity modes, framing error injection, parity error injection, back-to-back frames, glitch on the start bit.
- Baud offset tests at +-2%, and divisor edge values (minimum, maximum).
- Loopback test of tx into rx.
- Reset behavior: tx line idles high after reset.
- Check rx synchronizer presence with CDC lint.

## Reusable IP recommendations (licences UNVERIFIED, confirm before use)
| Candidate | Typical licence | Note |
|---|---|---|
| OpenCores uart16550 | LGPL-style | 16550-compatible. Heavier than needed. Check the licence terms. |
| Alex Forencich verilog-uart | MIT | Small, simple. Good reference for a testbench. |
| lowRISC / OpenTitan uart | Apache-2.0 | Needs the TL-UL bus. Large dependency. |
| Write from scratch | Own | A UART this small is cheap to write and fully controlled. Recommended. |

Recommendation: write the core in-house and use a permissively licensed open UART only as a cross-check reference model.

## Licensing flags for the CEO
- Low risk overall. Avoid GPL/LGPL code in the RTL if the design is to be released under a permissive licence.
- SKY130 PDK is Apache-2.0.

## Caveats
No tools were run. Citations come from the knowledge base and memory; primary sources and licences need confirmation.
