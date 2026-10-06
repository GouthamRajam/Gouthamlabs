// -----------------------------------------------------------------------------
// Module   : sync2
// Purpose  : 2-flop synchronizer for a single asynchronous input (miso) into
//            the clk domain. Only CDC in the spi_master design.
// Implements: REQ-011 (miso passes a 2-flop synchronizer),
//             REQ-020 (single clock domain, only async crossing is miso),
//             REQ-018 (synchronous active-low reset, flops reset to 0).
// Assumptions:
//   - Both flops are reset synchronously to 0 by rst_n (arch.yaml: "reset to 0").
//   - Latency from d to q is 2 clk cycles; spi_shift compensates for it.
//   - No logic between the two flops (max_logic_depth: 2).
// -----------------------------------------------------------------------------
module sync2 (
    input  wire clk,
    input  wire rst_n,
    input  wire d,
    output wire q
);

    reg meta_q;  // first stage, may go metastable
    reg sync_q;  // second stage, synchronized output

    // REQ-011, REQ-020: two back-to-back flops on clk, no logic in between
    always @(posedge clk) begin
        if (!rst_n) begin            // REQ-018: synchronous active-low reset
            meta_q <= 1'b0;
            sync_q <= 1'b0;
        end else begin
            meta_q <= d;
            sync_q <= meta_q;
        end
    end

    assign q = sync_q;  // REQ-011

endmodule
