module s2s_uart_tx (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [15:0] baud_div,
    input  wire [7:0]  tx_data,
    input  wire        tx_valid,
    output reg         tx_ready,
    output reg         tx_out
);

    localparam IDLE  = 2'd0,
               START = 2'd1,
               DATA  = 2'd2,
               STOP  = 2'd3;

    reg [1:0]  state;
    reg [15:0] baud_cnt;
    reg [2:0]  bit_idx;
    reg [7:0]  shift_reg;

    wire baud_tick = (baud_cnt == 16'd0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            baud_cnt  <= 16'd0;
            bit_idx   <= 3'd0;
            shift_reg <= 8'd0;
            tx_ready  <= 1'b1;
            tx_out    <= 1'b1;
        end else begin
            case (state)
                IDLE: begin
                    tx_out   <= 1'b1;
                    tx_ready <= 1'b1;
                    if (tx_valid && tx_ready) begin
                        shift_reg <= tx_data;
                        tx_ready  <= 1'b0;
                        baud_cnt  <= baud_div;
                        state     <= START;
                    end
                end

                START: begin
                    tx_out <= 1'b0;
                    if (baud_tick) begin
                        baud_cnt <= baud_div;
                        bit_idx  <= 3'd0;
                        state    <= DATA;
                    end else begin
                        baud_cnt <= baud_cnt - 16'd1;
                    end
                end

                DATA: begin
                    tx_out <= shift_reg[0];
                    if (baud_tick) begin
                        shift_reg <= {1'b0, shift_reg[7:1]};
                        if (bit_idx == 3'd7) begin
                            baud_cnt <= baud_div;
                            state    <= STOP;
                        end else begin
                            baud_cnt <= baud_div;
                            bit_idx  <= bit_idx + 3'd1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt - 16'd1;
                    end
                end

                STOP: begin
                    tx_out <= 1'b1;
                    if (baud_tick) begin
                        state <= IDLE;
                    end else begin
                        baud_cnt <= baud_cnt - 16'd1;
                    end
                end
            endcase
        end
    end

endmodule
