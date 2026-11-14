// -----------------------------------------------------------------------------
// Module : fifo_ctrl
// Purpose: Control block of sync_fifo: write/read pointers, occupancy count,
//          full/empty/almost_full decode, sticky overflow/underflow flags.
// Implements: REQ-001 REQ-002 REQ-004 REQ-005 REQ-006 REQ-007 REQ-008 REQ-009
//             REQ-010 REQ-011 REQ-012 REQ-013 REQ-014 REQ-015 REQ-016 REQ-017
// Assumptions: CNT_W == ADDR_W+1; DEPTH = 2**ADDR_W; ALMOST_FULL_TH fits in
//              CNT_W bits; synchronous active-low reset rst_n; single clock.
// -----------------------------------------------------------------------------
module fifo_ctrl #(
  parameter ADDR_W         = 4,
  parameter CNT_W          = 5,
  parameter ALMOST_FULL_TH = 12
) (
  input  wire               clk,
  input  wire               rst_n,
  input  wire               wr_en,
  input  wire               rd_en,
  output wire               wr_accept,
  output wire [ADDR_W-1:0]  wr_addr,
  output wire [ADDR_W-1:0]  rd_addr,
  output wire               full,
  output wire               empty,
  output wire               almost_full,
  output wire               overflow,
  output wire               underflow,
  output wire [CNT_W-1:0]   count
);

  localparam PTR_W = ADDR_W + 1;
  localparam [CNT_W-1:0] CNT_ONE  = {{(CNT_W-1){1'b0}}, 1'b1};
  localparam [CNT_W-1:0] CNT_ZERO = {CNT_W{1'b0}};
  localparam [CNT_W-1:0] DEPTH_C  = CNT_ONE << ADDR_W;
  localparam [CNT_W-1:0] AF_TH    = ALMOST_FULL_TH;
  localparam [PTR_W-1:0] PTR_ONE  = {{(PTR_W-1){1'b0}}, 1'b1};
  localparam [PTR_W-1:0] PTR_ZERO = {PTR_W{1'b0}};

  reg [PTR_W-1:0] wr_ptr_q, wr_ptr_d;
  reg [PTR_W-1:0] rd_ptr_q, rd_ptr_d;
  reg [CNT_W-1:0] count_q, count_d;
  reg             overflow_q, overflow_d;
  reg             underflow_q, underflow_d;

  wire full_w;
  wire empty_w;
  wire rd_accept_w;

  // Flags decoded from registered count only
  assign full_w      = (count_q == DEPTH_C);   // REQ-004
  assign empty_w     = (count_q == CNT_ZERO);  // REQ-005
  assign wr_accept   = wr_en & ~full_w;        // REQ-001 REQ-010 REQ-014
  assign rd_accept_w = rd_en & ~empty_w;       // REQ-002 REQ-011 REQ-015

  // Next-state logic
  always @(*) begin
    wr_ptr_d    = wr_ptr_q;
    rd_ptr_d    = rd_ptr_q;
    count_d     = count_q;
    overflow_d  = overflow_q;
    underflow_d = underflow_q;

    if (wr_accept) begin
      wr_ptr_d = wr_ptr_q + PTR_ONE;           // REQ-016
    end
    if (rd_accept_w) begin
      rd_ptr_d = rd_ptr_q + PTR_ONE;           // REQ-016
    end

    case ({wr_accept, rd_accept_w})
      2'b10:   count_d = count_q + CNT_ONE;    // REQ-001
      2'b01:   count_d = count_q - CNT_ONE;    // REQ-002
      2'b11:   count_d = count_q;              // REQ-013
      default: count_d = count_q;
    endcase

    if (wr_en & full_w) begin
      overflow_d = 1'b1;                       // REQ-010 REQ-012
    end
    if (rd_en & empty_w) begin
      underflow_d = 1'b1;                      // REQ-011 REQ-012
    end
  end

  // State registers, synchronous active-low reset with priority
  always @(posedge clk) begin
    if (!rst_n) begin                          // REQ-006 REQ-008
      wr_ptr_q    <= PTR_ZERO;
      rd_ptr_q    <= PTR_ZERO;
      count_q     <= CNT_ZERO;
      overflow_q  <= 1'b0;                     // REQ-007
      underflow_q <= 1'b0;                     // REQ-007
    end else begin
      wr_ptr_q    <= wr_ptr_d;
      rd_ptr_q    <= rd_ptr_d;
      count_q     <= count_d;
      overflow_q  <= overflow_d;
      underflow_q <= underflow_d;
    end
  end

  assign wr_addr     = wr_ptr_q[ADDR_W-1:0];
  assign rd_addr     = rd_ptr_q[ADDR_W-1:0];
  assign full        = full_w;                 // REQ-017
  assign empty       = empty_w;                // REQ-017
  assign almost_full = (count_q >= AF_TH);     // REQ-009
  assign overflow    = overflow_q;
  assign underflow   = underflow_q;
  assign count       = count_q;

endmodule
