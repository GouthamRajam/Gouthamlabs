// -----------------------------------------------------------------------------
// Module   : alu8_top
// Design   : alu8 (8-bit synchronous ALU, registered result and N/Z/C/V flags)
// Purpose  : Structural top. Exposes exactly the spec I/O and connects the
//            combinational datapath (alu8_core) to the 12-flop output
//            register bank (alu8_regs). No logic of its own.
// Implements: REQ-009, REQ-014, REQ-015, REQ-017
// Assumptions:
//   - Single clock domain clk, rising edge; no asynchronous inputs, so no
//     synchronizers are needed (arch.yaml cdc: []).
//   - Data width W is fixed at 8 by the spec; it is a localparam (not a
//     parameter) so the top-level port list always matches the spec.
//   - alu8_core and alu8_regs are written by other RTL engineers with the
//     parameter W and the port names given in arch.yaml.
// -----------------------------------------------------------------------------
module alu8_top (
    input  wire       clk,     // REQ-014: single clock, rising edge
    input  wire       rst_n,   // synchronous active-low reset
    input  wire [7:0] a,       // operand A
    input  wire [7:0] b,       // operand B (b[2:0] = shift amount)
    input  wire [2:0] op,      // operation select
    output wire [7:0] result,  // REQ-009: registered result
    output wire       flag_z,  // REQ-009: registered zero flag
    output wire       flag_c,  // REQ-009: registered carry flag
    output wire       flag_v,  // REQ-009: registered overflow flag
    output wire       flag_n   // REQ-009: registered negative flag
);

    localparam integer W = 8;  // data width (spec: 8-bit operands/result)

    // Combinational next-state signals from datapath to register bank
    wire [W-1:0] res_next;
    wire         z_next;
    wire         c_next;
    wire         v_next;
    wire         n_next;
    wire         res_we;

    // REQ-015: one operation per clock; purely combinational datapath,
    // no wait states. REQ-017: datapath isolated for exhaustive sweep.
    alu8_core #(
        .W (W)
    ) u_core (
        .a        (a),
        .b        (b),
        .op       (op),
        .res_next (res_next),
        .z_next   (z_next),
        .c_next   (c_next),
        .v_next   (v_next),
        .n_next   (n_next),
        .res_we   (res_we)
    );

    // REQ-009: all outputs come straight from flops (latency exactly 1).
    // REQ-014: register bank clocked only by clk.
    alu8_regs #(
        .W (W)
    ) u_regs (
        .clk      (clk),
        .rst_n    (rst_n),
        .res_next (res_next),
        .z_next   (z_next),
        .c_next   (c_next),
        .v_next   (v_next),
        .n_next   (n_next),
        .res_we   (res_we),
        .result   (result),
        .flag_z   (flag_z),
        .flag_c   (flag_c),
        .flag_v   (flag_v),
        .flag_n   (flag_n)
    );

endmodule
