// ============================================================================
// Module : spi_shift
// Design : spi_master (S2S Phase 0)
// Purpose: TX/RX shift datapath. On start_acc it latches cpha, word_len and
//          the TX word left-aligned (8-bit: tx_data[7:0] in the top byte).
//          For cpha=0 the MSB is driven on start_acc (visible with cs_n fall);
//          later bits shift out on shift-edge strobes (trailing for cpha=0,
//          leading for cpha=1). Sample-edge strobes pass a 2-flop delay to
//          match the miso synchronizer latency and shift miso_s into the RX
//          register. On cs_rise_stb rx_data is loaded right-aligned and mosi
//          returns to 0.
// Requirements: REQ-001, REQ-002, REQ-003, REQ-004, REQ-007, REQ-011,
//               REQ-012, REQ-017, REQ-018, REQ-019
// Assumptions :
//   - edge_stb/lead_edge/cs_rise_stb come from spi_clkgen one cycle before
//     the SCK edge / cs_n rise they represent; N>=4 guarantees the last RX
//     capture happens before cs_rise_stb.
//   - miso_s is miso after the 2-flop synchronizer sync2.
// ============================================================================
module spi_shift #(
  parameter integer DATA_W = 16
) (
  input  wire              clk,
  input  wire              rst_n,
  input  wire              start_acc,
  input  wire [DATA_W-1:0] tx_data,
  input  wire              word_len,
  input  wire              cpha,
  input  wire              edge_stb,
  input  wire              lead_edge,
  input  wire              cs_rise_stb,
  input  wire              miso_s,
  output wire              mosi,
  output wire [DATA_W-1:0] rx_data
);

  // Constants
  localparam integer      BYTE_W    = DATA_W / 2;     // 8-bit word width
  localparam [BYTE_W-1:0] BYTE_ZERO = {BYTE_W{1'b0}};
  localparam [DATA_W-1:0] WORD_ZERO = {DATA_W{1'b0}};

  // State
  reg              cpha_q;     // latched cpha
  reg              wl_q;       // latched word_len
  reg [DATA_W-1:0] tx_sr_q;    // TX shift register, MSB first
  reg              mosi_q;     // MOSI output register
  reg [DATA_W-1:0] rx_sr_q;    // RX shift register, fills from LSB
  reg [DATA_W-1:0] rx_data_q;  // received word output register
  reg              smp_d1_q;   // sample strobe delayed 1 clk
  reg              smp_d2_q;   // sample strobe delayed 2 clk

  // TX word, left-aligned (REQ-004: 8-bit ignores tx_data[15:8])
  wire [DATA_W-1:0] tx_word = word_len ? tx_data : {tx_data[BYTE_W-1:0], BYTE_ZERO};

  // REQ-002: cpha=0 shift on trailing, sample on leading; cpha=1 the reverse
  wire shift_stb  = edge_stb & (lead_edge == cpha_q);
  wire sample_stb = edge_stb & (lead_edge != cpha_q);

  assign mosi    = mosi_q;
  assign rx_data = rx_data_q;

  always @(posedge clk) begin
    if (!rst_n) begin
      // REQ-018, REQ-019: synchronous reset, mosi=0, rx_data=0
      cpha_q    <= 1'b0;
      wl_q      <= 1'b0;
      tx_sr_q   <= WORD_ZERO;
      mosi_q    <= 1'b0;
      rx_sr_q   <= WORD_ZERO;
      rx_data_q <= WORD_ZERO;
      smp_d1_q  <= 1'b0;
      smp_d2_q  <= 1'b0;
    end else begin
      // REQ-011: delay the sample strobe by the synchronizer latency (2 clk)
      smp_d1_q <= sample_stb;
      smp_d2_q <= smp_d1_q;
      if (start_acc) begin
        // REQ-001, REQ-007: latch cpha, word_len, tx_data on the accepting edge
        cpha_q  <= cpha;
        wl_q    <= word_len;
        rx_sr_q <= WORD_ZERO;
        if (cpha) begin
          tx_sr_q <= tx_word;                                   // REQ-017: MSB at first leading edge
          mosi_q  <= 1'b0;
        end else begin
          tx_sr_q <= {tx_word[DATA_W-2:0], 1'b0};
          mosi_q  <= tx_word[DATA_W-1];                         // REQ-017: MSB with cs_n fall
        end
      end else begin
        if (!(shift_stb)) begin
          mosi_q  <= tx_sr_q[DATA_W-1];                         // REQ-003: MSB first
          tx_sr_q <= {tx_sr_q[DATA_W-2:0], 1'b0};
        end
        if (smp_d2_q) begin
          rx_sr_q <= {rx_sr_q[DATA_W-2:0], miso_s};             // REQ-003, REQ-011: MSB first
        end
        if (cs_rise_stb) begin
          mosi_q    <= 1'b0;                                    // REQ-017: mosi=0 after transfer
          rx_data_q <= wl_q ? rx_sr_q                           // REQ-012: update only at completion
                            : {BYTE_ZERO, rx_sr_q[BYTE_W-1:0]}; // REQ-004: upper byte 0
        end
      end
    end
  end

endmodule
