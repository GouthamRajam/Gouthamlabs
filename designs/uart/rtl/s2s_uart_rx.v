module s2s_uart_rx (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [15:0] baud_div,
    input  wire        rx_in,
    output reg  [7:0]  rx_data,
    output reg         rx_valid,
    output reg         rx_frame_err
);

    localparam IDLE    = 2'd0,
               START   = 2'd1,
               DATA    = 2'd2,
               STOP    = 2'd3;

    reg [1:0]  state;
    reg [15:0] baud_cnt;
    reg [3:0]  sample_cnt;
    reg [2:0]  bit_idx;
    reg [7:0]  shift_reg;
    reg [2:0]  rx_sync;

    wire rx_filtered = rx_sync[2];

    wire [15:0] baud_div_16 = baud_div / 16;
    wire baud_tick_16 = (baud_cnt == 16'd0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rx_sync <= 3'b111;
        else
            rx_sync <= {rx_sync[1:0], rx_in};
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            baud_cnt     <= 16'd0;
            sample_cnt   <= 4'd0;
            bit_idx      <= 3'd0;
            shift_reg    <= 8'd0;
            rx_data      <= 8'd0;
            rx_valid     <= 1'b0;
            rx_frame_err <= 1'b0;
        end else begin
            rx_valid     <= 1'b0;
            rx_frame_err <= 1'b0;

            case (state)
                IDLE: begin
                    if (!rx_filtered) begin
                        baud_cnt   <= baud_div_16;
                        sample_cnt <= 4'd0;
                        state      <= START;
                    end
                end

                START: begin
                    if (baud_tick_16) begin
                        if (sample_cnt == 4'd7) begin
                            if (!rx_filtered) begin
                                baud_cnt   <= baud_div_16;
                                sample_cnt <= 4'd0;
                                bit_idx    <= 3'd0;
                                state      <= DATA;
                            end else begin
                                state <= IDLE;
                            end
                        end else begin
                            baud_cnt   <= baud_div_16;
                            sample_cnt <= sample_cnt + 4'd1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt - 16'd1;
                    end
                end

                DATA: begin
                    if (baud_tick_16) begin
                        if (sample_cnt == 4'd15) begin
                            shift_reg  <= {rx_filtered, shift_reg[7:1]};
                            sample_cnt <= 4'd0;
                            baud_cnt   <= baud_div_16;
                            if (bit_idx == 3'd7) begin
                                state <= STOP;
                            end else begin
                                bit_idx <= bit_idx + 3'd1;
                            end
                        end else begin
                            baud_cnt   <= baud_div_16;
                            sample_cnt <= sample_cnt + 4'd1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt - 16'd1;
                    end
                end

                STOP: begin
                    if (baud_tick_16) begin
                        if (sample_cnt == 4'd15) begin
                            rx_data  <= shift_reg;
                            rx_valid <= 1'b1;
                            if (!rx_filtered)
                                rx_frame_err <= 1'b1;
                            state <= IDLE;
                        end else begin
                            baud_cnt   <= baud_div_16;
                            sample_cnt <= sample_cnt + 4'd1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt - 16'd1;
                    end
                end
            endcase
        end
    end

endmodule
