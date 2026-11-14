# alu8 DFT Plan (Phase 0)

Design: alu8 (top `alu8_top`), sky130A / sky130_fd_sc_hd, single clock `clk` at 75 MHz, synchronous active-low reset `rst_n`.
Author: Tess (DFT Agent). Status: PLAN ONLY. No scan has been inserted and no ATPG or fault simulation has been run.
No fault-coverage number is claimed anywhere in this document.

Inputs used: spec/spec.yaml, arch/arch.yaml, reports/synth_tool.json (pre-layout synthesis of run it1: 182 cells, 1938.1 um^2).

## 1. Test strategy

- Structure (from arch.yaml): `alu8_core` is purely combinational (shared 9-bit adder, logic unit, barrel shifter, 8:1 result mux, flag logic). `alu8_regs` holds exactly 12 flops (8 result + 4 flags), all with synchronous active-low reset. No FSM, no memory, no CDC, one clock domain.
- Every input of the combinational core (a[7:0], b[7:0], op[2:0]) is a primary input, and every core output is captured by one of the 12 flops, which drive primary outputs directly. The design is therefore already fully controllable and observable at the pins with a one-cycle latency (REQ-009).
- Phase 0 production-test strategy:
  1. Functional (pin-based) structural test: apply a/b/op, clock once, compare result and flags. Because the only internal state is the 12-flop output register, each test cycle is a full-scan-equivalent capture of the core's response.
  2. Reset test: assert rst_n=0 for one clock with random a/b/op and check all outputs are 0 (REQ-010); then release and check normal operation (REQ-011).
  3. Hold test: op=CMP must leave result unchanged (REQ-006); this exercises the result-register load-enable path, which a pure combinational sweep would not observe.
  4. At-speed check: back-to-back operations at the 13.333 ns functional period on the tester to screen delay defects on the adder carry chain (the worst synthesized path is op[0] through the adder/mux into a result flop, per reports/synth_tool.json).
- The test pattern source is the verification reference model (the same independent model used for REQ-017), restricted to a compact vector set chosen by fault simulation (see section 4).

## 2. Scan approach

- Recommendation for Phase 0: no scan insertion. The open OpenLane 2 Classic flow used here has no scan-insertion or ATPG step, and with all 12 flops directly loadable from primary inputs in one cycle and directly observable at primary outputs, scan adds area and a mux delay to every D input without adding controllability or observability for stuck-at faults in the core.
- The one structure scan would improve is the register bank's own enable/reset logic and the hold path (res_we); these are covered by the reset and CMP-hold functional tests above.
- Phase 1 plan (if the design is embedded in a larger SoC, or if a scan-based test flow is mandated): replace the 12 `sky130_fd_sc_hd__dfxtp` flops with mux-D scan flops (`sky130_fd_sc_hd__sdfxtp` family), stitch one chain of 12 flops, scan-in from a dedicated pin, scan-out shared with or separate from an output, and run stuck-at and transition ATPG. Scan insertion and ATPG tool choice is a Phase 1 decision.
- Scan timing (Phase 1): shift at a slow test clock; capture at the functional period; check hold on the scan path after CTS.

## 3. Test pins

- Phase 0 (no scan): no dedicated test pins are added. Test uses only the spec I/O: clk, rst_n, a[7:0], b[7:0], op[2:0], result[7:0], flag_z, flag_c, flag_v, flag_n. This keeps the pinout exactly as specified (arch.yaml: top exposes exactly the spec I/O).
- Phase 1 (if scan is inserted), proposed additional pins, which require a spec change approved by a human:
  - `scan_en` (in): selects shift vs. capture.
  - `scan_in` (in): chain input.
  - `scan_out` (out): chain output (or multiplexed onto an existing output under scan_en).
  - Optional `test_mode` (in) if any test-only control is later needed.
- Adding any pin is outside the current spec and must go through the spec owner, not DFT.

## 4. Expected coverage method

- Fault models (Phase 1 targets per the S2S DFT role): stuck-at and transition faults on the gate-level netlist.
- Method planned:
  1. Take the synthesized gate-level netlist (reports/synth_tool.json `netlist`: 06-yosys-synthesis/alu8_top.nl.v of run it1, or the post-route netlist when available).
  2. Build the collapsed stuck-at fault list over all cell pins.
  3. Fault-simulate the functional vector set (exhaustive per-op sweeps from the verification testbench, plus reset and CMP-hold sequences) with a real fault simulator and record detected / undetected / untestable faults per fault class.
  4. Compact: keep only vectors that detect new faults, to get a short production pattern set.
  5. For transition faults, use launch-on-capture pairs of consecutive functional vectors at the 13.333 ns period.
- Coverage will be reported only from that real tool output. Until a fault simulator or ATPG tool has actually run on this netlist, the coverage is UNKNOWN and no number is stated.
- Expectation (qualitative, not a claim): because the core is combinational and fully controllable/observable through one register stage, undetected faults should be limited to redundant logic, if any; this must be confirmed by the tool.

## 5. Memory test approach

- The design contains no memories (no SRAM, register file, or ROM macro). The only storage is the 12-flop output register (arch.yaml alu8_regs).
- No memory BIST is planned or needed. The 12 flops are tested by the functional, reset and hold tests above (and by scan shift/capture if Phase 1 scan is added).
- If a later revision adds a memory macro, a march-test MBIST (for example March C-) with a BIST controller will be planned at that time.

## 6. Limitations of the open flow

- OpenLane 2 Classic (as used here) has no scan-insertion step and no ATPG step; no scan chains exist in this netlist.
- No fault simulation or ATPG has been run, so no fault coverage (stuck-at or transition) is known. The Phase 1 targets cannot be checked in Phase 0.
- No scan-timing, shift-power, or IDDQ analysis is possible in this flow.
- No test-pattern output (STIL/WGL) is produced; tester vectors would have to be derived from the simulation testbench by a separate, not-yet-built step.
- Open-source DFT tools (for example Fault from the OpenLane ecosystem) exist but are not part of this flow and have not been qualified for S2S; using them is a Phase 1 decision.
- STA observation (not a DFT result): reports/synth_tool.json applies a 4.0 ns input external delay, while spec.yaml open_questions assume 0 ns external delay. Tester timing for at-speed test depends on which budget is correct; flagged for the timing owner.
