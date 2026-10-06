// -----------------------------------------------------------------------------
// Module  : uart_tx
// Purpose : UART transmitter. FSM IDLE/START/DATA/PARITY/STOP, LSB first,
//           1 start bit, 8 data bits, optional parity, 1 stop bit.
//           Each bit lasts 16 frame-aligned ticks (dtick).
// REQs    : REQ-001 REQ-003 REQ-004 REQ-009 REQ-010 REQ-011 REQ-012
//           REQ-013 REQ-023 REQ-006
// Assumptions: tick16 is a one-cycle periodic pulse from baud_gen; parity_mode
//           is latched at accept so a mid-frame change cannot hang the FSM.
//           The start bit is driven in the cycle after accept. dtick is the
//           shared tick16 delayed by the phase (cycles since last tick16 at
//           accept), so dtick occurs at accept + j*baud_div cycles and each
//           bit is exactly 16*baud_div clk cycles.
// -----------------------------------------------------------------------------
module uart_tx (
  input  wire       clk,
  input  wire       rst_n,
  input  wire       tick16,
  input  wire [1:0] parity_mode,
  input  wire [7:0] tx_data,
  input  wire       tx_valid,
  output wire       tx_ready,
  output wire       tx
);

  localparam [2:0]  ST_IDLE   = 3'd0;
  localparam [2:0]  ST_START  = 3'd1;
  localparam [2:0]  ST_DATA   = 3'd2;
  localparam [2:0]  ST_PARITY = 3'd3;
  localparam [2:0]  ST_STOP   = 3'd4;
  localparam [3:0]  TICK_LAST = 4'd15;
  localparam [2:0]  BIT_LAST  = 3'd7;
  localparam [15:0] PH_ZERO   = 16'd0;
  localparam [15:0] PH_ONE    = 16'd1;
  localparam [15:0] PH_MAX    = 16'hFFFF;

  reg [2:0]  state_q;
  reg [3:0]  tick_cnt_q;
  reg [7:0]  shreg_q;
  reg [2:0]  bit_idx_q;
  reg        par_bit_q;
  reg        par_en_q;
  reg        tx_q;
  reg [15:0] cnt_q;    // cycles since last tick16 (strictly before this cycle)
  reg [15:0] phase_q;  // phase latched at accept
  reg        pend_q;   // delayed tick pending
  reg [15:0] dly_q;    // remaining delay

  // phase at accept: 0 if tick16 is high this cycle, else cycles since last tick
  wire [15:0] phase_w = tick16 ? PH_ZERO : cnt_q;                 // REQ-006
  // frame-aligned tick
  wire dtick = (tick16 & (phase_q == PH_ZERO)) |
               (pend_q & (dly_q == PH_ZERO));                     // REQ-006
  wire tick_last = (tick_cnt_q == TICK_LAST);

  assign tx_ready = 1'b1;// REQ-011 REQ-003
  assign tx       = tx_q;                 // REQ-003

  always @(posedge clk) begin
    if (!rst_n) begin                     // REQ-004 synchronous reset
      state_q    <= ST_IDLE;
      tick_cnt_q <= 4'd0;
      shreg_q    <= 8'd0;
      bit_idx_q  <= 3'd0;
      par_bit_q  <= 1'b0;
      par_en_q   <= 1'b0;
      tx_q       <= 1'b1;                 // REQ-003
      cnt_q      <= PH_ONE;               // REQ-004 virtual tick at cycle -1
      phase_q    <= PH_ZERO;
      pend_q     <= 1'b0;
      dly_q      <= PH_ZERO;
    end else begin
      // measure cycles since last tick16
      if (tick16)                cnt_q <= PH_ONE;
      else if (cnt_q != PH_MAX)  cnt_q <= cnt_q + PH_ONE;

      // delayed tick generation (only while a frame is active)
      if (state_q == ST_IDLE) begin
        pend_q <= 1'b0;
      end else if (tick16 && (phase_q != PH_ZERO)) begin
        pend_q <= 1'b1;
        dly_q  <= phase_q - PH_ONE;
      end else if (pend_q) begin
        if (dly_q == PH_ZERO) pend_q <= 1'b0;
        else                  dly_q  <= dly_q - PH_ONE;
      end

      case (state_q)
        ST_IDLE: begin
          tx_q <= 1'b1;
          if (tx_valid) begin             // REQ-001 REQ-012 accept only in IDLE
            tx_q       <= 1'b0;           // REQ-001 REQ-011 start bit from next cycle
            shreg_q    <= tx_data;
            par_bit_q  <= (^tx_data) ^ parity_mode[1]; // REQ-009
            par_en_q   <= parity_mode[0] ^ parity_mode[1]; // REQ-009 REQ-010
            phase_q    <= phase_w;        // REQ-006 frame alignment
            tick_cnt_q <= 4'd0;
            bit_idx_q  <= 3'd0;
            state_q    <= ST_START;
          end
        end
        ST_START: begin
          if (dtick) begin
            if (tick_last) begin
              tx_q       <= shreg_q[0];   // REQ-001 LSB first
              shreg_q    <= {1'b0, shreg_q[7:1]};
              bit_idx_q  <= 3'd0;
              tick_cnt_q <= 4'd0;
              state_q    <= ST_DATA;
            end else begin
              tick_cnt_q <= tick_cnt_q + 4'd1;
            end
          end
        end
        ST_DATA: begin
          if (dtick) begin
            if (tick_last) begin
              tick_cnt_q <= 4'd0;
              if (bit_idx_q == BIT_LAST) begin
                if (par_en_q) begin
                  tx_q    <= par_bit_q;   // REQ-009 parity after bit 7
                  state_q <= ST_PARITY;
                end else begin
                  tx_q    <= 1'b1;        // REQ-001 stop bit
                  state_q <= ST_STOP;
                end
              end else begin
                tx_q      <= shreg_q[0];
                shreg_q   <= {1'b0, shreg_q[7:1]};
                bit_idx_q <= bit_idx_q + 3'd1;
              end
            end else begin
              tick_cnt_q <= tick_cnt_q + 4'd1;
            end
          end
        end
        ST_PARITY: begin
          if (dtick) begin
            if (tick_last) begin
              tx_q       <= 1'b1;         // REQ-001 stop bit
              tick_cnt_q <= 4'd0;
              state_q    <= ST_STOP;
            end else begin
              tick_cnt_q <= tick_cnt_q + 4'd1;
            end
          end
        end
        ST_STOP: begin
          tx_q <= 1'b1;
          if (dtick) begin
            if (tick_last) begin          // REQ-013 stop exactly 16 ticks
              tick_cnt_q <= 4'd0;
              state_q    <= ST_IDLE;
            end else begin
              tick_cnt_q <= tick_cnt_q + 4'd1;
            end
          end
        end
        default: begin                    // REQ-023 recover to idle
          state_q    <= ST_IDLE;
          tick_cnt_q <= 4'd0;
          tx_q       <= 1'b1;
        end
      endcase
    end
  end

endmodule
