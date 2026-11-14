// -----------------------------------------------------------------------------
// Module  : uart_tx
// Purpose : UART transmitter. FSM IDLE/START/DATA/PARITY/STOP, LSB first,
//           1 start bit, 8 data bits, optional parity, 1 stop bit.
//           Each bit lasts 16 tick16 pulses.
// REQs    : REQ-001 REQ-003 REQ-004 REQ-009 REQ-010 REQ-011 REQ-012
//           REQ-013 REQ-023
// Assumptions: tick16 is a one-cycle pulse from baud_gen; parity_mode is
//           latched at accept so a mid-frame change cannot hang the FSM.
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

  localparam [2:0] ST_IDLE   = 3'd0;
  localparam [2:0] ST_START  = 3'd1;
  localparam [2:0] ST_DATA   = 3'd2;
  localparam [2:0] ST_PARITY = 3'd3;
  localparam [2:0] ST_STOP   = 3'd4;
  localparam [3:0] TICK_LAST = 4'd15;
  localparam [2:0] BIT_LAST  = 3'd7;

  reg [2:0] state_q;
  reg [3:0] tick_cnt_q;
  reg [7:0] shreg_q;
  reg [2:0] bit_idx_q;
  reg       par_bit_q;
  reg       par_en_q;
  reg       tx_q;

  wire tick_last = (tick_cnt_q == TICK_LAST);

  assign tx_ready = (state_q == ST_IDLE); // REQ-011 REQ-003
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
    end else begin
      case (state_q)
        ST_IDLE: begin
          tx_q <= 1'b1;
          if (tx_valid) begin             // REQ-001 REQ-012 accept only in IDLE
            shreg_q    <= tx_data;
            par_bit_q  <= (^tx_data) ^ parity_mode[1]; // REQ-009
            par_en_q   <= parity_mode[0] ^ parity_mode[1]; // REQ-009 REQ-010
            tick_cnt_q <= 4'd0;
            bit_idx_q  <= 3'd0;
            state_q    <= ST_START;
          end
        end
        ST_START: begin
          if (tick16) begin
            if (tx_q) begin               // aligned start: first tick after accept
              tx_q       <= 1'b0;         // REQ-001 start bit
              tick_cnt_q <= 4'd0;
            end else if (tick_last) begin
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
          if (tick16) begin
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
          if (tick16) begin
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
          if (tick16) begin
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
