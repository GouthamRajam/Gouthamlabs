# DFT Plan - spi_master (Phase 0)

Status: PLAN ONLY. No scan insertion, ATPG or fault simulation was run. The open OpenLane 2 Classic flow used here has no scan-insertion or ATPG step, so nothing in this document is a measured result. No coverage number is claimed.

Inputs: spec/spec.yaml (sha256:1ecb674e65ef), arch/arch.yaml (sha256:89436414e18b), reports/synth_tool.json (sha256:ecc34f7b1b0c).

## 1. Test strategy

- Design facts relied on (from spec and arch): one clock domain (clk), synchronous active-low reset rst_n, no clock gating, no SCK-clocked flops (REQ-020), all outputs registered, one asynchronous input (miso) passing the 2-flop synchronizer sync2. sck is a clk-domain register, not a clock.
- Synthesis report (reports/synth_tool.json) lists 486 cells and about 5574 um2 pre-layout; the arch estimate is about 105 flops. The flop count is an architecture estimate, not a measured figure, and must be re-counted from the netlist before any scan chain is sized.
- Post-silicon test is intended to be structural: full-scan stuck-at test plus at-speed transition test, followed by a small functional (SPI loopback) screening test.
- Phase 0 deliverable is this plan. The functional verification in REQ-024/REQ-025 (testbench, assertions, formal) is design verification, not manufacturing test, and is not counted as DFT.
- Manufacturing test items planned for later phases: (a) scan-chain integrity (shift/flush) test, (b) stuck-at ATPG patterns, (c) transition-fault ATPG patterns, (d) functional SPI loopback sanity test with an external slave or tester model, (e) IO/boundary checks by tester.
- Reset is synchronous, so during scan the reset must be held inactive (rst_n=1) and not used as a scan control; reset-state flops are initialized by shifting, not by reset.

## 2. Scan approach

- Style: single full-scan, muxed-flop (scan flop replaces each dfxtp with a scan-capable cell, e.g. sky130_fd_sc_hd__sdfxtp family, or a mux plus dfxtp), one scan chain, one clock (clk). Single clock domain and no gated clocks mean no clock-domain partitioning, no lock-up latches and no clock-gating bypass are needed in the current architecture.
- Chain count: one chain is the starting assumption because the design is small (about 105 flops, estimate). Chain count is revisited if tester pin count or shift time requires it.
- Scan flops: all flops in sync2, spi_ctrl, spi_clkgen, spi_shift, including the two sync2 flops and the 2-flop sample-strobe delay pipeline in spi_shift. No flop is planned to be excluded from the chain; any exclusion must be listed with a reason.
- Hold on the chain: shift paths are flop-to-flop with little logic and are the likeliest hold violations. Pre-layout hold slack in synth_tool.json is small in the ff corner (nom_ff_n40C_1v95), so the post-CTS hold check must include scan shift paths before scan is accepted. Scan timing checks (shift and capture) are a Phase 1 item.
- Constraints for scan mode: separate SDC mode with scan_en/test_mode constants set; setup/hold in shift mode on the same 50 MHz clock unless a slower shift clock is chosen later.
- Controllability concerns to handle at insertion time: (1) the clk_div compare/clamp logic (N = max(clk_div,4)) and the 6-bit tick counter are deep sequential structures, so scan is needed to reach their states; (2) miso input is asynchronous, so in test it is driven synchronously by the tester; (3) combinational path from start and busy to start_acc is covered by capture-cycle primary-input values.
- Primary inputs held or constrained in test: rst_n=1 during shift and capture, cs_mode/cs_force free (they are ordinary inputs).
- Flow integration: scan insertion would be done after synthesis and before placement (Yosys/OpenROAD-based or external tool in a later phase), followed by an equivalence check of scan-disabled function against the original netlist.

## 3. Test pins

The spec interface (spec/spec.yaml) has no scan or test pins. Adding pins changes the interface and needs a human decision (see open issues). Proposed minimum set for full scan:

| Signal | Dir | Purpose | Proposed source |
|---|---|---|---|
| scan_en | in | 1 = shift, 0 = capture/functional | new pin (preferred) |
| scan_in | in | chain serial input | new pin, or shared with an existing input (e.g. tx_data bit) via test_mode |
| scan_out | out | chain serial output | new pin, or shared with an existing output (e.g. rx_data bit) via test_mode |
| test_mode | in | optional, selects scan configuration | new pin, optional |
| clk | in | scan shift and capture clock (existing) | existing |
| rst_n | in | held 1 in scan (existing) | existing |

- Sharing functional pins for scan_in/scan_out saves pad count but adds a mux in a functional IO path and affects REQ-022 IO timing; this trade-off is for a human to decide.
- With a sync2 and registered outputs, scan_out should be taken from a flop output directly so the output path stays flop-to-pad.

## 4. Expected coverage method

- Fault models: single stuck-at (all cell pins) and transition (slow-to-rise/slow-to-fall) at-speed using launch-on-capture (LOC), since the design has a single clock and a scan_en that can be timed.
- Method: ATPG tool run on the scan-inserted netlist, with fault simulation giving test coverage and fault coverage, reported separately, with untestable/ATPG-untestable faults listed rather than excluded silently. Targets are those set in the Phase 1 gate (PHASE_GATES.md / Appendix A); they are not restated or assessed here.
- Phase 0: no coverage is computed and none is claimed. The only quantities available now are the flop and cell estimates above, which are not coverage.
- Expected coverage limiters to track: faults on rst_n logic (synchronous reset is data logic, so it is testable), sync2 flops (testable through scan), constant-tied or redundant logic such as clamp comparisons, and logic only observable through done/irq pulses (needs an observe path through capture).
- Evidence required later: ATPG tool log, fault list report, pattern count, and a scan-chain flush test on the real netlist. A coverage figure counts only when the real tool produced it.
- Complementary check: gate-level simulation of the generated patterns against the scan netlist (zero-delay and with SDF) to confirm no mismatches.

## 5. Memory test approach

- The design contains no memory macros and no inferred RAM/ROM: storage is the tx/rx shift registers (16 bits), counters and control flops, all of which are ordinary flops covered by scan.
- Therefore memory BIST is not applicable for spi_master. No MBIST controller is planned.
- If a later spec revision adds a FIFO or register file (currently out of scope per spec out_of_scope: FIFOs or queued transfers), a memory test approach (MBIST with march algorithm for macros, or scan for small flop arrays) must be added and this plan revised.

## 6. Limitations of the open flow

- The OpenLane 2 Classic flow used here has no scan-insertion step and no ATPG step. Scan cells are not inserted in the flow, so the delivered netlist and GDSII will not contain scan chains.
- No open-source ATPG/fault-simulation step is part of this flow, so there is no tool-produced stuck-at or transition coverage in Phase 0. Commercial ATPG is Phase 1+ and not used in Phase 0.
- Scan-aware STA modes (scan shift/capture SDC, scan hold checks) are not part of the flow's default constraints.
- Pre-layout figures in reports/synth_tool.json come from a synthesis-stage STA run (cell count 486, three corners) and say nothing about testability.
- Any later scan insertion with open tools would be an addition outside the current flow and needs a human decision and a DECISIONS.md entry.
- The plan is unverified by any tool run; all numbers quoted are from input files or architecture estimates.
