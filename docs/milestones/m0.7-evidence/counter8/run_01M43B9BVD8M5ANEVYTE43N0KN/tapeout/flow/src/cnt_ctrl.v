// -----------------------------------------------------------------------------
// Module  : cnt_ctrl
// Purpose : Combinational control decoder for the 8-bit up/down counter.
//           Encodes load/enable/up_down into a 2-bit operation code for cnt_dp.
// Requirements implemented: REQ-004, REQ-005, REQ-006, REQ-009, REQ-010
// Encoding: 00 hold, 01 up, 10 down, 11 load
// Assumptions:
//   - Purely combinational, no state, so no clock/reset ports (per arch.yaml).
//   - Reset priority (rst_n > load) is applied in cnt_dp.
//   - Priority inside this block: load > enable.
// -----------------------------------------------------------------------------
module cnt_ctrl (
    input  wire       load,
    input  wire       enable,
    input  wire       up_down,
    output reg  [1:0] op
);

    localparam [1:0] OP_HOLD = 2'b00;
    localparam [1:0] OP_UP   = 2'b01;
    localparam [1:0] OP_DOWN = 2'b10;
    localparam [1:0] OP_LOAD = 2'b11;

    always @(*) begin
        op = OP_HOLD;                 // REQ-009 default: hold
        if (load) begin
            op = OP_LOAD;             // REQ-004, REQ-010: load beats enable/up_down
        end else if (enable) begin
            if (up_down) begin
                op = OP_UP;           // REQ-005
            end else begin
                op = OP_DOWN;         // REQ-006
            end
        end else begin
            op = OP_HOLD;             // REQ-009, REQ-010
        end
    end

endmodule
