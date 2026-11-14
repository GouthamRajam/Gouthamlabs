// -----------------------------------------------------------------------------
// Module  : uart_rx
// Purpose : UART receiver, 16x oversampling, majority of 3 samples at ticks
//           7, 8, 9 of each bit. FSM IDLE/START/DATA/PARITY/STOP/WAIT_HIGH.
// REQs    : REQ-002 REQ-003 REQ-004 REQ-010 REQ-014 REQ-015 REQ-016
//           REQ-017 REQ-018 REQ-019 REQ-020 REQ-021 REQ-022 REQ-023
// Assumptions: rx_sync is already synchronized (sync2); tick16 is a one-cycle
//           pulse; parity_mode is latched at start detection.
//           Tick counter counts ticks since falling edge; the sample at
//           counter value n (with tick16) is tick n+1 of the bit.
// -----------------------------------------------------------------------------
module uart_rx (
  input  wire       clk,
  input  wire       rst_n,
  input  wire       tick16,
  input  wire [1:0] parity_mode,
  input  wire       rx_sync,
  output wire [7:0] rx_data,
  output wire       rx_valid,
  output wire       frame_err,
  output wire       parity_err,
  output wire       overrun_err
);

  localparam [2:0] ST_IDLE      = 3'd0;
  localparam [2:0] ST_START     = 3'd1;
  localparam [2:0] ST_DATA      = 3'd2;
  localparam [2:0] ST_PARITY    = 3'd3;
  localparam [2:0] ST_STOP      = 3'd4;
  localparam [2:0] ST_WAIT_HIGH = 3'd5;
  localparam [3:0] CNT_S0       = 4'd6;  // tick 7
  localparam [3:0] CNT_S1       = 4'd7;  // tick 8
  localparam [3:0] CNT_S2       = 4'd8;  // tick 9
  localparam [3:0] CNT_LAST     = 4'd15;
  localparam [2:0] BIT_LAST     = 3'd7;

  reg [2:0] state_q;
  reg [3:0] tick_cnt_q;
  reg [7:0] shreg_q;
  reg [2:0] bit_idx_q;
  reg [1:0] samp_q;
  reg       prev_q;
  reg       par_en_q;
  reg       odd_q;
  reg       perr_q;
  reg [7:0] rx_data_q;
  reg       rx_valid_q;
  reg       frame_err_q;
  reg       parity_err_q;

  // REQ-002 majority of the 3 center samples (current input is sample 3)
  wire maj = (samp_q[0] & samp_q[1]) | (samp_q[0] & rx_sync) | (samp_q[1] & rx_sync);
  wire fall_edge = prev_q & ~rx_sync;      // REQ-014 synchronized falling edge
  wire tick_s2 = tick16 & (tick_cnt_q == CNT_S2);

  assign rx_data     = rx_data_q;
  assign rx_valid    = rx_valid_q;         // REQ-016
  assign frame_err   = frame_err_q;
  assign parity_err  = parity_err_q;
  assign overrun_err = 1'b0;               // REQ-022 constant 0

  always @(posedge clk) begin
    if (!rst_n) begin                      // REQ-004 REQ-003
      state_q      <= ST_IDLE;
      tick_cnt_q   <= 4'd0;
      shreg_q      <= 8'd0;
      bit_idx_q    <= 3'd0;
      samp_q       <= 2'b00;
      prev_q       <= 1'b1;
      par_en_q     <= 1'b0;
      odd_q        <= 1'b0;
      perr_q       <= 1'b0;
      rx_data_q    <= 8'd0;
      rx_valid_q   <= 1'b0;
      frame_err_q  <= 1'b0;
      parity_err_q <= 1'b0;
    end else begin
      prev_q       <= rx_sync;
      rx_valid_q   <= 1'b0;                // one-cycle pulses by default
      frame_err_q  <= 1'b0;
      parity_err_q <= 1'b0;

      if (state_q != ST_IDLE && state_q != ST_WAIT_HIGH && tick16) begin
        if (tick_cnt_q == CNT_LAST) tick_cnt_q <= 4'd0;
        else                        tick_cnt_q <= tick_cnt_q + 4'd1;
        if (tick_cnt_q == CNT_S0) samp_q[0] <= rx_sync; // REQ-002 tick 7
        if (tick_cnt_q == CNT_S1) samp_q[1] <= rx_sync; // REQ-002 tick 8
      end

      case (state_q)
        ST_IDLE: begin
          tick_cnt_q <= 4'd0;
          bit_idx_q  <= 3'd0;
          perr_q     <= 1'b0;
          if (fall_edge) begin             // REQ-014 start detection
            par_en_q <= parity_mode[0] ^ parity_mode[1]; // REQ-010 REQ-018
            odd_q    <= parity_mode[1];
            state_q  <= ST_START;
          end
        end
        ST_START: begin
          if (tick16 && tick_cnt_q == CNT_S1) begin
            if (rx_sync) state_q <= ST_IDLE;   // REQ-014 glitch rejected
          end
          if (tick16 && tick_cnt_q == CNT_S2) begin
            state_q <= ST_DATA;
          end
        end
        ST_DATA: begin
          if (tick_s2) begin               // REQ-015 LSB first
            shreg_q   <= {maj, shreg_q[7:1]};
            bit_idx_q <= bit_idx_q + 3'd1;
            if (bit_idx_q == BIT_LAST) begin
              if (par_en_q) state_q <= ST_PARITY;
              else          state_q <= ST_STOP;
            end
          end
        end
        ST_PARITY: begin
          if (tick_s2) begin               // REQ-018
            perr_q  <= maj ^ (^shreg_q) ^ odd_q;
            state_q <= ST_STOP;
          end
        end
        ST_STOP: begin
          if (tick_s2) begin               // REQ-016 REQ-017 REQ-021
            rx_valid_q   <= 1'b1;
            rx_data_q    <= shreg_q;
            frame_err_q  <= ~maj;
            parity_err_q <= perr_q;
            if (maj) state_q <= ST_IDLE;   // REQ-021 ready for next start
            else     state_q <= ST_WAIT_HIGH; // REQ-019
          end
        end
        ST_WAIT_HIGH: begin                // REQ-019 wait for line high
          if (rx_sync) state_q <= ST_IDLE;
        end
        default: begin                     // REQ-023
          state_q <= ST_IDLE;
        end
      endcase
    end
  end

endmodule
