// Provenance: hand-authored by Claude in interactive Code session (not S2S agent pipeline)
//
// s2s_rv32i_core.v — Top-level module for the s2s_rv32i RISC-V core.
// Contains the FSM controller, PC register, pipeline registers,
// interrupt synchronizers, memory interface muxes, and instantiates
// all submodules (decoder, regfile, ALU, CSR unit).
// See architecture.md sections 4, 8.1.

module s2s_rv32i_core #(
    parameter RESET_VECTOR = 32'h0000_0000
) (
    input  wire        clk,
    input  wire        rst_n,          // active-low synchronous reset

    // Memory interface (active-high valid/ready)
    output reg  [31:0] mem_addr,
    output reg  [31:0] mem_wdata,
    output reg  [3:0]  mem_wstrb,
    input  wire [31:0] mem_rdata,
    output reg         mem_valid,
    input  wire        mem_ready,

    // Interrupt inputs (active-high, directly from external sources)
    input  wire        irq_external,
    input  wire        irq_timer
);

    // ---------------------------------------------------------------
    // ALU operation encodings (must match s2s_rv32i_alu)
    // ---------------------------------------------------------------
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

    // ---------------------------------------------------------------
    // FSM state encoding
    // ---------------------------------------------------------------
    localparam [2:0] S_FETCH      = 3'd0;
    localparam [2:0] S_DECODE     = 3'd1;
    localparam [2:0] S_EXECUTE    = 3'd2;
    localparam [2:0] S_MEM_READ   = 3'd3;
    localparam [2:0] S_MEM_WRITE  = 3'd4;
    localparam [2:0] S_WRITEBACK  = 3'd5;
    localparam [2:0] S_TRAP_ENTRY = 3'd6;
    localparam [2:0] S_MRET       = 3'd7;

    // ---------------------------------------------------------------
    // Architectural state
    // ---------------------------------------------------------------
    reg [31:0] pc;
    reg [2:0]  state;

    // Pipeline / intermediate registers
    reg [31:0] instruction_reg;
    reg [31:0] rs1_data_reg;
    reg [31:0] rs2_data_reg;
    reg [31:0] alu_result_reg;
    reg [31:0] mem_rdata_reg;
    reg [31:0] csr_old_reg;
    reg [31:0] csr_new_reg;
    reg [31:0] branch_target_reg;

    // Trap info registers
    reg [31:0] trap_cause_reg;
    reg [31:0] trap_val_reg;
    reg [31:0] trap_pc_reg;

    // Branch control
    reg        branch_taken_flag;

    // CSR write control (latched in EXECUTE, used in WRITEBACK)
    reg        csr_do_write;

    // ---------------------------------------------------------------
    // Interrupt synchronizers (2-flop)
    // ---------------------------------------------------------------
    reg irq_ext_meta, irq_ext_sync;
    reg irq_tmr_meta, irq_tmr_sync;

    always @(posedge clk) begin
        if (!rst_n) begin
            irq_ext_meta <= 1'b0;
            irq_ext_sync <= 1'b0;
            irq_tmr_meta <= 1'b0;
            irq_tmr_sync <= 1'b0;
        end else begin
            irq_ext_meta <= irq_external;
            irq_ext_sync <= irq_ext_meta;
            irq_tmr_meta <= irq_timer;
            irq_tmr_sync <= irq_tmr_meta;
        end
    end

    // ---------------------------------------------------------------
    // Decoder instantiation
    // ---------------------------------------------------------------
    wire [4:0]  dec_rs1_addr, dec_rs2_addr, dec_rd_addr;
    wire [31:0] dec_imm;
    wire [2:0]  dec_funct3;
    /* verilator lint_off UNUSEDSIGNAL */
    wire [6:0]  dec_funct7;  // only bit 5 used in core; full width for decoder
    /* verilator lint_on UNUSEDSIGNAL */
    wire        dec_funct7_bit5 = dec_funct7[5];
    wire        dec_is_lui, dec_is_auipc, dec_is_jal, dec_is_jalr;
    wire        dec_is_branch, dec_is_load, dec_is_store;
    wire        dec_is_alu_imm, dec_is_alu_reg;
    wire        dec_is_fence;
    wire        dec_is_ecall, dec_is_ebreak, dec_is_mret, dec_is_wfi;
    wire        dec_is_csr;
    wire        dec_is_illegal;

    /* verilator lint_off PINCONNECTEMPTY */
    s2s_rv32i_decoder u_decoder (
        .instr      (instruction_reg),
        .rs1_addr   (dec_rs1_addr),
        .rs2_addr   (dec_rs2_addr),
        .rd_addr    (dec_rd_addr),
        .imm        (dec_imm),
        .opcode     (),             // not used by core FSM
        .funct3     (dec_funct3),
        .funct7     (dec_funct7),
        .is_lui     (dec_is_lui),
        .is_auipc   (dec_is_auipc),
        .is_jal     (dec_is_jal),
        .is_jalr    (dec_is_jalr),
        .is_branch  (dec_is_branch),
        .is_load    (dec_is_load),
        .is_store   (dec_is_store),
        .is_alu_imm (dec_is_alu_imm),
        .is_alu_reg (dec_is_alu_reg),
        .is_fence   (dec_is_fence),
        .is_system  (),             // sub-flags used directly
        .is_ecall   (dec_is_ecall),
        .is_ebreak  (dec_is_ebreak),
        .is_mret    (dec_is_mret),
        .is_wfi     (dec_is_wfi),
        .is_csr     (dec_is_csr),
        .is_illegal (dec_is_illegal)
    );
    /* verilator lint_on PINCONNECTEMPTY */

    // ---------------------------------------------------------------
    // Register file instantiation
    // ---------------------------------------------------------------
    wire [31:0] rf_rs1_data, rf_rs2_data;
    reg         rf_wr_en;
    reg  [4:0]  rf_wr_addr;
    reg  [31:0] rf_wr_data;

    s2s_rv32i_regfile u_regfile (
        .clk      (clk),
        .rs1_addr (dec_rs1_addr),
        .rs1_data (rf_rs1_data),
        .rs2_addr (dec_rs2_addr),
        .rs2_data (rf_rs2_data),
        .wr_en    (rf_wr_en),
        .wr_addr  (rf_wr_addr),
        .wr_data  (rf_wr_data)
    );

    // ---------------------------------------------------------------
    // ALU instantiation
    // ---------------------------------------------------------------
    reg  [31:0] alu_op_a, alu_op_b;
    reg  [3:0]  alu_op;
    wire [31:0] alu_result;

    s2s_rv32i_alu u_alu (
        .op_a   (alu_op_a),
        .op_b   (alu_op_b),
        .alu_op (alu_op),
        .result (alu_result)
    );

    // ---------------------------------------------------------------
    // CSR unit instantiation
    // ---------------------------------------------------------------
    wire [31:0] csr_rdata;
    wire        csr_valid_addr;
    wire        csr_readonly;
    reg         csr_wen;
    reg  [31:0] csr_wdata_to_unit;
    reg         trap_enter;
    reg         mret_exec;
    wire [31:0] mtvec_val;
    wire [31:0] mepc_val;
    wire        mstatus_mie_val;
    /* verilator lint_off UNUSEDSIGNAL */
    wire [31:0] mie_val;  // only bits 11, 7 used (MEIE, MTIE)
    wire [31:0] mip_val;  // only bits 11, 7 used (MEIP, MTIP)
    /* verilator lint_on UNUSEDSIGNAL */
    reg         instret_inc;

    s2s_rv32i_csr u_csr (
        .clk           (clk),
        .rst_n         (rst_n),
        .csr_addr      (instruction_reg[31:20]),
        .csr_rdata     (csr_rdata),
        .csr_wen       (csr_wen),
        .csr_wdata     (csr_wdata_to_unit),
        .csr_valid     (csr_valid_addr),
        .csr_readonly  (csr_readonly),
        .trap_enter    (trap_enter),
        .trap_mepc     (trap_pc_reg),
        .trap_mcause   (trap_cause_reg),
        .trap_mtval    (trap_val_reg),
        .mret_exec     (mret_exec),
        .mtvec_o       (mtvec_val),
        .mepc_o        (mepc_val),
        .mstatus_mie_o (mstatus_mie_val),
        .mie_o         (mie_val),
        .mip_o         (mip_val),
        .irq_ext_sync  (irq_ext_sync),
        .irq_tmr_sync  (irq_tmr_sync),
        .instret_inc   (instret_inc)
    );

    // ---------------------------------------------------------------
    // Branch condition logic (combinational)
    // ---------------------------------------------------------------
    reg branch_cond;
    always @(*) begin
        case (dec_funct3)
            3'b000:  branch_cond = (rs1_data_reg == rs2_data_reg);                    // BEQ
            3'b001:  branch_cond = (rs1_data_reg != rs2_data_reg);                    // BNE
            3'b100:  branch_cond = ($signed(rs1_data_reg) < $signed(rs2_data_reg));   // BLT
            3'b101:  branch_cond = ($signed(rs1_data_reg) >= $signed(rs2_data_reg));  // BGE
            3'b110:  branch_cond = (rs1_data_reg < rs2_data_reg);                     // BLTU
            3'b111:  branch_cond = (rs1_data_reg >= rs2_data_reg);                    // BGEU
            default: branch_cond = 1'b0;
        endcase
    end

    // ---------------------------------------------------------------
    // Load data extraction (combinational)
    // Section 4.5: select byte/halfword based on address low bits,
    // then sign/zero-extend based on funct3.
    // ---------------------------------------------------------------
    reg [31:0] load_result;
    reg [7:0]  load_byte;
    reg [15:0] load_half;

    always @(*) begin
        // Byte selection based on alu_result_reg[1:0]
        case (alu_result_reg[1:0])
            2'b00: load_byte = mem_rdata_reg[7:0];
            2'b01: load_byte = mem_rdata_reg[15:8];
            2'b10: load_byte = mem_rdata_reg[23:16];
            2'b11: load_byte = mem_rdata_reg[31:24];
        endcase

        // Halfword selection based on alu_result_reg[1]
        case (alu_result_reg[1])
            1'b0: load_half = mem_rdata_reg[15:0];
            1'b1: load_half = mem_rdata_reg[31:16];
        endcase

        // Sign/zero extension based on funct3
        case (dec_funct3)
            3'b000:  load_result = {{24{load_byte[7]}}, load_byte};    // LB
            3'b001:  load_result = {{16{load_half[15]}}, load_half};   // LH
            3'b010:  load_result = mem_rdata_reg;                      // LW
            3'b100:  load_result = {24'b0, load_byte};                 // LBU
            3'b101:  load_result = {16'b0, load_half};                 // LHU
            default: load_result = 32'b0;
        endcase
    end

    // ---------------------------------------------------------------
    // Store data formatting (combinational)
    // Section 4.4: byte/halfword replication + write strobe.
    // ---------------------------------------------------------------
    reg [31:0] store_wdata;
    reg [3:0]  store_wstrb;

    always @(*) begin
        case (dec_funct3[1:0])
            2'b00: begin  // SB
                store_wdata = {4{rs2_data_reg[7:0]}};
                case (alu_result_reg[1:0])
                    2'b00: store_wstrb = 4'b0001;
                    2'b01: store_wstrb = 4'b0010;
                    2'b10: store_wstrb = 4'b0100;
                    2'b11: store_wstrb = 4'b1000;
                endcase
            end
            2'b01: begin  // SH
                store_wdata = {2{rs2_data_reg[15:0]}};
                case (alu_result_reg[1])
                    1'b0: store_wstrb = 4'b0011;
                    1'b1: store_wstrb = 4'b1100;
                endcase
            end
            2'b10: begin  // SW
                store_wdata = rs2_data_reg;
                store_wstrb = 4'b1111;
            end
            default: begin
                store_wdata = 32'b0;
                store_wstrb = 4'b0000;
            end
        endcase
    end

    // ---------------------------------------------------------------
    // ALU operand and operation muxing (combinational, per section 3.3)
    // ---------------------------------------------------------------
    always @(*) begin
        // Defaults
        alu_op_a = rs1_data_reg;
        alu_op_b = dec_imm;
        alu_op   = ALU_ADD;

        if (dec_is_alu_reg) begin
            // R-type: operand_a = rs1, operand_b = rs2
            alu_op_a = rs1_data_reg;
            alu_op_b = rs2_data_reg;
            // alu_op from funct3/funct7
            case (dec_funct3)
                3'b000: alu_op = dec_funct7_bit5 ? ALU_SUB : ALU_ADD;
                3'b001: alu_op = ALU_SLL;
                3'b010: alu_op = ALU_SLT;
                3'b011: alu_op = ALU_SLTU;
                3'b100: alu_op = ALU_XOR;
                3'b101: alu_op = dec_funct7_bit5 ? ALU_SRA : ALU_SRL;
                3'b110: alu_op = ALU_OR;
                3'b111: alu_op = ALU_AND;
            endcase
        end else if (dec_is_alu_imm) begin
            // I-type ALU: operand_a = rs1, operand_b = imm
            alu_op_a = rs1_data_reg;
            alu_op_b = dec_imm;
            case (dec_funct3)
                3'b000: alu_op = ALU_ADD;  // ADDI
                3'b010: alu_op = ALU_SLT;  // SLTI
                3'b011: alu_op = ALU_SLTU; // SLTIU
                3'b100: alu_op = ALU_XOR;  // XORI
                3'b110: alu_op = ALU_OR;   // ORI
                3'b111: alu_op = ALU_AND;  // ANDI
                3'b001: alu_op = ALU_SLL;  // SLLI
                3'b101: alu_op = dec_funct7_bit5 ? ALU_SRA : ALU_SRL; // SRLI/SRAI
            endcase
        end else if (dec_is_lui) begin
            // LUI: 0 + imm
            alu_op_a = 32'b0;
            alu_op_b = dec_imm;
            alu_op   = ALU_ADD;
        end else if (dec_is_auipc) begin
            // AUIPC: PC + imm
            alu_op_a = pc;
            alu_op_b = dec_imm;
            alu_op   = ALU_ADD;
        end else if (dec_is_jal || dec_is_branch) begin
            // JAL / Branch: PC + imm (for target computation)
            alu_op_a = pc;
            alu_op_b = dec_imm;
            alu_op   = ALU_ADD;
        end else if (dec_is_jalr) begin
            // JALR: rs1 + imm
            alu_op_a = rs1_data_reg;
            alu_op_b = dec_imm;
            alu_op   = ALU_ADD;
        end else begin
            // Load / Store / default: rs1 + imm (address calc)
            alu_op_a = rs1_data_reg;
            alu_op_b = dec_imm;
            alu_op   = ALU_ADD;
        end
    end

    // ---------------------------------------------------------------
    // CSR new-value computation (combinational)
    // Per section 5.2: compute the value to write into the CSR.
    // ---------------------------------------------------------------
    reg [31:0] csr_new_val_comb;
    wire [31:0] csr_zimm;
    assign csr_zimm = {27'b0, instruction_reg[19:15]};

    always @(*) begin
        case (dec_funct3)
            3'b001:  csr_new_val_comb = rs1_data_reg;                // CSRRW
            3'b010:  csr_new_val_comb = csr_rdata | rs1_data_reg;    // CSRRS
            3'b011:  csr_new_val_comb = csr_rdata & ~rs1_data_reg;   // CSRRC
            3'b101:  csr_new_val_comb = csr_zimm;                    // CSRRWI
            3'b110:  csr_new_val_comb = csr_rdata | csr_zimm;        // CSRRSI
            3'b111:  csr_new_val_comb = csr_rdata & ~csr_zimm;       // CSRRCI
            default: csr_new_val_comb = 32'b0;
        endcase
    end

    // CSR write suppression logic (combinational)
    // CSRRS/CSRRC: don't write if rs1_addr == x0
    // CSRRSI/CSRRCI: don't write if uimm == 0
    // CSRRW/CSRRWI: always write
    reg csr_will_write;
    always @(*) begin
        case (dec_funct3)
            3'b001:  csr_will_write = 1'b1;                                  // CSRRW
            3'b010:  csr_will_write = (dec_rs1_addr != 5'b00000);             // CSRRS
            3'b011:  csr_will_write = (dec_rs1_addr != 5'b00000);             // CSRRC
            3'b101:  csr_will_write = 1'b1;                                  // CSRRWI
            3'b110:  csr_will_write = (instruction_reg[19:15] != 5'b00000);   // CSRRSI
            3'b111:  csr_will_write = (instruction_reg[19:15] != 5'b00000);   // CSRRCI
            default: csr_will_write = 1'b0;
        endcase
    end

    // ---------------------------------------------------------------
    // Misalignment checks (combinational, used in EXECUTE)
    // ---------------------------------------------------------------
    wire load_misaligned =
        (dec_is_load && dec_funct3 == 3'b010 && alu_result[1:0] != 2'b00) |   // LW
        (dec_is_load && (dec_funct3 == 3'b001 || dec_funct3 == 3'b101)
                     && alu_result[0] != 1'b0);                                // LH/LHU

    wire store_misaligned =
        (dec_is_store && dec_funct3 == 3'b010 && alu_result[1:0] != 2'b00) |  // SW
        (dec_is_store && dec_funct3 == 3'b001 && alu_result[0] != 1'b0);      // SH

    // JALR target: (rs1 + imm) with bit 0 cleared
    wire [31:0] jalr_target = (rs1_data_reg + dec_imm) & 32'hFFFF_FFFE;

    // CSR access illegal conditions (in EXECUTE):
    // - CSR address not valid
    // - Write to read-only CSR when instruction actually writes
    wire csr_access_illegal = dec_is_csr &&
        (!csr_valid_addr || (csr_readonly && csr_will_write));

    // ---------------------------------------------------------------
    // PC + 4 (used for link address and sequential flow)
    // ---------------------------------------------------------------
    wire [31:0] pc_plus_4 = pc + 32'd4;

    // ---------------------------------------------------------------
    // Interrupt pending logic (used at end of WRITEBACK)
    // ---------------------------------------------------------------
    wire irq_pending = mstatus_mie_val &&
                       ((mie_val[11] & mip_val[11]) | (mie_val[7] & mip_val[7]));

    // ---------------------------------------------------------------
    // Main FSM
    // ---------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            // Reset state
            pc               <= RESET_VECTOR;
            state            <= S_FETCH;
            mem_valid        <= 1'b0;
            instruction_reg  <= 32'b0;
            rs1_data_reg     <= 32'b0;
            rs2_data_reg     <= 32'b0;
            alu_result_reg   <= 32'b0;
            mem_rdata_reg    <= 32'b0;
            csr_old_reg      <= 32'b0;
            csr_new_reg      <= 32'b0;
            branch_target_reg <= 32'b0;
            trap_cause_reg   <= 32'b0;
            trap_val_reg     <= 32'b0;
            trap_pc_reg      <= 32'b0;
            branch_taken_flag <= 1'b0;
            csr_do_write     <= 1'b0;
            rf_wr_en         <= 1'b0;
            rf_wr_addr       <= 5'b0;
            rf_wr_data       <= 32'b0;
            csr_wen          <= 1'b0;
            csr_wdata_to_unit <= 32'b0;
            trap_enter       <= 1'b0;
            mret_exec        <= 1'b0;
            instret_inc      <= 1'b0;
            mem_addr         <= 32'b0;
            mem_wdata        <= 32'b0;
            mem_wstrb        <= 4'b0;
        end else begin
            // Default: deassert one-cycle pulses
            rf_wr_en    <= 1'b0;
            csr_wen     <= 1'b0;
            trap_enter  <= 1'b0;
            mret_exec   <= 1'b0;
            instret_inc <= 1'b0;

            case (state)
                // ---------------------------------------------------
                // FETCH: drive PC onto memory bus, latch instruction
                // ---------------------------------------------------
                S_FETCH: begin
                    mem_addr  <= pc;
                    mem_wstrb <= 4'b0000;
                    mem_valid <= 1'b1;
                    mem_wdata <= 32'b0;

                    if (mem_ready && mem_valid) begin
                        instruction_reg <= mem_rdata;
                        mem_valid       <= 1'b0;
                        state           <= S_DECODE;
                    end
                end

                // ---------------------------------------------------
                // DECODE: read registers, check for traps/special insns
                // ---------------------------------------------------
                S_DECODE: begin
                    // Latch register file outputs
                    rs1_data_reg <= rf_rs1_data;
                    rs2_data_reg <= rf_rs2_data;

                    // Check decode-time traps and special instructions
                    if (instruction_reg == 32'h0000_0000) begin
                        // All-zeros traps as illegal instruction
                        trap_cause_reg <= 32'd2;
                        trap_val_reg   <= instruction_reg;
                        trap_pc_reg    <= pc;
                        state          <= S_TRAP_ENTRY;
                    end else if (dec_is_illegal) begin
                        trap_cause_reg <= 32'd2;
                        trap_val_reg   <= instruction_reg;
                        trap_pc_reg    <= pc;
                        state          <= S_TRAP_ENTRY;
                    end else if (dec_is_ecall) begin
                        trap_cause_reg <= 32'd11;
                        trap_val_reg   <= 32'b0;
                        trap_pc_reg    <= pc;
                        state          <= S_TRAP_ENTRY;
                    end else if (dec_is_ebreak) begin
                        trap_cause_reg <= 32'd3;
                        trap_val_reg   <= 32'b0;
                        trap_pc_reg    <= pc;
                        state          <= S_TRAP_ENTRY;
                    end else if (dec_is_mret) begin
                        state <= S_MRET;
                    end else if (dec_is_fence || dec_is_wfi) begin
                        // Treated as NOP; PC advances by 4 in WRITEBACK
                        state <= S_WRITEBACK;
                    end else begin
                        state <= S_EXECUTE;
                    end
                end

                // ---------------------------------------------------
                // EXECUTE: ALU, address calc, branch eval, CSR read
                // ---------------------------------------------------
                S_EXECUTE: begin
                    // ALU result is combinationally available via alu_result
                    alu_result_reg <= alu_result;

                    if (dec_is_jal) begin
                        // Target = PC + imm (from ALU)
                        branch_target_reg <= alu_result;
                        // rd gets PC + 4
                        alu_result_reg <= pc_plus_4;

                        if (alu_result[1]) begin
                            // Misaligned target
                            trap_cause_reg <= 32'd0;
                            trap_val_reg   <= alu_result;
                            trap_pc_reg    <= pc;
                            state          <= S_TRAP_ENTRY;
                        end else begin
                            state <= S_WRITEBACK;
                        end

                    end else if (dec_is_jalr) begin
                        // Target = (rs1 + imm) & ~1
                        branch_target_reg <= jalr_target;
                        // rd gets PC + 4
                        alu_result_reg <= pc_plus_4;

                        if (jalr_target[1]) begin
                            trap_cause_reg <= 32'd0;
                            trap_val_reg   <= jalr_target;
                            trap_pc_reg    <= pc;
                            state          <= S_TRAP_ENTRY;
                        end else begin
                            state <= S_WRITEBACK;
                        end

                    end else if (dec_is_branch) begin
                        // Target = PC + imm (from ALU)
                        branch_target_reg <= alu_result;

                        if (branch_cond && alu_result[1]) begin
                            // Taken but misaligned
                            trap_cause_reg <= 32'd0;
                            trap_val_reg   <= alu_result;
                            trap_pc_reg    <= pc;
                            state          <= S_TRAP_ENTRY;
                        end else begin
                            branch_taken_flag <= branch_cond;
                            state             <= S_WRITEBACK;
                        end

                    end else if (dec_is_load) begin
                        alu_result_reg <= alu_result;  // effective address

                        if (load_misaligned) begin
                            trap_cause_reg <= 32'd4;
                            trap_val_reg   <= alu_result;
                            trap_pc_reg    <= pc;
                            state          <= S_TRAP_ENTRY;
                        end else begin
                            state <= S_MEM_READ;
                        end

                    end else if (dec_is_store) begin
                        alu_result_reg <= alu_result;  // effective address

                        if (store_misaligned) begin
                            trap_cause_reg <= 32'd6;
                            trap_val_reg   <= alu_result;
                            trap_pc_reg    <= pc;
                            state          <= S_TRAP_ENTRY;
                        end else begin
                            state <= S_MEM_WRITE;
                        end

                    end else if (dec_is_csr) begin
                        // CSR read (combinational from CSR unit)
                        csr_old_reg  <= csr_rdata;
                        csr_new_reg  <= csr_new_val_comb;
                        csr_do_write <= csr_will_write;

                        if (csr_access_illegal) begin
                            trap_cause_reg <= 32'd2;
                            trap_val_reg   <= instruction_reg;
                            trap_pc_reg    <= pc;
                            state          <= S_TRAP_ENTRY;
                        end else begin
                            state <= S_WRITEBACK;
                        end

                    end else begin
                        // R-type, I-type ALU, LUI, AUIPC
                        state <= S_WRITEBACK;
                    end
                end

                // ---------------------------------------------------
                // MEM_READ: drive address, latch read data
                // ---------------------------------------------------
                S_MEM_READ: begin
                    mem_addr  <= {alu_result_reg[31:2], 2'b00};
                    mem_wstrb <= 4'b0000;
                    mem_valid <= 1'b1;
                    mem_wdata <= 32'b0;

                    if (mem_ready && mem_valid) begin
                        mem_rdata_reg <= mem_rdata;
                        mem_valid     <= 1'b0;
                        state         <= S_WRITEBACK;
                    end
                end

                // ---------------------------------------------------
                // MEM_WRITE: drive address + data + strobe
                // ---------------------------------------------------
                S_MEM_WRITE: begin
                    mem_addr  <= {alu_result_reg[31:2], 2'b00};
                    mem_wdata <= store_wdata;
                    mem_wstrb <= store_wstrb;
                    mem_valid <= 1'b1;

                    if (mem_ready && mem_valid) begin
                        mem_valid <= 1'b0;
                        state    <= S_WRITEBACK;
                    end
                end

                // ---------------------------------------------------
                // WRITEBACK: write rd, update PC, retire, check irqs
                // ---------------------------------------------------
                S_WRITEBACK: begin
                    // 1. Register write
                    rf_wr_en   <= 1'b0;
                    rf_wr_addr <= dec_rd_addr;

                    if (dec_is_alu_reg || dec_is_alu_imm || dec_is_lui || dec_is_auipc) begin
                        if (dec_rd_addr != 5'b00000) begin
                            rf_wr_en   <= 1'b1;
                            rf_wr_data <= alu_result_reg;
                        end
                    end else if (dec_is_jal || dec_is_jalr) begin
                        if (dec_rd_addr != 5'b00000) begin
                            rf_wr_en   <= 1'b1;
                            rf_wr_data <= alu_result_reg;  // holds PC+4
                        end
                    end else if (dec_is_load) begin
                        if (dec_rd_addr != 5'b00000) begin
                            rf_wr_en   <= 1'b1;
                            rf_wr_data <= load_result;
                        end
                    end else if (dec_is_csr) begin
                        if (dec_rd_addr != 5'b00000) begin
                            rf_wr_en   <= 1'b1;
                            rf_wr_data <= csr_old_reg;
                        end
                    end
                    // Branch, Store, FENCE, WFI: no register write

                    // 2. CSR write (in WRITEBACK)
                    if (dec_is_csr && csr_do_write) begin
                        csr_wen          <= 1'b1;
                        csr_wdata_to_unit <= csr_new_reg;
                    end

                    // 3. PC update
                    if (dec_is_jal || dec_is_jalr) begin
                        pc <= branch_target_reg;
                    end else if (dec_is_branch && branch_taken_flag) begin
                        pc <= branch_target_reg;
                    end else begin
                        pc <= pc_plus_4;
                    end

                    // 4. Instruction retire
                    instret_inc <= 1'b1;

                    // 5. Interrupt check
                    if (irq_pending) begin
                        // Determine next_pc for mepc
                        if (dec_is_jal || dec_is_jalr) begin
                            trap_pc_reg <= branch_target_reg;
                        end else if (dec_is_branch && branch_taken_flag) begin
                            trap_pc_reg <= branch_target_reg;
                        end else begin
                            trap_pc_reg <= pc_plus_4;
                        end

                        trap_val_reg      <= 32'b0;

                        // Priority: external > timer
                        if (mie_val[11] & mip_val[11]) begin
                            trap_cause_reg <= 32'h8000_000B;
                        end else begin
                            trap_cause_reg <= 32'h8000_0007;
                        end

                        state <= S_TRAP_ENTRY;
                    end else begin
                        state <= S_FETCH;
                    end
                end

                // ---------------------------------------------------
                // TRAP_ENTRY: save mepc/mcause, disable interrupts, jump
                // ---------------------------------------------------
                S_TRAP_ENTRY: begin
                    trap_enter <= 1'b1;
                    // The CSR unit handles mepc/mcause/mtval/mstatus
                    // via its trap_enter input.
                    pc    <= mtvec_val;  // mtvec with low 2 bits cleared
                    state <= S_FETCH;
                end

                // ---------------------------------------------------
                // MRET: restore mepc, re-enable interrupts
                // ---------------------------------------------------
                S_MRET: begin
                    mret_exec <= 1'b1;
                    pc        <= mepc_val;
                    state     <= S_FETCH;
                end

                default: begin
                    state <= S_FETCH;
                end
            endcase
        end
    end

endmodule
