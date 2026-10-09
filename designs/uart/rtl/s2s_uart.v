module s2s_uart (
    input  wire        clk,
    input  wire        rst_n,

    // Host register interface (active-high active, active-high write)
    input  wire [1:0]  addr,
    input  wire        wr_en,
    input  wire        rd_en,
    input  wire [7:0]  wr_data,
    output reg  [7:0]  rd_data,

    // Serial pins
    output wire        tx,
    input  wire        rx
);

    // Register map:
    //   0x0  TX_DATA  (W)  — write byte to transmit
    //   0x1  RX_DATA  (R)  — read received byte (clears rx_data_ready)
    //   0x2  STATUS   (R)  — {5'b0, frame_err, rx_ready, tx_ready}
    //   0x3  BAUD_DIV (W)  — baud divisor (low 8 bits; high 8 via addr 0x3 twice)

    reg [15:0] baud_div;
    reg        baud_hi_next;

    // TX signals
    wire       tx_ready;
    reg  [7:0] tx_data_reg;
    reg        tx_valid_pulse;

    // RX signals
    wire [7:0] rx_data_raw;
    wire       rx_valid_raw;
    wire       rx_frame_err_raw;

    reg  [7:0] rx_data_buf;
    reg        rx_data_ready;
    reg        rx_frame_err;

    s2s_uart_tx u_tx (
        .clk      (clk),
        .rst_n    (rst_n),
        .baud_div (baud_div),
        .tx_data  (tx_data_reg),
        .tx_valid (tx_valid_pulse),
        .tx_ready (tx_ready),
        .tx_out   (tx)
    );

    s2s_uart_rx u_rx (
        .clk          (clk),
        .rst_n        (rst_n),
        .baud_div     (baud_div),
        .rx_in        (rx),
        .rx_data      (rx_data_raw),
        .rx_valid     (rx_valid_raw),
        .rx_frame_err (rx_frame_err_raw)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_div      <= 16'd433;  // default: 115200 @ 50 MHz
            baud_hi_next  <= 1'b0;
            tx_data_reg   <= 8'd0;
            tx_valid_pulse <= 1'b0;
            rx_data_buf   <= 8'd0;
            rx_data_ready <= 1'b0;
            rx_frame_err  <= 1'b0;
            rd_data       <= 8'd0;
        end else begin
            tx_valid_pulse <= 1'b0;

            if (rx_valid_raw) begin
                rx_data_buf   <= rx_data_raw;
                rx_data_ready <= 1'b1;
                rx_frame_err  <= rx_frame_err_raw;
            end

            if (wr_en) begin
                case (addr)
                    2'd0: begin
                        tx_data_reg    <= wr_data;
                        tx_valid_pulse <= 1'b1;
                    end
                    2'd3: begin
                        if (!baud_hi_next) begin
                            baud_div[7:0] <= wr_data;
                            baud_hi_next  <= 1'b1;
                        end else begin
                            baud_div[15:8] <= wr_data;
                            baud_hi_next   <= 1'b0;
                        end
                    end
                    default: ;
                endcase
            end

            if (rd_en) begin
                case (addr)
                    2'd1: begin
                        rd_data       <= rx_data_buf;
                        rx_data_ready <= 1'b0;
                        rx_frame_err  <= 1'b0;
                    end
                    2'd2: begin
                        rd_data <= {5'b0, rx_frame_err, rx_data_ready, tx_ready};
                    end
                    default: rd_data <= 8'd0;
                endcase
            end
        end
    end

endmodule
