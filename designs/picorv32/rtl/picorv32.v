module picorv32 #(
    parameter [31:0] RESET_VECTOR = 32'h0000_0000
) (
    input  wire        clk,
    input  wire        rst,

    // Memory interface — valid/ready handshake
    output reg         mem_valid,
    input  wire        mem_ready,
    output reg  [31:0] mem_addr,
    output reg  [31:0] mem_wdata,
    output reg  [ 3:0] mem_wstrb,
    input  wire [31:0] mem_rdata,

    // Interrupts
    input  wire        irq_external,
    input  wire        irq_timer
);

    // ---------------------------------------------------------------
    // State encoding
    // ---------------------------------------------------------------
    localparam S_FETCH   = 3'd0,
               S_DECODE  = 3'd1,
               S_EXEC    = 3'd2,
               S_MEM     = 3'd3,
               S_WB      = 3'd4,
               S_TRAP    = 3'd5;

    reg [2:0] state;

    // ---------------------------------------------------------------
    // Architectural registers
    // ---------------------------------------------------------------
    reg [31:0] pc;
    reg [31:0] regfile [0:31];

    reg [31:0] instr;

    // Decode fields
    wire [6:0]  opcode = instr[6:0];
    wire [4:0]  rd     = instr[11:7];
    wire [2:0]  funct3 = instr[14:12];
    wire [4:0]  rs1    = instr[19:15];
    wire [4:0]  rs2    = instr[24:20];
    wire [6:0]  funct7 = instr[31:25];

    // Immediate generators
    wire [31:0] imm_i = {{20{instr[31]}}, instr[31:20]};
    wire [31:0] imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    wire [31:0] imm_b = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    wire [31:0] imm_u = {instr[31:12], 12'b0};
    wire [31:0] imm_j = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};

    // Opcode constants
    localparam OP_LUI    = 7'b0110111,
               OP_AUIPC  = 7'b0010111,
               OP_JAL    = 7'b1101111,
               OP_JALR   = 7'b1100111,
               OP_BRANCH = 7'b1100011,
               OP_LOAD   = 7'b0000011,
               OP_STORE  = 7'b0100011,
               OP_IMM    = 7'b0010011,
               OP_REG    = 7'b0110011,
               OP_FENCE  = 7'b0001111,
               OP_SYSTEM = 7'b1110011;

    // ---------------------------------------------------------------
    // Register reads (x0 hardwired to 0)
    // ---------------------------------------------------------------
    wire [31:0] rs1_val = (rs1 == 5'd0) ? 32'd0 : regfile[rs1];
    wire [31:0] rs2_val = (rs2 == 5'd0) ? 32'd0 : regfile[rs2];

    // ---------------------------------------------------------------
    // ALU
    // ---------------------------------------------------------------
    reg [31:0] alu_result;
    wire [4:0] shamt = (opcode == OP_IMM) ? imm_i[4:0] : rs2_val[4:0];
    wire       is_sub = (opcode == OP_REG) && funct7[5];

    always @(*) begin
        case (funct3)
            3'b000: alu_result = is_sub ? (rs1_val - rs2_val) :
                     (rs1_val + ((opcode == OP_IMM) ? imm_i : rs2_val));
            3'b001: alu_result = rs1_val << shamt;
            3'b010: alu_result = {31'd0, $signed(rs1_val) < $signed((opcode == OP_IMM) ? imm_i : rs2_val)};
            3'b011: alu_result = {31'd0, rs1_val < ((opcode == OP_IMM) ? imm_i : rs2_val)};
            3'b100: alu_result = rs1_val ^ ((opcode == OP_IMM) ? imm_i : rs2_val);
            3'b101: begin
                     if (funct7[5])
                         alu_result = $signed(rs1_val) >>> shamt;  // SRA
                     else
                         alu_result = rs1_val >> shamt;            // SRL
                     end
            3'b110: alu_result = rs1_val | ((opcode == OP_IMM) ? imm_i : rs2_val);
            3'b111: alu_result = rs1_val & ((opcode == OP_IMM) ? imm_i : rs2_val);
            default: alu_result = 32'd0;
        endcase
    end

    // ---------------------------------------------------------------
    // Branch condition
    // ---------------------------------------------------------------
    reg branch_taken;
    always @(*) begin
        case (funct3)
            3'b000:  branch_taken = (rs1_val == rs2_val);
            3'b001:  branch_taken = (rs1_val != rs2_val);
            3'b100:  branch_taken = ($signed(rs1_val) < $signed(rs2_val));
            3'b101:  branch_taken = ($signed(rs1_val) >= $signed(rs2_val));
            3'b110:  branch_taken = (rs1_val < rs2_val);
            3'b111:  branch_taken = (rs1_val >= rs2_val);
            default: branch_taken = 1'b0;
        endcase
    end

    // ---------------------------------------------------------------
    // CSRs — machine-mode only
    // ---------------------------------------------------------------
    reg [31:0] csr_mstatus;
    reg [31:0] csr_mtvec;
    reg [31:0] csr_mepc;
    reg [31:0] csr_mcause;
    reg [31:0] csr_mtval;
    reg [31:0] csr_mie;
    reg [31:0] csr_mip;
    reg [63:0] csr_mcycle;
    reg [63:0] csr_minstret;

    // CSR addresses
    localparam CSR_MSTATUS   = 12'h300,
               CSR_MIE       = 12'h304,
               CSR_MTVEC     = 12'h305,
               CSR_MEPC      = 12'h341,
               CSR_MCAUSE    = 12'h342,
               CSR_MTVAL     = 12'h343,
               CSR_MIP       = 12'h344,
               CSR_MCYCLE    = 12'hB00,
               CSR_MCYCLEH   = 12'hB80,
               CSR_MINSTRET  = 12'hB02,
               CSR_MINSTRETH = 12'hB82;

    wire [11:0] csr_addr = instr[31:20];

    reg [31:0] csr_rdata;
    always @(*) begin
        case (csr_addr)
            CSR_MSTATUS:   csr_rdata = csr_mstatus;
            CSR_MIE:       csr_rdata = csr_mie;
            CSR_MTVEC:     csr_rdata = csr_mtvec;
            CSR_MEPC:      csr_rdata = csr_mepc;
            CSR_MCAUSE:    csr_rdata = csr_mcause;
            CSR_MTVAL:     csr_rdata = csr_mtval;
            CSR_MIP:       csr_rdata = csr_mip;
            CSR_MCYCLE:    csr_rdata = csr_mcycle[31:0];
            CSR_MCYCLEH:   csr_rdata = csr_mcycle[63:32];
            CSR_MINSTRET:  csr_rdata = csr_minstret[31:0];
            CSR_MINSTRETH: csr_rdata = csr_minstret[63:32];
            default:       csr_rdata = 32'd0;
        endcase
    end

    // CSR write value
    reg [31:0] csr_wdata;
    always @(*) begin
        case (funct3[1:0])
            2'b01: csr_wdata = rs1_val;                     // CSRRW
            2'b10: csr_wdata = csr_rdata | rs1_val;         // CSRRS
            2'b11: csr_wdata = csr_rdata & ~rs1_val;        // CSRRC
            default: csr_wdata = rs1_val;
        endcase
        if (funct3[2]) begin
            // Immediate forms (CSRRWI, CSRRSI, CSRRCI)
            case (funct3[1:0])
                2'b01: csr_wdata = {27'd0, rs1};
                2'b10: csr_wdata = csr_rdata | {27'd0, rs1};
                2'b11: csr_wdata = csr_rdata & ~{27'd0, rs1};
                default: csr_wdata = {27'd0, rs1};
            endcase
        end
    end

    // Trap pending
    wire mie_global = csr_mstatus[3];
    wire irq_pending = mie_global && (
        (irq_external && csr_mie[11] && csr_mip[11]) ||
        (irq_timer    && csr_mie[7]  && csr_mip[7])
    );

    // ---------------------------------------------------------------
    // Load data alignment
    // ---------------------------------------------------------------
    reg [31:0] load_data;
    wire [1:0] load_offset = 2'b00;

    always @(*) begin
        case (funct3)
            3'b000: begin // LB
                case (load_offset)
                    2'b00: load_data = {{24{mem_rdata[ 7]}}, mem_rdata[ 7: 0]};
                    2'b01: load_data = {{24{mem_rdata[15]}}, mem_rdata[15: 8]};
                    2'b10: load_data = {{24{mem_rdata[23]}}, mem_rdata[23:16]};
                    2'b11: load_data = {{24{mem_rdata[31]}}, mem_rdata[31:24]};
                endcase
            end
            3'b001: begin // LH
                case (load_offset[1])
                    1'b0: load_data = {{16{mem_rdata[15]}}, mem_rdata[15: 0]};
                    1'b1: load_data = {{16{mem_rdata[31]}}, mem_rdata[31:16]};
                endcase
            end
            3'b010: load_data = mem_rdata; // LW
            3'b100: begin // LBU
                case (load_offset)
                    2'b00: load_data = {24'd0, mem_rdata[ 7: 0]};
                    2'b01: load_data = {24'd0, mem_rdata[15: 8]};
                    2'b10: load_data = {24'd0, mem_rdata[23:16]};
                    2'b11: load_data = {24'd0, mem_rdata[31:24]};
                endcase
            end
            3'b101: begin // LHU
                case (load_offset[1])
                    1'b0: load_data = {16'd0, mem_rdata[15: 0]};
                    1'b1: load_data = {16'd0, mem_rdata[31:16]};
                endcase
            end
            default: load_data = mem_rdata;
        endcase
    end

    // ---------------------------------------------------------------
    // Store data / strobe alignment
    // ---------------------------------------------------------------
    reg [31:0] store_data;
    reg [ 3:0] store_strb;
    wire [1:0] store_offset = 2'b00;

    always @(*) begin
        case (funct3)
            3'b000: begin // SB
                case (store_offset)
                    2'b00: begin store_data = {24'd0, rs2_val[7:0]};       store_strb = 4'b0001; end
                    2'b01: begin store_data = {16'd0, rs2_val[7:0], 8'd0}; store_strb = 4'b0010; end
                    2'b10: begin store_data = {8'd0, rs2_val[7:0], 16'd0}; store_strb = 4'b0100; end
                    2'b11: begin store_data = {rs2_val[7:0], 24'd0};       store_strb = 4'b1000; end
                endcase
            end
            3'b001: begin // SH
                case (store_offset[1])
                    1'b0: begin store_data = {16'd0, rs2_val[15:0]};       store_strb = 4'b0011; end
                    1'b1: begin store_data = {rs2_val[15:0], 16'd0};       store_strb = 4'b1100; end
                endcase
            end
            3'b010: begin // SW
                store_data = rs2_val;
                store_strb = 4'b1111;
            end
            default: begin
                store_data = 32'd0;
                store_strb = 4'b0000;
            end
        endcase
    end

    // ---------------------------------------------------------------
    // Writeback value
    // ---------------------------------------------------------------
    reg [31:0] wb_data;
    reg        wb_en;

    // ---------------------------------------------------------------
    // Illegal instruction detection
    // ---------------------------------------------------------------
    reg illegal_instr;
    always @(*) begin
        illegal_instr = 1'b0;
        case (opcode)
            OP_LUI, OP_AUIPC, OP_JAL: ;
            OP_JALR:   if (funct3 != 3'b000) illegal_instr = 1'b1;
            OP_BRANCH: if (funct3 == 3'b010 || funct3 == 3'b011) illegal_instr = 1'b1;
            OP_LOAD:   if (funct3 == 3'b011 || funct3 == 3'b110 || funct3 == 3'b111) illegal_instr = 1'b1;
            OP_STORE:  if (funct3 != 3'b000 && funct3 != 3'b001 && funct3 != 3'b010) illegal_instr = 1'b1;
            OP_IMM: begin
                if (funct3 == 3'b001 && funct7 != 7'b0000000) illegal_instr = 1'b1;
                if (funct3 == 3'b101 && funct7 != 7'b0000000 && funct7 != 7'b0100000) illegal_instr = 1'b1;
            end
            OP_REG: begin
                if (funct7 != 7'b0000000 && funct7 != 7'b0100000) illegal_instr = 1'b1;
                if (funct7 == 7'b0100000 && funct3 != 3'b000 && funct3 != 3'b101) illegal_instr = 1'b1;
            end
            OP_FENCE:  ;
            OP_SYSTEM: begin
                if (funct3 == 3'b000) begin
                    if (instr[31:7] != 25'b0000000000000000000000000 && // ECALL
                        instr[31:7] != {25{1'b0}} + 25'b0000000000010000000000000)  // EBREAK: imm=1
                        if (instr != 32'b00110000001000000000000001110011) // MRET
                            illegal_instr = 1'b1;
                end else if (funct3[1:0] == 2'b00) begin
                    illegal_instr = 1'b1;
                end
            end
            default: illegal_instr = 1'b1;
        endcase
    end

    // ---------------------------------------------------------------
    // ECALL / EBREAK / MRET detection
    // ---------------------------------------------------------------
    wire is_ecall  = (opcode == OP_SYSTEM) && (funct3 == 3'b000) && (instr[31:20] == 12'h000);
    wire is_ebreak = (opcode == OP_SYSTEM) && (funct3 == 3'b000) && (instr[31:20] == 12'h001);
    wire is_mret   = (opcode == OP_SYSTEM) && (funct3 == 3'b000) && (instr[31:20] == 12'h302);
    wire is_csr    = (opcode == OP_SYSTEM) && (funct3[1:0] != 2'b00);

    // ---------------------------------------------------------------
    // Main FSM
    // ---------------------------------------------------------------
    integer i;

    always @(posedge clk) begin
        if (rst) begin
            state       <= S_FETCH;
            pc          <= RESET_VECTOR;
            mem_valid   <= 1'b0;
            mem_addr    <= 32'd0;
            mem_wdata   <= 32'd0;
            mem_wstrb   <= 4'd0;
            instr       <= 32'd0;
            wb_en       <= 1'b0;
            wb_data     <= 32'd0;

            csr_mstatus  <= 32'd0;
            csr_mtvec    <= 32'd0;
            csr_mepc     <= 32'd0;
            csr_mcause   <= 32'd0;
            csr_mtval    <= 32'd0;
            csr_mie      <= 32'd0;
            csr_mip      <= 32'd0;
            csr_mcycle   <= 64'd0;
            csr_minstret <= 64'd0;

            for (i = 0; i < 32; i = i + 1)
                regfile[i] <= 32'd0;
        end else begin
            csr_mcycle <= csr_mcycle + 64'd1;

            // Update mip from external signals
            csr_mip[11] <= irq_external;
            csr_mip[7]  <= irq_timer;

            case (state)
                // ---------------------------------------------------
                S_FETCH: begin
                    mem_valid <= 1'b1;
                    mem_addr  <= pc;
                    mem_wstrb <= 4'b0000;
                    if (mem_valid && mem_ready) begin
                        instr     <= mem_rdata;
                        mem_valid <= 1'b0;
                        state     <= S_DECODE;
                    end
                end

                // ---------------------------------------------------
                S_DECODE: begin
                    wb_en <= 1'b0;

                    if (irq_pending) begin
                        csr_mepc    <= pc;
                        csr_mcause  <= (csr_mip[11] && csr_mie[11]) ?
                                       {1'b1, 31'd11} : {1'b1, 31'd7};
                        csr_mstatus[7]  <= csr_mstatus[3]; // MPIE = MIE
                        csr_mstatus[3]  <= 1'b0;           // MIE = 0
                        pc    <= csr_mtvec;
                        state <= S_FETCH;
                    end else if (illegal_instr) begin
                        state <= S_TRAP;
                    end else begin
                        state <= S_EXEC;
                    end
                end

                // ---------------------------------------------------
                S_EXEC: begin
                    case (opcode)
                        OP_LUI: begin
                            wb_data <= imm_u;
                            wb_en   <= (rd != 5'd0);
                            pc      <= pc + 32'd4;
                            state   <= S_WB;
                        end

                        OP_AUIPC: begin
                            wb_data <= pc + imm_u;
                            wb_en   <= (rd != 5'd0);
                            pc      <= pc + 32'd4;
                            state   <= S_WB;
                        end

                        OP_JAL: begin
                            wb_data <= pc + 32'd4;
                            wb_en   <= (rd != 5'd0);
                            pc      <= pc + imm_j;
                            state   <= S_WB;
                        end

                        OP_JALR: begin
                            wb_data <= pc + 32'd4;
                            wb_en   <= (rd != 5'd0);
                            pc      <= (rs1_val + imm_i) & 32'hFFFF_FFFE;
                            state   <= S_WB;
                        end

                        OP_BRANCH: begin
                            if (branch_taken)
                                pc <= pc + imm_b;
                            else
                                pc <= pc + 32'd4;
                            state <= S_FETCH;
                        end

                        OP_LOAD: begin
                            mem_valid <= 1'b1;
                            mem_addr  <= rs1_val + imm_i;
                            mem_wstrb <= 4'b0000;
                            state     <= S_MEM;
                        end

                        OP_STORE: begin
                            mem_valid <= 1'b1;
                            mem_addr  <= rs1_val + imm_s;
                            mem_wdata <= store_data;
                            mem_wstrb <= store_strb;
                            state     <= S_MEM;
                        end

                        OP_IMM, OP_REG: begin
                            wb_data <= alu_result;
                            wb_en   <= (rd != 5'd0);
                            pc      <= pc + 32'd4;
                            state   <= S_WB;
                        end

                        OP_FENCE: begin
                            pc    <= pc + 32'd4;
                            state <= S_FETCH;
                        end

                        OP_SYSTEM: begin
                            if (is_ecall) begin
                                csr_mepc   <= pc;
                                csr_mcause <= 32'd11; // Environment call from M-mode
                                csr_mtval  <= 32'd0;
                                csr_mstatus[7] <= csr_mstatus[3];
                                csr_mstatus[3] <= 1'b0;
                                pc    <= csr_mtvec;
                                state <= S_FETCH;
                            end else if (is_ebreak) begin
                                csr_mepc   <= pc;
                                csr_mcause <= 32'd3; // Breakpoint
                                csr_mtval  <= 32'd0;
                                csr_mstatus[7] <= csr_mstatus[3];
                                csr_mstatus[3] <= 1'b0;
                                pc    <= csr_mtvec;
                                state <= S_FETCH;
                            end else if (is_mret) begin
                                pc <= csr_mepc;
                                csr_mstatus[3] <= csr_mstatus[7];
                                csr_mstatus[7] <= 1'b1;
                                state <= S_FETCH;
                            end else if (is_csr) begin
                                wb_data <= csr_rdata;
                                wb_en   <= (rd != 5'd0);
                                // CSR write
                                if (funct3[1:0] != 2'b00) begin
                                    case (csr_addr)
                                        CSR_MSTATUS:  csr_mstatus <= csr_wdata;
                                        CSR_MIE:      csr_mie     <= csr_wdata;
                                        CSR_MTVEC:    csr_mtvec   <= csr_wdata;
                                        CSR_MEPC:     csr_mepc    <= csr_wdata;
                                        CSR_MCAUSE:   csr_mcause  <= csr_wdata;
                                        CSR_MTVAL:    csr_mtval   <= csr_wdata;
                                        CSR_MCYCLE:   csr_mcycle[31:0]    <= csr_wdata;
                                        CSR_MCYCLEH:  csr_mcycle[63:32]   <= csr_wdata;
                                        CSR_MINSTRET: csr_minstret[31:0]  <= csr_wdata;
                                        CSR_MINSTRETH:csr_minstret[63:32] <= csr_wdata;
                                        default: ;
                                    endcase
                                end
                                pc    <= pc + 32'd4;
                                state <= S_WB;
                            end else begin
                                state <= S_TRAP;
                            end
                        end

                        default: begin
                            state <= S_TRAP;
                        end
                    endcase
                end

                // ---------------------------------------------------
                S_MEM: begin
                    if (mem_valid && mem_ready) begin
                        mem_valid <= 1'b0;
                        if (opcode == OP_LOAD) begin
                            wb_data <= load_data;
                            wb_en   <= (rd != 5'd0);
                            pc      <= pc + 32'd4;
                            state   <= S_WB;
                        end else begin
                            pc    <= pc + 32'd4;
                            state <= S_FETCH;
                        end
                    end
                end

                // ---------------------------------------------------
                S_WB: begin
                    if (wb_en) begin
                        regfile[rd] <= wb_data;
                    end
                    csr_minstret <= csr_minstret + 64'd1;
                    wb_en <= 1'b0;
                    state <= S_FETCH;
                end

                // ---------------------------------------------------
                S_TRAP: begin
                    csr_mepc   <= pc;
                    csr_mcause <= 32'd2; // Illegal instruction
                    csr_mtval  <= instr;
                    csr_mstatus[7] <= csr_mstatus[3];
                    csr_mstatus[3] <= 1'b0;
                    pc    <= csr_mtvec;
                    state <= S_FETCH;
                end

                default: state <= S_FETCH;
            endcase
        end
    end

endmodule
