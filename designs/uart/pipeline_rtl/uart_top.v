// -----------------------------------------------------------------------------
// Module  : uart_top
// Purpose : Top level wiring of UART: baud generator, transmitter, receiver
//           and rx input synchronizer.
// Reqs    : REQ-003 (reset values via submodules), REQ-004 (rst_n to every
//           state element), REQ-005 (single clock, rx via sync2),
//           REQ-024 (verification hooks are external to RTL)
// Assumptions: submodule ports exactly as arch.yaml; DIV_W = 16.
// -----------------------------------------------------------------------------
module uart_top #(
    parameter DIV_W = 16,
    parameter DATA_W = 8,
    parameter PM_W = 2
) (
    input  wire              clk,         // REQ-005 single clock
    input  wire              rst_n,       // REQ-004 sync active-low reset
    input  wire              rx,          // async serial input
    output wire              tx,
    input  wire [DATA_W-1:0] tx_data,
    input  wire              tx_valid,
    output wire              tx_ready,
    output wire [DATA_W-1:0] rx_data,
    output wire              rx_valid,
    input  wire [DIV_W-1:0]  baud_div,
    input  wire [PM_W-1:0]   parity_mode,
    output wire              frame_err,
    output wire              parity_err,
    output wire              overrun_err
);

    wire tick16_w;
    wire rx_sync_w;

    // REQ-005: only async crossing, 2-flop synchronizer
    sync2 #(.STAGES(2)) u_sync2 (
        .clk   (clk),
        .rst_n (rst_n),
        .d     (rx),
        .q     (rx_sync_w)
    );

    baud_gen #(.DIV_W(DIV_W)) u_baud_gen (
        .clk      (clk),
        .rst_n    (rst_n),    // REQ-004
        .baud_div (baud_div),
        .tick16   (tick16_w)
    );

    uart_tx u_uart_tx (
        .clk         (clk),
        .rst_n       (rst_n), // REQ-003 REQ-004
        .tick16      (tick16_w),
        .parity_mode (parity_mode),
        .tx_data     (tx_data),
        .tx_valid    (tx_valid),
        .tx_ready    (tx_ready),
        .tx          (tx)
    );

    uart_rx u_uart_rx (
        .clk         (clk),
        .rst_n       (rst_n), // REQ-003 REQ-004
        .tick16      (tick16_w),
        .parity_mode (parity_mode),
        .rx_sync     (rx_sync_w),
        .rx_data     (rx_data),
        .rx_valid    (rx_valid),
        .frame_err   (frame_err),
        .parity_err  (parity_err),
        .overrun_err (overrun_err)
    );

endmodule
