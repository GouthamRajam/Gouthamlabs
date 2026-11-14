// -----------------------------------------------------------------------------
// Module  : sync2
// Purpose : Multi-stage (default 2-flop) synchronizer for an asynchronous input.
// Reqs    : REQ-004 (synchronous reset, synchronizer flops reset to 1),
//           REQ-005 (single async crossing via 2-flop synchronizer)
// Assumptions: STAGES >= 2. Reset is synchronous active-low (rst_n).
// -----------------------------------------------------------------------------
module sync2 #(
    parameter STAGES = 2
) (
    input  wire clk,
    input  wire rst_n,
    input  wire d,
    output wire q
);

    reg [STAGES-1:0] sync_q;
    wire [STAGES-1:0] sync_d;

    // shift the async input through the chain
    assign sync_d = {sync_q[STAGES-2:0], d}; // REQ-005

    always @(posedge clk) begin
        if (!rst_n) begin
            sync_q <= {STAGES{1'b1}}; // REQ-004 reset to 1
        end else begin
            sync_q <= sync_d; // REQ-005
        end
    end

    assign q = sync_q[STAGES-1];

endmodule
