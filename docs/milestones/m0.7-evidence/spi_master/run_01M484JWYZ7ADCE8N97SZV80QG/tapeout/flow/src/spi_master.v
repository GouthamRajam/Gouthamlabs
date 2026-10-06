// -----------------------------------------------------------------------------
// Module   : spi_master
// Purpose  : Top level of the SPI master (modes 0-3, 8/16-bit MSB-first,
//            programmable SCK divider, auto/manual CS, transfer-complete irq).
//            Wiring only: instantiates sync2, spi_ctrl, spi_clkgen, spi_shift
//            exactly as connected in arch.yaml. No logic at this level.
// Implements: REQ-020 (one clock domain clk, no clock gating, no SCK-clocked
//             flops; miso is the only async crossing, via sync2),
//             REQ-021/REQ-022/REQ-023 (PPA/constraints: met by the flow; this
//             level adds no logic), REQ-024/REQ-025 (verification hooks:
//             spi_clkgen.edge_cnt exposed hierarchically).
//             Sub-module requirements REQ-001..REQ-019 are implemented in the
//             instanced modules and traced at their instances below.
// Assumptions:
//   - Port list, names, directions and widths follow spec.yaml interfaces.
//   - spi_clkgen params DIV_W=16, CNT_W=6; spi_shift param DATA_W=16
//     (arch.yaml).
//   - spi_clkgen.edge_cnt is a verification hook only and has no top-level
//     port; it is connected to a wire named edge_cnt_unused so it is visible
//     to the testbench/formal by hierarchy.
// -----------------------------------------------------------------------------
module spi_master (
    input  wire        clk,        // REQ-020: single system clock
    input  wire        rst_n,      // REQ-018: synchronous active-low reset
    input  wire        start,      // REQ-001
    input  wire [15:0] tx_data,    // REQ-001, REQ-004
    input  wire        word_len,   // REQ-001, REQ-003
    input  wire        cpol,       // REQ-002, REQ-007
    input  wire        cpha,       // REQ-002
    input  wire [15:0] clk_div,    // REQ-005, REQ-006
    input  wire        cs_mode,    // REQ-008, REQ-010
    input  wire        cs_force,   // REQ-010
    input  wire        irq_clear,  // REQ-013
    input  wire        miso,       // REQ-011: asynchronous input
    output wire        sck,        // REQ-002, REQ-005
    output wire        mosi,       // REQ-003, REQ-017
    output wire        cs_n,       // REQ-008, REQ-010
    output wire        busy,       // REQ-014
    output wire        done,       // REQ-012
    output wire        irq,        // REQ-013
    output wire [15:0] rx_data,    // REQ-004, REQ-012
    output wire        start_err   // REQ-015
);

    // Parameters from arch.yaml
    localparam integer DIV_W  = 16;  // clk_div width
    localparam integer CNT_W  = 6;   // tick counter width (0..2W+1 <= 33)
    localparam integer DATA_W = 16;  // max word width

    // Internal nets
    wire             miso_s;          // synchronized miso
    wire             start_acc;       // start accepted (start & ~busy)
    wire             edge_stb;        // SCK edge strobe
    wire             lead_edge;       // edge is a leading edge
    wire             cs_rise_stb;     // transfer complete / CS rise strobe
    wire             end_stb;         // end of CS-high recovery
    wire [CNT_W-1:0] edge_cnt_unused; // verification hook (REQ-025), no port

    // REQ-011, REQ-020: the only asynchronous crossing (miso) passes sync2
    sync2 u_sync2 (
        .clk   (clk),
        .rst_n (rst_n),
        .d     (miso),
        .q     (miso_s)
    );

    // REQ-001, REQ-008..REQ-010, REQ-012..REQ-016, REQ-018, REQ-019
    spi_ctrl u_spi_ctrl (
        .clk         (clk),
        .rst_n       (rst_n),
        .start       (start),
        .cs_mode     (cs_mode),
        .cs_force    (cs_force),
        .irq_clear   (irq_clear),
        .cs_rise_stb (cs_rise_stb),
        .end_stb     (end_stb),
        .start_acc   (start_acc),
        .busy        (busy),
        .cs_n        (cs_n),
        .done        (done),
        .irq         (irq),
        .start_err   (start_err)
    );

    // REQ-002, REQ-003, REQ-005..REQ-007, REQ-009, REQ-014, REQ-016, REQ-020
    // (SCK is a clk-domain register; no flop is clocked by SCK)
    spi_clkgen #(
        .DIV_W (DIV_W),
        .CNT_W (CNT_W)
    ) u_spi_clkgen (
        .clk         (clk),
        .rst_n       (rst_n),
        .start_acc   (start_acc),
        .clk_div     (clk_div),
        .word_len    (word_len),
        .cpol        (cpol),
        .sck         (sck),
        .edge_stb    (edge_stb),
        .lead_edge   (lead_edge),
        .cs_rise_stb (cs_rise_stb),
        .end_stb     (end_stb),
        .edge_cnt    (edge_cnt_unused)   // REQ-025 verification hook
    );

    // REQ-001..REQ-004, REQ-007, REQ-011, REQ-012, REQ-017..REQ-019
    spi_shift #(
        .DATA_W (DATA_W)
    ) u_spi_shift (
        .clk         (clk),
        .rst_n       (rst_n),
        .start_acc   (start_acc),
        .tx_data     (tx_data),
        .word_len    (word_len),
        .cpha        (cpha),
        .edge_stb    (edge_stb),
        .lead_edge   (lead_edge),
        .cs_rise_stb (cs_rise_stb),
        .miso_s      (miso_s),
        .mosi        (mosi),
        .rx_data     (rx_data)
    );

endmodule
