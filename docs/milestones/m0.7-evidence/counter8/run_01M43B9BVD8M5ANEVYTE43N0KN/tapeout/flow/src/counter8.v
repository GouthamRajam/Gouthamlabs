// -----------------------------------------------------------------------------
// Module  : counter8
// Purpose : Top level of the 8-bit up/down counter with synchronous active-low
//           reset, enable and load. Structural only: wires inputs to the
//           control decoder (cnt_ctrl) and the datapath register (cnt_dp).
// Requirements implemented at this level:
//   REQ-011 single 100 MHz clock, all inputs synchronous to clk
//   REQ-012 count is driven directly by the datapath flops, no logic here
//   REQ-013 clean, verifiable top (reference-model compare, DRC/LVS later)
//   REQ-001..REQ-010 are implemented in cnt_ctrl / cnt_dp; this top only wires
//   rst_n, load, enable, up_down and load_data to them.
// Assumptions:
//   - All inputs are synchronous to clk (spec: no CDC, no synchronizers).
//   - Synchronous active-low reset rst_n is consumed by cnt_dp only.
// -----------------------------------------------------------------------------
module counter8 #(
    parameter W    = 8, // counter width (spec: 8)
    parameter OP_W = 2  // operation code width (arch: 2)
) (
    input  wire         clk,       // REQ-011 rising-edge clock
    input  wire         rst_n,     // REQ-001 synchronous active-low reset
    input  wire         enable,    // REQ-005 REQ-006 REQ-009
    input  wire         load,      // REQ-004
    input  wire         up_down,   // REQ-005 REQ-006 (1 = up, 0 = down)
    input  wire [W-1:0] load_data, // REQ-004
    output wire [W-1:0] count      // REQ-012 registered output
);

    // op: 00 hold, 01 up, 10 down, 11 load (from cnt_ctrl)
    wire [OP_W-1:0] op;

    // REQ-010 priority decode lives in cnt_ctrl
    cnt_ctrl u_cnt_ctrl (
        .load    (load),
        .enable  (enable),
        .up_down (up_down),
        .op      (op)
    );

    // REQ-001 REQ-002 REQ-012 register, reset and next-state mux in cnt_dp
    cnt_dp #(
        .W (W)
    ) u_cnt_dp (
        .clk       (clk),
        .rst_n     (rst_n),
        .op        (op),
        .load_data (load_data),
        .count     (count)
    );

endmodule
