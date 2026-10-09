// Provenance: agent-generated (Phase 1.5 Pillar A)
//
// s2s_rv32i_decoder.v — Combinational instruction decoder for the s2s_rv32i
// RISC-V core. Extracts all fields, generates the sign-extended immediate,
// flags instruction types, and detects illegal instructions.
// See architecture.md sections 3.4, 8.2, 11.1.

module s2s_rv32i_decoder (
    input  wire [31:0] instr,

    // Register addresses
    output wire [4:0]  rs1_addr,
    output wire [4:0]  rs2_addr,
    output wire [4:0]  rd_addr,

    // Immediate (sign-extended, shifted as appropriate per type)
    output reg  [31:0] imm,

    // Instruction fields
    output wire [6:0]  opcode,
    output wire [2:0]  funct3,
    output wire [6:0]  funct7,

    // Instruction type flags (exactly one set for valid instructions)
    output wire        is_lui,
    output wire        is_auipc,
    output wire        is_jal,
    output wire        is_jalr,
    output wire        is_branch,
    output wire        is_load,
    output wire        is_store,
    output wire        is_alu_imm,     // OP-IMM (ADDI, SLTI, etc.)
    output wire        is_alu_reg,     // OP (ADD, SUB, etc.)
    output wire        is_fence,
    output wire        is_system,      // any SYSTEM opcode instruction

    // SYSTEM sub-type flags
    output wire        is_ecall,
    output wire        is_ebreak,
    output wire        is_mret,
    output wire        is_wfi,
    output wire        is_csr,

    // Illegal instruction flag
    output wire        is_illegal
);

    // ---------------------------------------------------------------
    // Field extraction
    // ---------------------------------------------------------------
    assign opcode   = instr[6:0];
    assign rd_addr  = instr[11:7];
    assign funct3   = instr[14:12];
    assign rs1_addr = instr[19:15];
    assign rs2_addr = instr[24:20];
    assign funct7   = instr[31:25];

    // ---------------------------------------------------------------
    // Opcode decode — primary type flags
    // ---------------------------------------------------------------
    assign is_lui     = (opcode == 7'b0110111);
    assign is_auipc   = (opcode == 7'b0010111);
    assign is_jal     = (opcode == 7'b1101111);
    assign is_jalr    = (opcode == 7'b1100111);
    assign is_branch  = (opcode == 7'b1100011);
    assign is_load    = (opcode == 7'b0000011);
    assign is_store   = (opcode == 7'b0100011);
    assign is_alu_imm = (opcode == 7'b0010011);
    assign is_alu_reg = (opcode == 7'b0110011);
    assign is_fence   = (opcode == 7'b0001111);
    assign is_system  = (opcode == 7'b1110011);

    wire opcode_valid = is_lui | is_auipc | is_jal | is_jalr | is_branch
                      | is_load | is_store | is_alu_imm | is_alu_reg
                      | is_fence | is_system;

    // ---------------------------------------------------------------
    // SYSTEM sub-type decode (funct3 == 000 encodes ECALL/EBREAK/MRET/WFI)
    // ---------------------------------------------------------------
    wire sys_funct3_000 = is_system && (funct3 == 3'b000);

    assign is_ecall  = sys_funct3_000 && (instr[31:7] == 25'b0000000000000000000000000);
    assign is_ebreak = sys_funct3_000 && (instr[31:7] == 25'b0000000000010000000000000);
    assign is_mret   = sys_funct3_000 && (instr[31:7] == 25'b0011000000100000000000000);
    assign is_wfi    = sys_funct3_000 && (instr[31:7] == 25'b0001000001010000000000000);

    // CSR instructions: SYSTEM opcode with funct3 in {001,010,011,101,110,111}
    assign is_csr = is_system && (funct3[1:0] != 2'b00) && (funct3 != 3'b100);

    // ---------------------------------------------------------------
    // Immediate generation (combinational mux by opcode)
    // ---------------------------------------------------------------
    always @(*) begin
        case (1'b1) // synopsys parallel_case
            is_lui, is_auipc:
                // U-type: {inst[31:12], 12'b0}
                imm = {instr[31:12], 12'b0};
            is_jal:
                // J-type: {12{inst[31]}, inst[19:12], inst[20], inst[30:21], 1'b0}
                imm = {{12{instr[31]}}, instr[19:12], instr[20], instr[30:21], 1'b0};
            is_branch:
                // B-type: {20{inst[31]}, inst[7], inst[30:25], inst[11:8], 1'b0}
                imm = {{20{instr[31]}}, instr[7], instr[30:25], instr[11:8], 1'b0};
            is_store:
                // S-type: {21{inst[31]}, inst[30:25], inst[11:7]}
                imm = {{21{instr[31]}}, instr[30:25], instr[11:7]};
            default:
                // I-type (JALR, LOAD, OP-IMM, SYSTEM/CSR, FENCE, etc.)
                // {21{inst[31]}, inst[30:20]}
                imm = {{21{instr[31]}}, instr[30:20]};
        endcase
    end

    // ---------------------------------------------------------------
    // Illegal instruction detection
    // ---------------------------------------------------------------

    // JALR: funct3 must be 000
    wire jalr_illegal = is_jalr && (funct3 != 3'b000);

    // BRANCH: funct3 010 and 011 are illegal
    wire branch_illegal = is_branch && (funct3 == 3'b010 || funct3 == 3'b011);

    // LOAD: funct3 011, 110, 111 are illegal
    wire load_illegal = is_load && (funct3 == 3'b011 || funct3 == 3'b110
                                    || funct3 == 3'b111);

    // STORE: only funct3 000, 001, 010 are legal
    wire store_illegal = is_store && (funct3[2] == 1'b1 || funct3 == 3'b011);

    // OP-IMM shift checks:
    // SLLI (funct3=001) requires funct7=0000000
    // SRLI (funct3=101) requires funct7=0000000
    // SRAI (funct3=101) requires funct7=0100000
    wire opimm_shift_illegal =
        (is_alu_imm && (funct3 == 3'b001) && (funct7 != 7'b0000000)) |
        (is_alu_imm && (funct3 == 3'b101)
            && (funct7 != 7'b0000000) && (funct7 != 7'b0100000));

    // OP (R-type): only the 10 defined funct3/funct7 combinations are legal
    wire r_type_legal =
        (funct3 == 3'b000 && (funct7 == 7'b0000000 || funct7 == 7'b0100000)) |  // ADD/SUB
        (funct3 == 3'b001 && funct7 == 7'b0000000) |  // SLL
        (funct3 == 3'b010 && funct7 == 7'b0000000) |  // SLT
        (funct3 == 3'b011 && funct7 == 7'b0000000) |  // SLTU
        (funct3 == 3'b100 && funct7 == 7'b0000000) |  // XOR
        (funct3 == 3'b101 && (funct7 == 7'b0000000 || funct7 == 7'b0100000)) |  // SRL/SRA
        (funct3 == 3'b110 && funct7 == 7'b0000000) |  // OR
        (funct3 == 3'b111 && funct7 == 7'b0000000);   // AND
    wire r_type_illegal = is_alu_reg && !r_type_legal;

    // SYSTEM funct3=000: only ECALL, EBREAK, MRET, WFI are legal
    wire sys_000_illegal = sys_funct3_000
                         && !(is_ecall | is_ebreak | is_mret | is_wfi);

    // SYSTEM funct3=100: always illegal
    wire sys_100_illegal = is_system && (funct3 == 3'b100);

    // Combine all illegal conditions
    assign is_illegal = !opcode_valid
                      | jalr_illegal
                      | branch_illegal
                      | load_illegal
                      | store_illegal
                      | opimm_shift_illegal
                      | r_type_illegal
                      | sys_000_illegal
                      | sys_100_illegal;

endmodule
