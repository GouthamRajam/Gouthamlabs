// -----------------------------------------------------------------------------
// Module : alu8_core
// Design : alu8 (S2S)
// Purpose: Purely combinational ALU datapath. Computes the next-state values of
//          the 8-bit result and the N/Z/C/V flags from a, b, op, plus the
//          result write enable (res_we = 0 for CMP so the register holds).
//          Registers live in alu8_regs; this module has no state.
// Requirements implemented: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005,
//          REQ-006, REQ-007, REQ-008, REQ-012, REQ-013
// Structure (arch.yaml): one shared adder a + (b ^ {W{sub}}) + sub with
//          sub = (op==SUB || op==CMP), split as a (W-1)-bit low part and a
//          1-bit MSB part so carry-into-MSB and carry-out are both explicit;
//          logic unit (AND/OR/XOR); left/right logarithmic barrel shifter on
//          b[SHW-1:0] with carry = last bit shifted out; op-select mux;
//          zero detect and N from the selected operation result.
// Assumptions:
//   - W >= 2 and W is a power of two, so the shift amount is b[$clog2(W)-1:0]
//     (b[2:0] for W=8) and the remaining b bits are ignored for shifts.
//   - Opcode encoding per spec: 0 ADD, 1 SUB, 2 AND, 3 OR, 4 XOR, 5 SHL,
//     6 SHR, 7 CMP (DEFAULT - needs G1 review in spec).
//   - Variable shifts are written with the shift operator on a (W+1)-bit
//     vector; synthesis maps this to a log2(W)-stage barrel shifter.
// -----------------------------------------------------------------------------
module alu8_core #(
    parameter W = 8
) (
    input  wire [W-1:0] a,
    input  wire [W-1:0] b,
    input  wire [2:0]   op,
    output reg  [W-1:0] res_next,
    output wire         z_next,
    output reg          c_next,
    output reg          v_next,
    output wire         n_next,
    output wire         res_we
);

    // Opcode encoding (REQ-012: all 8 codes defined)
    localparam [2:0] OP_ADD = 3'd0;
    localparam [2:0] OP_SUB = 3'd1;
    localparam [2:0] OP_AND = 3'd2;
    localparam [2:0] OP_OR  = 3'd3;
    localparam [2:0] OP_XOR = 3'd4;
    localparam [2:0] OP_SHL = 3'd5;
    localparam [2:0] OP_SHR = 3'd6;
    localparam [2:0] OP_CMP = 3'd7;

    // Shift-amount width: log2(W) (3 for W=8)
    localparam integer SHW = $clog2(W);

    // ------------------------------------------------------------------
    // Shared adder: a + (b ^ {W{sub}}) + sub          // REQ-001, REQ-002, REQ-006
    // ------------------------------------------------------------------
    wire         sub   = (op == OP_SUB) || (op == OP_CMP);   // REQ-002, REQ-006
    wire [W-1:0] b_eff = b ^ {W{sub}};                       // REQ-002: a + ~b + 1

    // Low W-1 bits; lo_sum[W-1] is the carry into the MSB
    wire [W-1:0] lo_sum = {1'b0, a[W-2:0]} + {1'b0, b_eff[W-2:0]}
                        + {{(W-1){1'b0}}, sub};
    // MSB; hi_sum[1] is the carry out of the MSB
    wire [1:0]   hi_sum = {1'b0, a[W-1]} + {1'b0, b_eff[W-1]}
                        + {1'b0, lo_sum[W-1]};

    wire [W-1:0] add_res = {hi_sum[0], lo_sum[W-2:0]};      // REQ-001/002/013: wraps mod 2^W
    wire         add_c   = hi_sum[1];                        // REQ-001/002: carry out (1 = no borrow for SUB/CMP)
    wire         add_v   = hi_sum[1] ^ lo_sum[W-1];          // REQ-008: carry-in(MSB) XOR carry-out(MSB)

    // ------------------------------------------------------------------
    // Barrel shifter (logical, zero fill), amount = b[SHW-1:0]
    // ------------------------------------------------------------------
    wire [SHW-1:0] sh_amt = b[SHW-1:0];                      // REQ-004/005/012: upper b bits ignored

    // Left: bit W of ({0,a} << n) is a[W-n] for n>=1, 0 for n=0
    wire [W:0] shl_full = {1'b0, a} << sh_amt;               // REQ-004
    // Right: bit 0 of ({a,0} >> n) is a[n-1] for n>=1, 0 for n=0
    wire [W:0] shr_full = {a, 1'b0} >> sh_amt;               // REQ-005

    // ------------------------------------------------------------------
    // Operation select mux (defaults first: no latches)
    // ------------------------------------------------------------------
    always @* begin
        res_next = add_res;
        c_next   = 1'b0;
        v_next   = 1'b0;
        case (op)
            OP_ADD: begin                                    // REQ-001, REQ-008
                res_next = add_res;
                c_next   = add_c;
                v_next   = add_v;
            end
            OP_SUB: begin                                    // REQ-002, REQ-008
                res_next = add_res;
                c_next   = add_c;
                v_next   = add_v;
            end
            OP_AND: begin                                    // REQ-003
                res_next = a & b;
                c_next   = 1'b0;
                v_next   = 1'b0;
            end
            OP_OR: begin                                     // REQ-003
                res_next = a | b;
                c_next   = 1'b0;
                v_next   = 1'b0;
            end
            OP_XOR: begin                                    // REQ-003
                res_next = a ^ b;
                c_next   = 1'b0;
                v_next   = 1'b0;
            end
            OP_SHL: begin                                    // REQ-004
                res_next = shl_full[W-1:0];
                c_next   = shl_full[W];
                v_next   = 1'b0;
            end
            OP_SHR: begin                                    // REQ-005
                res_next = shr_full[W:1];
                c_next   = shr_full[0];
                v_next   = 1'b0;
            end
            OP_CMP: begin                                    // REQ-006: flags as SUB, opres = a-b
                res_next = add_res;
                c_next   = add_c;
                v_next   = add_v;
            end
            default: begin
                res_next = add_res;
                c_next   = 1'b0;
                v_next   = 1'b0;
            end
        endcase
    end

    // ------------------------------------------------------------------
    // Flags derived from the selected W-bit operation result
    // ------------------------------------------------------------------
    assign z_next = (res_next == {W{1'b0}});                 // REQ-007
    assign n_next = res_next[W-1];                           // REQ-007

    // Result register loads on every op except CMP (holds)  // REQ-006
    assign res_we = (op != OP_CMP);

endmodule
