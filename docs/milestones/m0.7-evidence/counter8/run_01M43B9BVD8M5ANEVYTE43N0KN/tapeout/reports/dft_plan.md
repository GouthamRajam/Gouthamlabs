# DFT Plan: counter8 (Phase 0)

Status: plan only. No scan insertion, ATPG or fault simulation was run. No coverage number is claimed anywhere in this document.

Inputs: spec/spec.yaml, arch/arch.yaml, reports/synth_tool.json (pre-layout synthesis, 71 cells).

## 1. Test strategy

- The design has one clock (clk), one synchronous active-low reset (rst_n) and one state element: the 8-bit count register in cnt_dp. There is no memory, no analog block, no clock gating and no CDC (arch.yaml cdc is empty).
- Phase 0 manufacturing test relies on the functional verification already required by REQ-013 (random simulation against a reference model plus the directed tests of REQ-001..REQ-010). These show the RTL is right; they are not a manufacturing test.
- Planned manufacturing test (Phase 1+): full-scan structural test with stuck-at and transition-delay fault models, plus a short functional reset/load/count sanity sequence at the tester.
- Because count is directly observable at the output pins, a purely functional pattern set is possible as a fallback. The scan route is preferred because it controls and observes each flop independently of the counter's own sequencing.

## 2. Scan approach

- Style: single-chain, mux-based scan on the 8 count flops, using the sky130_fd_sc_hd scan flop cell (sdfxtp family) in place of dfxtp, one clock domain, rising-edge capture and shift.
- Chain order: count[0] to count[7], 8 flops, one chain.
- Reset interaction: reset is synchronous and sits in the next-state logic ahead of the flop D input. Scan insertion must place the scan mux at the flop, so shift data is not gated by rst_n. Whether rst_n must be held at 1 during shift is to be confirmed with the real tool; this is an assumption, not a result.
- Lockup latches are not needed (single clock domain, single edge).
- Not performed in Phase 0: the open OpenLane 2 Classic flow used here has no scan insertion step, so the netlist stays non-scan.
- Timing impact to be checked after insertion by the real STA flow: the scan mux adds delay to each D path and a hold-sensitive scan-in path. Reference only: the pre-layout report shows worst setup slack 1.57 ns (nom_ss_100C_1v60) and worst hold slack 0.077 ns (nom_ff_n40C_1v95) before any scan. The tight hold figure means scan-in to scan-out hops must be checked for hold and may need buffers.

## 3. Test pins

Scan needs pins the current spec does not define. Spec lists scan/DFT insertion as out of scope, so adding pins is a spec change requiring human (G1) approval. Proposed, not applied:

| Signal | Dir | Width | Proposal |
|---|---|---|---|
| scan_en | in | 1 | New port. 1 = shift, 0 = functional/capture. |
| scan_in | in | 1 | New port, or share load_data[0] in test mode to save a pad. |
| scan_out | out | 1 | Share count[7] (the chain tail Q), avoiding a new output. |
| clk | in | 1 | Existing, used as scan clock. |
| rst_n | in | 1 | Existing, used to initialise state; held inactive during shift (to be confirmed). |

Sharing functional pins keeps the port list close to the spec but must be reviewed against REQ-012 (count is a registered output) since the chain tail would also drive count. A dedicated scan_out is the cleaner alternative at the cost of one pad.

## 4. Expected coverage method

- Fault models: stuck-at on all cell pins, and transition-delay (launch-on-capture) faults.
- Method (Phase 1+, commercial ATPG): run ATPG on the scan netlist, then report test coverage and fault coverage separately, with the list of untestable, tied and blocked faults.
- Targets are set by the S2S master spec for Phase 1+; they are not restated here as results. Nothing in this document is a measured or predicted coverage value.
- Structural expectation only: the logic is small (71 cells, one chain of 8 flops), so no inherent untestable structure is anticipated, but this is unverified until a tool runs.
- Phase 0 evidence available instead: the functional random and directed simulation of REQ-013 and the formal property of REQ-001. These are not fault coverage.

## 5. Memory test approach

- The design contains no memories, so memory BIST is not applicable. count is a flop register, covered by scan.
- If a later revision adds memory, a memory BIST plan will be added then. No memory test is planned or claimed now.

## 6. Limitations of the open flow

- OpenLane 2 Classic has no scan insertion and no ATPG step. No scan netlist, pattern set or fault report can be produced in Phase 0.
- No open fault simulator or ATPG is integrated in this flow, so stuck-at and transition coverage cannot be measured here.
- Scan timing (setup and hold on shift and capture) cannot be checked until a scan netlist exists.
- Boundary scan and on-chip test compression are not planned for a design this small.
- Test pins are not in the spec or arch; they require a spec change and approval before any RTL or netlist change.
- Phase 1+ work (scan insertion, ATPG, coverage report, scan timing) is deferred and requires commercial tools, outside Phase 0 scope.
