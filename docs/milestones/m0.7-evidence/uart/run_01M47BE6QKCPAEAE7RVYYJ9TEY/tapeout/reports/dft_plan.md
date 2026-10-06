# DFT Plan - uart (Phase 0)

Status: PLAN ONLY. No scan insertion, ATPG or fault simulation was run. This document states no coverage number and no measured result.

Inputs: spec/spec.yaml (sha256:bfb6ccb242e6), arch/arch.yaml (sha256:24cfc0bf006b), reports/synth_tool.json (sha256:9ecc6fad35c2).

## 1. Test strategy

- Design is a single-clock (clk, 50 MHz), synchronous-reset (rst_n, active low) UART: modules baud_gen, uart_tx, uart_rx, sync2 under uart_top. The only asynchronous input is rx, through the 2-flop sync2.
- Post-manufacture test is structural: full-scan stuck-at as the primary method, transition-fault (at-speed, launch-on-capture) as the secondary method, plus a functional loopback screen using the existing ports.
- Functional screen (works with no DFT hardware): tx looped to rx externally, all parity modes, baud_div edge values (0, 1, 65535), and check rx_data, frame_err and parity_err. This is a go/no-go sanity test, not a fault-coverage method.
- The design has no analog blocks, no embedded memory and no hard macros. Everything is standard-cell logic and D flip-flops (sky130_fd_sc_hd).
- Structural targets for Phase 1+ come from the role definition (stuck-at and transition coverage targets); they are not restated or claimed here.

## 2. Scan approach

- Style: single full-scan, mux-D scan flops, all state flops replaced by scan equivalents (baud counter, tx and rx FSM state, tick dividers, shift registers, parity flops, sync2 flops, output registers).
- Chain count: one chain as the starting point. The flop count is not stated in the inputs (synthesis reports 736 cells total, flop count not given), so chain length is to be determined from the synthesized netlist at insertion time. A second chain is only justified if pin count or test time demands it.
- Clocking: single clock domain, so no clock-domain partitioning or lock-up latches are needed between domains. Scan shift and capture both use clk.
- Reset in test: rst_n is synchronous, so it is functional logic into the D path, not an async set/reset. During scan shift rst_n must be held inactive (high) so reset does not corrupt shifted data. ATPG constraint: rst_n = 1 during shift and capture, except for a dedicated reset-initialization pattern.
- sync2: both flops reset to 1 (REQ-004) and are scannable; rx is an uncontrolled asynchronous input, so in capture the rx pin must be constrained to a fixed value or treated as unobservable/uncontrolled by ATPG. The sync2 chain gets no special CDC handling beyond this.
- Inputs baud_div[15:0] and parity_mode[1:0] are primary inputs held at ATPG-chosen values per pattern; tx_data and tx_valid likewise.
- Insertion step (Phase 1+): scan stitching in the netlist after synthesis, followed by scan-aware STA. Scan adds a mux on each D path and extra hold-sensitive shift paths. Existing pre-layout hold slack is thin at the fast corner (nom_ff_n40C_1v95 hold worst slack reported as slightly negative in reports/synth_tool.json), so scan-shift hold must be checked and fixed by the PnR agent, not waived.
- Design rules to check before insertion: no latches, no combinational feedback, no internally generated clocks, no gated clocks. The architecture lists none of these, but this is stated from arch.yaml and must be verified on the netlist.

## 3. Test pins

Proposed scan/test pins (not in spec/spec.yaml today; adding them is an interface change that needs human approval at G1 and a spec update):

| Pin | Dir | Function |
|---|---|---|
| scan_en | in | 1 = shift, 0 = capture/functional |
| scan_in | in | serial data into chain 1 |
| scan_out | out | serial data out of chain 1 |
| test_mode | in (optional) | holds rx constrained and disables functional-only behaviors during test |

- To limit pin overhead, scan_in may be shared with an existing input (for example tx_data[0]) and scan_out with an existing output (for example rx_data[0]) through a test_mode-controlled mux. This is an option, not a decision.
- Existing pins used in test: clk (shift/capture clock), rst_n (held high during scan), the functional inputs as ATPG-controllable primary inputs, and all outputs as observation points.
- No JTAG/TAP is planned for Phase 0; the design has no boundary-scan requirement in the spec.

## 4. Expected coverage method

- Fault models: single stuck-at (all scannable cell pins) and transition delay faults (launch-on-capture, at-speed with clk).
- Method: ATPG on the scan-inserted netlist, then fault simulation of the final pattern set; coverage is computed by the tool as detected faults over total faults, reported separately for test coverage and fault coverage, with undetected/untestable fault classes listed.
- Expected sources of lost coverage, to be reviewed rather than excluded: rx (uncontrolled async input), the constant-0 overrun_err output (REQ-022, tied low, its faults are structurally untestable or redundant), the reserved parity_mode=3 fold (redundant logic possible), and the baud_div==0 clamp.
- No waivers or excluded faults will be added to raise a number. Any fault class declared untestable must be justified in the report and approved by a human.
- Open-flow substitute available now: S2S simulation-based verification and mutation testing evaluate the functional testbench, not manufacturing fault coverage. They must not be reported as DFT coverage.
- Result reporting (Phase 1+): coverage numbers will be quoted only from tool output of the ATPG run, with the tool name, version and log path.

## 5. Memory test approach

- The design contains no memories (no SRAM, ROM, register file, or macro). The architecture has only flip-flop registers, which are covered by the scan chain.
- Memory BIST is therefore not applicable in this design, and no BIST controller is planned.
- If a future version adds a memory (for example a FIFO larger than one entry, currently out of scope), a memory test approach (BIST with a march algorithm, or scan-based test through wrapper logic) will be added to this plan and needs a plan revision.

## 6. Limitations of the open flow

- The OpenLane 2 Classic flow used here has no scan insertion step and no ATPG step. Nothing in the flow produces scan-stitched netlists, test patterns or fault coverage.
- Consequently this deliverable is a plan only: no scan was inserted, no patterns were generated, and no stuck-at or transition coverage was measured.
- Open-source ATPG/DFT tools exist (for example Yosys-based scan experiments and the Fault project), but they are not part of the current flow and have not been qualified here; using them would need a decision recorded in docs/DECISIONS.md.
- Phase 0 uses only open-source tools and open SKY130; commercial scan insertion and ATPG are Phase 1+ and are not used here.
- Scan-aware timing (shift and capture paths, at-speed capture) cannot be checked with the current flow's constraints; these need a Phase 1+ scan-aware STA setup.
- The SKY130 library includes scan flop cells (sky130_fd_sc_hd__sdf*), but whether the flow's synthesis maps to them was not checked in this task and is not assumed.
