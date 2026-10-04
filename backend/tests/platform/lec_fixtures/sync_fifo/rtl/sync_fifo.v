// -----------------------------------------------------------------------------
// Module : sync_fifo
// Purpose: Top-level wrapper of a single-clock 16 x 32 synchronous FIFO.
//          Wires fifo_ctrl (pointers, count, flags) to fifo_mem (flop array,
//          first-word-fall-through read). No logic other than connections.
// Requirements implemented here: REQ-018, REQ-019, REQ-021
//          (all other REQs are implemented in fifo_ctrl / fifo_mem)
// Assumptions:
//   - Single clock clk, synchronous active-low reset rst_n, no CDC.
//   - Sub-modules follow the port lists in arch.yaml.
// -----------------------------------------------------------------------------
module sync_fifo #(
    parameter DATA_W         = 32,
    parameter ADDR_W         = 4,
    parameter CNT_W          = 5,
    parameter DEPTH          = 16,
    parameter ALMOST_FULL_TH = 12
) (
    input  wire              clk,         // REQ-019 single clock
    input  wire              rst_n,
    input  wire              wr_en,
    input  wire [DATA_W-1:0] wr_data,
    input  wire              rd_en,
    output wire [DATA_W-1:0] rd_data,
    output wire              full,
    output wire              empty,
    output wire              almost_full,
    output wire              overflow,
    output wire              underflow,
    output wire [CNT_W-1:0]  count
);

    wire              wr_accept_w;
    wire [ADDR_W-1:0] wr_addr_w;
    wire [ADDR_W-1:0] rd_addr_w;
    wire              empty_w;

    assign empty = empty_w;

    // Control: pointers, count, flags (REQ-001..017 implemented inside)
    fifo_ctrl #(
        .ADDR_W         (ADDR_W),
        .CNT_W          (CNT_W),
        .ALMOST_FULL_TH (ALMOST_FULL_TH)
    ) u_fifo_ctrl (
        .clk         (clk),
        .rst_n       (rst_n),
        .wr_en       (wr_en),
        .rd_en       (rd_en),
        .wr_accept   (wr_accept_w),
        .wr_addr     (wr_addr_w),
        .rd_addr     (rd_addr_w),
        .full        (full),
        .empty       (empty_w),
        .almost_full (almost_full),
        .overflow    (overflow),
        .underflow   (underflow),
        .count       (count)
    );

    // Storage: flop array, FWFT read, forced 0 when empty (REQ-003, REQ-020)
    // REQ-018: rd_data depends only on registered state (rd_addr, storage, empty)
    fifo_mem #(
        .DATA_W (DATA_W),
        .ADDR_W (ADDR_W),
        .DEPTH  (DEPTH)
    ) u_fifo_mem (
        .clk     (clk),
        .wr_en   (wr_accept_w),
        .wr_addr (wr_addr_w),
        .wr_data (wr_data),
        .rd_addr (rd_addr_w),
        .empty   (empty_w),
        .rd_data (rd_data)
    );

endmodule
