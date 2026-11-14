// Provenance: hand-authored by Claude in interactive Code session (not S2S agent pipeline)
//
// s2s_rv32i_alu.v — Combinational ALU for the s2s_rv32i RISC-V core.
// 10 operations controlled by a 4-bit alu_op input.
// See architecture.md section 3.3.

module s2s_rv32i_alu (
    input  wire [31:0] op_a,
    input  wire [31:0] op_b,
    input  wire [3:0]  alu_op,

    output reg  [31:0] result
);

    // ALU operation encodings
    localparam ALU_ADD  = 4'b0000;
    localparam ALU_SUB  = 4'b0001;
    localparam ALU_AND  = 4'b0010;
    localparam ALU_OR   = 4'b0011;
    localparam ALU_XOR  = 4'b0100;
    localparam ALU_SLL  = 4'b0101;
    localparam ALU_SRL  = 4'b0110;
    localparam ALU_SRA  = 4'b0111;
    localparam ALU_SLT  = 4'b1000;
    localparam ALU_SLTU = 4'b1001;

    always @(*) begin
        case (alu_op)
            ALU_ADD:  result = op_a + op_b;
            ALU_SUB:  result = op_a - op_b;
            ALU_AND:  result = op_a & op_b;
            ALU_OR:   result = op_a | op_b;
            ALU_XOR:  result = op_a ^ op_b;
            ALU_SLL:  result = op_a << op_b[4:0];
            ALU_SRL:  result = op_a >> op_b[4:0];
            ALU_SRA:  result = $signed(op_a) >>> op_b[4:0];
            ALU_SLT:  result = {31'b0, $signed(op_a) < $signed(op_b)};
            ALU_SLTU: result = {31'b0, op_a < op_b};
            default:  result = 32'b0;
        endcase
    end

endmodule
