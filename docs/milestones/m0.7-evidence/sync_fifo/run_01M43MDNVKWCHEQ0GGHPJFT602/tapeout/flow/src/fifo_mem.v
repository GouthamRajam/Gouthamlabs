// -----------------------------------------------------------------------------
// Module : fifo_mem
// Purpose: Flop-based FIFO storage, DEPTH x DATA_W, one write port (synchronous)
//          and one combinational read port (first-word-fall-through).
// Requirements implemented: REQ-003, REQ-006, REQ-020
//          (REQ-018 read path is a function of registered state only)
// Assumptions:
//   - wr_en is the already-qualified accept signal from fifo_ctrl.
//   - empty is decoded from the registered count in fifo_ctrl.
//   - DEPTH == 2**ADDR_W.
//   - Storage array has no reset (REQ-006); unobservable because rd_data is
//     forced to 0 while empty and entries are written before being read.
// -----------------------------------------------------------------------------
module fifo_mem #(
    parameter DATA_W = 32,
    parameter ADDR_W = 4,
    parameter DEPTH  = 16
) (
    input  wire              clk,
    input  wire              wr_en,
    input  wire [ADDR_W-1:0] wr_addr,
    input  wire [DATA_W-1:0] wr_data,
    input  wire [ADDR_W-1:0] rd_addr,
    input  wire              empty,
    output wire [DATA_W-1:0] rd_data
);

    // REQ-020: flop-based storage, no SRAM macro
    reg [DATA_W-1:0] mem_q [0:DEPTH-1];

    // REQ-006: storage array intentionally has no reset
    always @(posedge clk) begin
        if (wr_en) begin
            mem_q[wr_addr] <= wr_data; // REQ-020
        end
    end

    // REQ-003: first-word-fall-through read, forced to 0 when empty
    assign rd_data = empty ? {DATA_W{1'b0}} : mem_q[rd_addr]; // REQ-003

endmodule
