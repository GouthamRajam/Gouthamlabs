# counter8 specification (v1)

## Request
8-bit up/down counter with synchronous reset, enable and load. Target: 100 MHz (10 ns period) on sky130A / sky130_fd_sc_hd, clean GDS.

## Standards
No external interface standard applies. Good-practice rules (reset, wrap, priority) come from the knowledge base.

## Clock and reset
- clk: 100 MHz, rising edge.
- rst_n: synchronous, active low.

## Interfaces
| Name | Dir | Width | Reset value / note |
|---|---|---|---|
| clk | in | 1 | |
| rst_n | in | 1 | sync active low |
| enable | in | 1 | |
| load | in | 1 | DEFAULT - needs G1 review |
| up_down | in | 1 | 1=up, 0=down. DEFAULT - needs G1 review |
| load_data | in | 8 | |
| count | out | 8 | reset_value 0 (8'h00) |

Port names are my choice (DEFAULT - needs G1 review).

## Requirements
| ID | Type | Statement | Acceptance |
|---|---|---|---|
| REQ-001 | reset | Synchronous active-low reset sets count to 8'h00 at the edge, overriding everything. | 256 start values x 16 input combinations, 0 mismatches; formal proof. |
| REQ-002 | reset | count resets to 8'h00; every state element is reset. | Reads 0x00 after every reset; no unreset register in netlist. |
| REQ-003 | reset | Reset is synchronous only. | Sub-cycle rst_n pulses between edges: no effect in 100 of 100 trials. |
| REQ-004 | functional | load=1 loads load_data, ignoring enable and up_down. | 1024 cases, 0 mismatches. |
| REQ-005 | functional | Up count when enable=1, load=0, up_down=1. | 255 start values, 0 mismatches. |
| REQ-006 | functional | Down count when enable=1, load=0, up_down=0. | 255 start values, 0 mismatches. |
| REQ-007 | functional | 0xFF + 1 wraps to 0x00 (DEFAULT - needs G1 review). | 256-step up sequence. |
| REQ-008 | functional | 0x00 - 1 wraps to 0xFF (DEFAULT - needs G1 review). | 256-step down sequence. |
| REQ-009 | functional | Hold when enable=0 and load=0. | 512 cases, 0 mismatches. |
| REQ-010 | functional | Priority reset > load > enable (DEFAULT - needs G1 review). | 32 combinations x 256 start values vs reference model. |
| REQ-011 | clock | Meets timing at 10 ns period. | STA setup and hold WNS >= 0 ns at the flow's corners. |
| REQ-012 | interface | count is registered; no combinational input-to-count path. | 0 such paths in STA; 0 count changes between edges. |
| REQ-013 | test | Random verification and clean layout. | At least 100000 random cycles with 0 mismatches; 0 DRC and 0 LVS violations. |

## Out of scope
Carry/overflow flags, saturating mode, asynchronous reset, multiple clock domains, step sizes other than 1, clock gating, DFT/scan, power and area targets.

## Open questions
1. Is load while enable=0 acceptable (default: yes)?
2. Is a carry/overflow flag needed (not included)?
3. Which sky130A release and STA corners apply?
