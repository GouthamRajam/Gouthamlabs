// -----------------------------------------------------------------------------
// Module   : spi_ctrl
// Design   : spi_master (S2S Phase 0, sky130A / sky130_fd_sc_hd)
// Purpose  : Transfer control FSM of the SPI master. Accepts start requests,
//            generates busy, chip select (auto / manual), the done pulse, the
//            level interrupt and the start-while-busy error pulse. All timing
//            strobes (cs_rise_stb, end_stb) come from spi_clkgen, decoded one
//            cycle early, so every output here is a register.
// Implements: REQ-001, REQ-008, REQ-009, REQ-010, REQ-012, REQ-013, REQ-014,
//             REQ-015, REQ-016, REQ-018, REQ-019
// Assumptions:
//   - cs_rise_stb is high in the cycle before cycle 1+(2W+1)N and end_stb in
//     the cycle before cycle 1+(2W+2)N (per arch.yaml spi_clkgen), so the
//     registered outputs change exactly at the spec cycle numbers.
//   - Effective CS mode = live cs_mode while busy=0, latched cs_mode_q while
//     busy=1 (cs_mode_q loads every cycle with busy=0, incl. the accepting
//     edge). Mode changes during a transfer take effect when busy=0.
//   - In manual mode cs_n <= ~cs_force every cycle (1 clk latency), also
//     during a transfer; transfers never change cs_n in manual mode.
//   - FSM: IDLE -> ACTIVE on start_acc, ACTIVE -> RECOVER on cs_rise_stb,
//     ACTIVE/RECOVER -> IDLE on end_stb; any -> IDLE on reset.
//     busy is a separate register equal to (next state != IDLE).
// -----------------------------------------------------------------------------
module spi_ctrl (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire cs_mode,
    input  wire cs_force,
    input  wire irq_clear,
    input  wire cs_rise_stb,
    input  wire end_stb,
    output wire start_acc,
    output wire busy,
    output wire cs_n,
    output wire done,
    output wire irq,
    output wire start_err
);

    // FSM encoding
    localparam integer ST_W       = 2;
    localparam [ST_W-1:0] ST_IDLE    = 2'd0;
    localparam [ST_W-1:0] ST_ACTIVE  = 2'd1;
    localparam [ST_W-1:0] ST_RECOVER = 2'd2;

    // CS mode encoding
    localparam CS_MODE_AUTO   = 1'b0;

    // Registers
    reg [ST_W-1:0] state_q, state_d;
    reg            busy_q,      busy_d;
    reg            cs_n_q,      cs_n_d;
    reg            done_q,      done_d;
    reg            irq_q,       irq_d;
    reg            start_err_q, start_err_d;
    reg            cs_mode_q,   cs_mode_d;

    wire           cs_mode_eff;

    // REQ-001 / REQ-016: accept start on an edge where start=1 and busy=0
    // (including the first busy=0 cycle after a transfer -> back-to-back).
    assign start_acc   = start & ~busy_q;

    // REQ-010: effective CS mode; changes while busy=1 take effect at busy=0.
    assign cs_mode_eff = busy_q ? cs_mode_q : cs_mode;

    // Next-state / next-output logic
    always @(*) begin
        // defaults (no latches)
        state_d     = state_q;
        cs_mode_d   = cs_mode_q;
        cs_n_d      = cs_n_q;

        // FSM
        case (state_q)
            ST_IDLE: begin
                if (start_acc) begin
                    state_d = ST_ACTIVE;                  // REQ-001
                end
            end
            ST_ACTIVE: begin
                if (end_stb) begin
                    state_d = ST_IDLE;                    // robustness
                end else if (cs_rise_stb) begin
                    state_d = ST_RECOVER;                 // REQ-014
                end
            end
            ST_RECOVER: begin
                if (end_stb) begin
                    state_d = ST_IDLE;                    // REQ-014
                end
            end
            default: begin
                state_d = ST_IDLE;
            end
        endcase

        // REQ-014: busy from cycle 1 until cycle 1+(2W+2)N exclusive
        busy_d = (state_d != ST_IDLE);

        // Effective CS mode register loads only while busy=0 (REQ-010)
        if (!busy_q) begin
            cs_mode_d = cs_mode;
        end

        // Chip select
        if (cs_mode_eff != CS_MODE_AUTO) begin
            cs_n_d = ~cs_force;                           // REQ-010
        end else if (start_acc) begin
            cs_n_d = 1'b0;                                // REQ-008: fall 1 clk after accept
        end else if (cs_rise_stb) begin
            cs_n_d = 1'b1;                                // REQ-008 / REQ-009: rise at 1+(2W+1)N
        end else if (!busy_q) begin
            cs_n_d = 1'b1;                                // REQ-008: high at all other times
        end

        // REQ-012: done pulses in cycle 1+(2W+1)N
        done_d      = cs_rise_stb;

        // REQ-013: set wins over clear; start does not clear irq
        irq_d       = cs_rise_stb | (irq_q & ~irq_clear);

        // REQ-015: start while busy -> 1-cycle error pulse next cycle
        start_err_d = start & busy_q;
    end

    // REQ-018 / REQ-019: synchronous active-low reset, aborts any transfer
    always @(posedge clk) begin
        if (!rst_n) begin
            state_q     <= ST_IDLE;
            busy_q      <= 1'b0;
            cs_n_q      <= 1'b1;
            done_q      <= 1'b0;
            irq_q       <= 1'b0;
            start_err_q <= 1'b0;
            cs_mode_q   <= CS_MODE_AUTO;
        end else begin
            state_q     <= state_d;
            busy_q      <= busy_d;
            cs_n_q      <= cs_n_d;
            done_q      <= done_d;
            irq_q       <= irq_d;
            start_err_q <= start_err_d;
            cs_mode_q   <= cs_mode_d;
        end
    end

    assign busy      = busy_q;     // REQ-014
    assign cs_n      = cs_n_q;     // REQ-008, REQ-010
    assign done      = done_q;     // REQ-012
    assign irq       = irq_q;      // REQ-013
    assign start_err = start_err_q; // REQ-015

endmodule
