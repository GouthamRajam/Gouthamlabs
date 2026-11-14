# uart specification (version 1)

## Restatement
A UART transmitter and receiver in a single 50 MHz clock domain on SKY130 (sky130A, sky130_fd_sc_hd; PDK choice is DEFAULT - needs G1 review). It supports 8N1 and 8E1/8O1 framing (parity none/even/odd), a 16-bit baud divisor input, 16x oversampling receive with majority of 3 center samples, and framing and parity error flags.

## Clocks and reset
- clk: 50 MHz, single domain.
- rst_n: synchronous, active low. Resets every state element.
- The only asynchronous crossing is rx, via a 2-flop synchronizer (reset to 1).

## Interfaces
| Name | Dir | Width | Reset value | Notes |
|---|---|---|---|---|
| clk | in | 1 | - | 50 MHz |
| rst_n | in | 1 | - | sync, active low |
| tx | out | 1 | 1 | idle high |
| rx | in | 1 | - | async, synchronized |
| tx_data | in | 8 | - | sampled on tx_valid & tx_ready |
| tx_valid | in | 1 | - | |
| tx_ready | out | 1 | 1 | |
| rx_data | out | 8 | 0 | valid with rx_valid |
| rx_valid | out | 1 | 0 | 1-cycle pulse |
| baud_div | in | 16 | - | clk cycles per 16x tick; 0 treated as 1 |
| parity_mode | in | 2 | - | 0 none, 1 even, 2 odd, 3 reserved (as none) |
| frame_err | out | 1 | 0 | pulse with rx_valid |
| parity_err | out | 1 | 0 | pulse with rx_valid |
| overrun_err | out | 1 | 0 | RECOMMENDED - default on; constant 0 in this version |

## Requirements
| ID | Type | Statement | Acceptance |
|---|---|---|---|
| REQ-001 | functional | Transmit one 8-bit word per handshake, LSB first, start 0, optional parity, stop 1. | Matches reference model for 10,000 random words per parity mode. |
| REQ-002 | functional | 16x oversampling, majority of 3 center samples. | Correct reception at +-2% baud offset, 10,000 words per mode. |
| REQ-003 | reset | After reset: tx=1, tx_ready=1, rx_data=0, rx_valid=0, all error flags 0. | Directed test and formal property. |
| REQ-004 | reset | Synchronous active-low reset on every state element. | Mid-frame reset returns outputs to reset values in 1 cycle; lint shows every register reset. |
| REQ-005 | clock | Single 50 MHz clock; only crossing is rx with 2-flop synchronizer. | CDC lint: 1 crossing, 2 stages; setup slack >= 0 at 20 ns. |
| REQ-006 | functional | One 16x tick per baud_div cycles. | Bit period = 16*baud_div cycles for baud_div 1, 2, 27, 65535. |
| REQ-007 | performance | baud_div=27 gives <= 0.5% error vs 115200. | Computed error <= 0.5%; 432 cycles per bit in simulation. |
| REQ-008 | functional | baud_div=0 treated as 1 (RECOMMENDED). | Bit period 16 cycles. |
| REQ-009 | functional | Parity bit after data bit 7; even/odd/none. | Frame length 10 or 11 bits and parity correct for all 256 values. |
| REQ-010 | functional | parity_mode 3 behaves as none (RECOMMENDED). | 1,000 frames as 10-bit, parity_err=0. |
| REQ-011 | interface | tx_ready low from accept until stop bit end. | Low for exactly one frame time in 1,000 transfers. |
| REQ-012 | functional | tx_valid while tx_ready=0 is ignored. | Frame unchanged in 1,000 trials. |
| REQ-013 | functional | Back-to-back frames with gap <= 1 bit period. | 1,000 frames, stop = 16*baud_div cycles. |
| REQ-014 | functional | Start-bit glitch rejection at tick 8. | 0 rx_valid in 1,000 glitch trials. |
| REQ-015 | functional | Sample each bit 16 ticks apart, LSB first. | 10,000 words correct per mode. |
| REQ-016 | interface | rx_valid is a 1-cycle pulse. | Exactly one pulse per frame in 10,000 frames. |
| REQ-017 | functional | frame_err=1 if stop sampled 0. | 1,000 injected: always 1; 10,000 clean: always 0. |
| REQ-018 | functional | parity_err on parity mismatch; 0 in modes 0 and 3. | 1,000 injected per mode: always 1; clean: 0. |
| REQ-019 | functional | Break (rx held low) gives one frame_err event. | 100 bit periods low gives exactly 1 rx_valid with frame_err=1. |
| REQ-020 | performance | Tolerate +-2% baud mismatch. | 0 errors in 10,000 frames at +-2% for baud_div 1, 27, 255. |
| REQ-021 | functional | Back-to-back frames received without loss. | 1,000 loopback frames, 0 errors. |
| REQ-022 | functional | overrun_err constant 0 (no read handshake). | 0 in every cycle over 10,000 frames. |
| REQ-023 | functional | Mid-frame change of baud_div/parity_mode: content undefined, no hang. | Returns to idle in bounded time; later frames correct in 1,000 trials. |
| REQ-024 | test | Verification set: loopback, parity modes, error injection, glitch, +-2%, divisor edges. | 0 failures; coverage >= 95%. |

## Out of scope
- Flow control (RTS/CTS, XON/XOFF)
- FIFOs larger than 1 entry
- Register bus (APB/AXI/Wishbone)
- RS-232 / RS-485 electrical drivers
- Stop-bit counts other than 1, data widths other than 8, mark/space parity
- Interrupts, DMA, auto-baud

## Open questions
1. Is a register bus required instead of plain ports?
2. Should a frame with framing error still assert rx_valid (assumed yes)?
