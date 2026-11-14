# DFT Plan - sync_fifo (Phase 0)

Owner: Tess (DFT Agent). Design: sync_fifo, sky130A / sky130_fd_sc_hd, single clock clk at 100 MHz.
Inputs: spec/spec.yaml, arch/arch.yaml, reports/synth_tool.json.
Status: PLAN ONLY. The OpenLane 2 Classic flow used in Phase 0 has no scan-insertion or ATPG step,
so no scan was inserted, no test patterns were generated and no fault coverage was measured.
This document makes no claim of any coverage number.

## 1. Test strategy

- Manufacturing test target: structural test of all standard-cell logic (stuck-at, then transition-delay)
  using full mux-D scan plus ATPG, applied in Phase 1+ with a scan-capable flow.
- Design properties that help testability (from arch.yaml and spec.yaml):
  - One clock (clk) driven directly from a top-level pin; no clock gating, no generated clocks, no CDC
    (REQ-019, out_of_scope "Power-down or clock gating"). The test clock is the functional clock pin.
  - Reset rst_n is synchronous and active-low (REQ-006). It is a normal data input to the flops, so it
    needs no async-reset bypass or test-mode control; ATPG can treat it as an ordinary primary input.
  - No SRAM macro (REQ-020); the 16 x 32 storage is plain flops, so it is covered by scan like other logic.
  - No latches, tri-states or combinational loops are expected from the architecture (to be confirmed by
    the Phase 1 DRC step of the DFT tool, not assumed).
- Expected state elements (from arch.yaml, to be confirmed against the netlist): 512 storage flops
  (fifo_mem, no reset, write-enabled) + 5 wr_ptr + 5 rd_ptr + 5 count + 1 overflow + 1 underflow
  = 529 flops. The synthesised netlist reports 1960 cells and 26049.984 um^2 (pre-scan).
- Phase 0 complement: functional verification (scoreboard, assertions, REQ-021 scenarios) proves
  design intent only; it is not a manufacturing test and is not used as a coverage figure.

## 2. Scan approach

- Style: full scan, mux-D. Replace every flop with a scan flop from sky130_fd_sc_hd (the library
  contains scan flop cells of the sdfxtp family, which suit the non-reset storage and control flops
  here since the reset is synchronous and therefore lives in the D-logic). Exact cell choice to be
  confirmed against the library liberty file in Phase 1.
- Chains: one clock domain, one edge (rising), so all flops can be stitched into chains with no
  lock-up latches. Proposed: 4 balanced chains of about 132-133 flops each (529 total) if 4 scan-in /
  scan-out pin pairs are affordable; otherwise 1 chain of 529 flops (longer test time, fewer pins).
  Final chain count is a human decision tied to the pin budget (see Open issues).
- Chain ordering: placement-aware reordering after placement to limit scan wire length and hold risk.
- Shift and capture: scan_en selects shift; capture uses the functional clk. Shift at a reduced
  frequency (to be set in Phase 1) to limit shift power and IR drop; capture at speed (10 ns) for
  transition-delay test (launch-on-capture preferred, since scan_en is unlikely to be timed at speed).
- Timing impact to check in Phase 1: the scan mux adds delay to each flop D path. Current pre-layout
  setup slack at the worst corner (nom_ss_100C_1v60) is 0.306 ns, on the path from a high-fanout
  read-pointer flop (_3259_, fanout 128) through the 16:1 read mux to rd_data. That path ends at an
  output port, so the scan mux on the launching flop does not sit on it, but other flop-to-flop paths
  will lose some slack. scan_en is a high-fanout net (529 loads) and needs buffering and its own
  timing constraint. Hold on shift paths (Q to next SI) must be fixed after CTS.

## 3. Test pins

The current spec interface has no test pins. Proposed additions (require spec change and G1 approval;
not added by DFT):

| Pin | Dir | Width | Purpose |
|-----|-----|-------|---------|
| scan_en | in | 1 | Selects shift (1) or functional/capture (0). Tied/held at 0 in mission mode. |
| scan_in[N-1:0] | in | N (1 or 4) | Scan chain inputs. |
| scan_out[N-1:0] | out | N (1 or 4) | Scan chain outputs. |
| test_mode | in | 1 | Optional. Not strictly needed (no clock gating, no async reset, no macro); include only if a future block needs test-mode overrides. |

Pin-sharing option (to reduce pin count): scan_in can be shared with wr_data bits and scan_out with
rd_data bits through a scan_en-controlled output mux. This adds a mux on the rd_data output path,
which is already the worst setup path (0.306 ns slack at ss corner), so sharing on rd_data is NOT
recommended without re-timing. Dedicated pins are preferred. clk and rst_n are reused as test clock
and test reset.

## 4. Expected coverage method

- Fault models (Phase 1+): stuck-at and transition-delay (launch-on-capture). Targets are set by the
  Phase 1+ role definition; nothing is claimed here.
- Method: after scan insertion, run the DFT tool's design-rule checks (scan chain trace, clock and
  reset controllability), then ATPG, then fault simulation of the generated patterns on the
  gate-level (post-scan) netlist. Coverage is reported by the tool as detected faults over total
  faults, with untestable and ATPG-untestable faults listed separately and reviewed by a human; no
  fault class is dropped to raise the number.
- Pattern validation: simulate the ATPG patterns on the post-layout netlist with SDF timing (serial
  load for a sample, parallel load for the full set) before sign-off.
- Expected hard-to-test areas (qualitative only): the rd_data path when empty forces 0 (needs
  non-empty states, which scan reaches directly), the count/flag decode at boundary values (16, 12, 0),
  and the sticky flag set logic. Full scan gives direct control of count and pointers, so these are
  expected to be reachable; this is a design expectation, not a measured result.
- Phase 0 open-flow option: an open-source scan/ATPG tool could be evaluated later as a cross-check;
  none is integrated or run in this flow, so it gives no result here.

## 5. Memory test approach

- There is no SRAM macro (REQ-020): storage is 512 ordinary D-flops plus a 16:1 read mux and write
  decode. Therefore memory BIST is NOT needed; the storage is tested by scan and ATPG like any other
  logic (each storage flop is a scan cell; write-enable logic and read mux are covered by capture).
- Storage flops have no reset (REQ-006). Under scan this is not a problem: they are loaded by shift.
- Optional supplementary functional test (applies through normal pins, no extra hardware): a
  March-style sequence through the FIFO interface - fill 16 entries with a background (all-0s,
  all-1s, checkerboard 0x55555555 / 0xAAAAAAAA, walking address-in-data), read back in FIFO order,
  repeat with the inverse background, and cover pointer wrap. This checks the write decode, read mux
  and data bits end to end at speed. It is a supplement, not a replacement for scan.
- If a future version moves to an SRAM macro (currently out of scope), a memory BIST controller and
  macro bypass/wrapper would be required and this section must be redone.

## 6. Limitations of the open flow (Phase 0)

- OpenLane 2 Classic flow has no scan insertion, scan stitching, or ATPG step. No scan was inserted in
  this design; the netlist in reports/synth_tool.json is the functional (non-scan) netlist.
- No fault coverage, pattern count, or test time can be measured in Phase 0. Any coverage number for
  this design would be unsupported and none is given.
- Timing reports (setup slack 0.306 ns at nom_ss_100C_1v60, pre-layout, ideal clocks) are for the
  non-scan netlist. Scan muxes, scan_en buffering and scan-chain hold fixes will change area and
  timing; the effect is unknown until a scan-capable flow runs.
- No scan-mode STA (shift mode constraints, scan_en timing) is available.
- Test pins are not in the spec, so the current design is not externally testable by scan as built.
- Manufacturing test of the Phase 0 die relies only on functional test through the normal pins (for
  example the March-style sequence in section 5), whose structural fault coverage is unmeasured.
