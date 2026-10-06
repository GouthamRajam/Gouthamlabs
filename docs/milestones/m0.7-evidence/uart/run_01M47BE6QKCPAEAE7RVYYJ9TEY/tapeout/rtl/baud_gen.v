// -----------------------------------------------------------------------------
// Module : baud_gen
// Purpose: 16x baud tick generator. Emits a one-cycle tick16 pulse every
//          max(baud_div,1) clk cycles.
// Requirements: REQ-004 (sync reset of all state), REQ-006 (tick period),
//          REQ-007 (baud_div=27 gives 432 clk bit period), REQ-008 (0 -> 1)
// Assumptions:
//   - Synchronous active-low reset rst_n.
//   - tick16 is a combinational decode of registered state.
//   - If baud_div changes below the running count, the counter reloads at the
//     next edge (>= compare), so it cannot hang (REQ-023 support).
// -----------------------------------------------------------------------------
module baud_gen #(
    parameter DIV_W = 16
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [DIV_W-1:0] baud_div,
    output wire             tick16
);

    localparam [DIV_W-1:0] ZERO = {DIV_W{1'b0}};
    localparam [DIV_W-1:0] ONE  = {{(DIV_W-1){1'b0}}, 1'b1};

    reg  [DIV_W-1:0] cnt_q;
    wire [DIV_W-1:0] cnt_d;
    wire [DIV_W-1:0] limit_w;
    wire             wrap_w;

    // REQ-008: baud_div == 0 treated as 1 -> limit 0
    assign limit_w = (baud_div == ZERO) ? ZERO : (baud_div - ONE); // REQ-008

    // REQ-006: wrap when count reached (or exceeds, after baud_div change) limit
    assign wrap_w = (cnt_q >= limit_w); // REQ-006

    assign cnt_d = wrap_w ? ZERO : (cnt_q + ONE); // REQ-006

    assign tick16 = wrap_w; // REQ-006, REQ-007

    always @(posedge clk) begin
        if (!rst_n) begin
            cnt_q <= ZERO; // REQ-004
        end else begin
            cnt_q <= cnt_d;
        end
    end

endmodule
