// -----------------------------------------------------------------------------
// Module : cnt_dp
// Purpose: W-bit counter datapath register. Synchronous active-low reset to 0,
//          next-state mux of hold, count+1, count-1 and load_data.
// Requirements implemented: REQ-001 REQ-002 REQ-003 REQ-004 REQ-005 REQ-006
//          REQ-007 REQ-008 REQ-009 REQ-012
// Assumptions: op encoding 00 hold, 01 up, 10 down, 11 load (from cnt_ctrl).
//          All inputs are synchronous to clk. Modulo-2^W wrap, no saturation.
// -----------------------------------------------------------------------------
module cnt_dp #(
    parameter W = 8
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [1:0]   op,
    input  wire [W-1:0] load_data,
    output wire [W-1:0] count
);

    localparam [1:0] OP_HOLD = 2'b00;
    localparam [1:0] OP_UP   = 2'b01;
    localparam [1:0] OP_DOWN = 2'b10;
    localparam [1:0] OP_LOAD = 2'b11;
    localparam [W-1:0] ONE   = {{(W-1){1'b0}}, 1'b1};

    reg [W-1:0] count_q;
    reg [W-1:0] count_d;

    // Next-state mux (combinational, defaults first)
    always @* begin
        count_d = count_q; // REQ-009 hold by default
        case (op)
            OP_HOLD: count_d = count_q;             // REQ-009
            OP_UP:   count_d = count_q + ONE;       // REQ-005 REQ-007 (wrap)
            OP_DOWN: count_d = count_q - ONE;       // REQ-006 REQ-008 (wrap)
            OP_LOAD: count_d = load_data;           // REQ-004
            default: count_d = count_q;
        endcase
    end

    // State register: synchronous active-low reset, highest priority
    always @(posedge clk) begin
        if (!rst_n) begin                           // REQ-001 REQ-002 REQ-003
            count_q <= {W{1'b0}};
        end else begin
            count_q <= count_d;
        end
    end

    assign count = count_q;                         // REQ-012 registered output

endmodule
