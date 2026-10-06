// ============================================================================
// Module : spi_clkgen
// Design : spi_master (S2S Phase 0)
// Purpose: SCK and transfer-timing generator. On start_acc it latches the
//          clamped half period N = max(clk_div,4) (stored as N-1) and word_len,
//          clears the half-period counter and the tick counter and starts
//          running. While running, a tick fires every N clk cycles; tick j
//          (0..2W+1) decodes edge_stb (j<2W), cs_rise_stb (j=2W) and end_stb
//          (j=2W+1). All strobes are combinational decodes one cycle ahead of
//          the registers that consume them. sck is a clk-domain register.
// Requirements: REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007,
//               REQ-009, REQ-010, REQ-014, REQ-016, REQ-018, REQ-019, REQ-020
// Assumptions :
//   - Cycle 0 = edge where start_acc=1; tick j occurs in cycle (j+1)N, so SCK
//     edge k is visible in cycle 1+(k+1)N.
//   - cpol is captured into sck_q at start_acc; while running sck only toggles
//     on edge_stb, so live cpol changes cannot affect a transfer.
//   - On end_stb sck_q reloads live cpol, visible in the first busy=0 cycle.
//   - edge_cnt counts every tick (2W+2 after a transfer completes).
// ============================================================================
module spi_clkgen #(
  parameter integer DIV_W = 16,
  parameter integer CNT_W = 6
) (
  input  wire             clk,
  input  wire             rst_n,
  input  wire             start_acc,
  input  wire [DIV_W-1:0] clk_div,
  input  wire             word_len,
  input  wire             cpol,
  output wire             sck,
  output wire             edge_stb,
  output wire             lead_edge,
  output wire             cs_rise_stb,
  output wire             end_stb,
  output wire [CNT_W-1:0] edge_cnt
);

  // Constants
  localparam [DIV_W-1:0] DIV_MIN   = 4;   // minimum half period N (REQ-006)
  localparam [DIV_W-1:0] DIV_ONE   = 1;
  localparam [DIV_W-1:0] DIV_ZERO  = 0;
  localparam [CNT_W-1:0] EDGES_W8  = 16;  // 2W SCK edges for W=8  (REQ-003)
  localparam [CNT_W-1:0] EDGES_W16 = 32;  // 2W SCK edges for W=16 (REQ-003)
  localparam [CNT_W-1:0] CNT_ONE   = 1;
  localparam [CNT_W-1:0] CNT_ZERO  = 0;

  // State
  reg [DIV_W-1:0] nm1_q;       // latched N-1
  reg [DIV_W-1:0] hp_cnt_q;    // half-period counter 0..N-1
  reg [CNT_W-1:0] tick_cnt_q;  // tick counter j
  reg             wl_q;        // latched word_len
  reg             running_q;   // transfer timing active
  reg             sck_q;       // SCK output register

  // Clamp and latch value
  wire [DIV_W-1:0] n_eff = (clk_div < DIV_MIN) ? DIV_MIN : clk_div;  // REQ-005, REQ-006
  wire [DIV_W-1:0] nm1_d = n_eff - DIV_ONE;

  // Tick and strobe decode
  wire             tick       = running_q & (hp_cnt_q == nm1_q);       // REQ-005: every N clk
  wire [CNT_W-1:0] edges_w    = wl_q ? EDGES_W16 : EDGES_W8;           // REQ-003: 2W
  wire [CNT_W-1:0] edges_w_p1 = edges_w + CNT_ONE;                     // 2W+1

  assign edge_stb    = tick & (tick_cnt_q < edges_w);                  // REQ-003, REQ-009
  assign lead_edge   = ~tick_cnt_q[0];                                 // REQ-002: even j = leading
  assign cs_rise_stb = tick & (tick_cnt_q == edges_w);                 // REQ-009, REQ-012
  assign end_stb     = tick & (tick_cnt_q == edges_w_p1);              // REQ-014, REQ-016
  assign sck         = sck_q;
  assign edge_cnt    = tick_cnt_q;

  always @(posedge clk) begin
    if (!rst_n) begin
      // REQ-018, REQ-019: synchronous reset aborts timing, sck=0
      nm1_q      <= DIV_ZERO;
      hp_cnt_q   <= DIV_ZERO;
      tick_cnt_q <= CNT_ZERO;
      wl_q       <= 1'b0;
      running_q  <= 1'b0;
      sck_q      <= 1'b0;
    end else if (start_acc) begin
      // REQ-001: latch N, word_len and cpol on the accepting edge
      nm1_q      <= nm1_d;
      hp_cnt_q   <= DIV_ZERO;
      tick_cnt_q <= CNT_ZERO;
      wl_q       <= word_len;
      running_q  <= 1'b0;
      sck_q      <= cpol;                                              // REQ-002: idle level cpol
    end else if (running_q) begin
      if (tick) begin
        hp_cnt_q   <= DIV_ZERO;
        tick_cnt_q <= tick_cnt_q + CNT_ONE;
      end else begin
        hp_cnt_q   <= hp_cnt_q + DIV_ONE;
      end
      if (end_stb) begin
        running_q  <= 1'b0;                                            // REQ-014
      end
      if (edge_stb) begin
        sck_q      <= ~sck_q;                                          // REQ-002, REQ-005: 50% duty
      end else if (end_stb) begin
        sck_q      <= cpol;                                            // REQ-007: idle follows cpol
      end
    end else begin
      sck_q      <= cpol;                                              // REQ-007, REQ-018: 1 clk latency
    end
  end

endmodule
