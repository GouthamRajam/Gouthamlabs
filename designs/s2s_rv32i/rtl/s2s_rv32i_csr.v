// Provenance: agent-generated (Phase 1.5 Pillar A)
//
// s2s_rv32i_csr.v — CSR unit for the s2s_rv32i RISC-V core.
// Implements all CSRs from architecture.md section 5.1, cycle/instret
// counters, and trap entry/return logic.

module s2s_rv32i_csr (
    input  wire        clk,
    input  wire        rst_n,

    // CSR read/write interface (active in EXECUTE/WRITEBACK)
    input  wire [11:0] csr_addr,
    output reg  [31:0] csr_rdata,       // combinational read
    input  wire        csr_wen,         // write enable (pulsed in WRITEBACK)
    input  wire [31:0] csr_wdata,       // new CSR value

    // CSR address validation
    output wire        csr_valid,       // 1 if csr_addr maps to a known CSR
    output wire        csr_readonly,    // 1 if csr_addr is read-only

    // Trap entry interface (active in TRAP_ENTRY)
    input  wire        trap_enter,      // pulse: save trap state
    input  wire [31:0] trap_mepc,       // PC to save in mepc
    input  wire [31:0] trap_mcause,     // cause code
    input  wire [31:0] trap_mtval,      // trap value

    // MRET interface
    input  wire        mret_exec,       // pulse: execute MRET

    // Outputs to FSM
    output wire [31:0] mtvec_o,         // trap vector address
    output wire [31:0] mepc_o,          // saved PC for MRET
    output wire        mstatus_mie_o,   // current MIE bit
    output wire [31:0] mie_o,           // interrupt enable register
    output wire [31:0] mip_o,           // interrupt pending register

    // Interrupt pending inputs (synchronized)
    input  wire        irq_ext_sync,
    input  wire        irq_tmr_sync,

    // Counter control
    input  wire        instret_inc      // pulse when instruction retires
);

    // ---------------------------------------------------------------
    // CSR address constants
    // ---------------------------------------------------------------
    localparam ADDR_MSTATUS   = 12'h300;
    localparam ADDR_MISA      = 12'h301;
    localparam ADDR_MIE       = 12'h304;
    localparam ADDR_MTVEC     = 12'h305;
    localparam ADDR_MSCRATCH  = 12'h340;
    localparam ADDR_MEPC      = 12'h341;
    localparam ADDR_MCAUSE    = 12'h342;
    localparam ADDR_MTVAL     = 12'h343;
    localparam ADDR_MIP       = 12'h344;
    localparam ADDR_CYCLE     = 12'hC00;
    localparam ADDR_TIME      = 12'hC01;
    localparam ADDR_INSTRET   = 12'hC02;
    localparam ADDR_CYCLEH    = 12'hC80;
    localparam ADDR_TIMEH     = 12'hC81;
    localparam ADDR_INSTRETH  = 12'hC82;
    localparam ADDR_MVENDORID = 12'hF11;
    localparam ADDR_MARCHID   = 12'hF12;
    localparam ADDR_MIMPID    = 12'hF13;
    localparam ADDR_MHARTID   = 12'hF14;

    // ---------------------------------------------------------------
    // Internal CSR registers
    // ---------------------------------------------------------------
    reg        mstatus_mie;
    reg        mstatus_mpie;
    reg [31:0] mie_reg;
    reg [31:2] mtvec_reg;
    reg [31:0] mscratch_reg;
    reg [31:0] mepc_reg;
    reg [31:0] mcause_reg;
    reg [31:0] mtval_reg;

    // 64-bit counters
    reg [63:0] cycle_counter;
    reg [63:0] instret_counter;

    // ---------------------------------------------------------------
    // mip is assembled combinationally from synchronized interrupt inputs
    // ---------------------------------------------------------------
    assign mip_o = {20'b0, irq_ext_sync, 3'b0, irq_tmr_sync, 7'b0};

    // ---------------------------------------------------------------
    // mstatus assembled from constituent bits
    // Bits 12:11 = MPP = 2'b11 (always M-mode)
    // Bit 7 = MPIE, Bit 3 = MIE
    // ---------------------------------------------------------------
    wire [31:0] mstatus_val;
    assign mstatus_val = {19'b0, 2'b11, 3'b0, mstatus_mpie, 3'b0, mstatus_mie, 3'b0};

    // ---------------------------------------------------------------
    // Output assignments
    // ---------------------------------------------------------------
    assign mtvec_o       = {mtvec_reg, 2'b00};
    assign mepc_o        = mepc_reg;  // low 2 bits already masked
    assign mstatus_mie_o = mstatus_mie;
    assign mie_o         = mie_reg;

    // ---------------------------------------------------------------
    // CSR address validation
    // ---------------------------------------------------------------
    reg addr_valid_r;
    always @(*) begin
        case (csr_addr)
            ADDR_MSTATUS,
            ADDR_MISA,
            ADDR_MIE,
            ADDR_MTVEC,
            ADDR_MSCRATCH,
            ADDR_MEPC,
            ADDR_MCAUSE,
            ADDR_MTVAL,
            ADDR_MIP,
            ADDR_CYCLE,
            ADDR_TIME,
            ADDR_INSTRET,
            ADDR_CYCLEH,
            ADDR_TIMEH,
            ADDR_INSTRETH,
            ADDR_MVENDORID,
            ADDR_MARCHID,
            ADDR_MIMPID,
            ADDR_MHARTID:   addr_valid_r = 1'b1;
            default:         addr_valid_r = 1'b0;
        endcase
    end
    assign csr_valid = addr_valid_r;

    // Read-only: addr[11:10] == 2'b11  (0xC00-0xCFF, 0xF00-0xFFF)
    // Also misa (0x301) is read-only per our implementation,
    // and mip (0x344) writes are ignored.
    assign csr_readonly = (csr_addr[11:10] == 2'b11);

    // ---------------------------------------------------------------
    // Combinational CSR read
    // ---------------------------------------------------------------
    always @(*) begin
        case (csr_addr)
            ADDR_MSTATUS:   csr_rdata = mstatus_val;
            ADDR_MISA:      csr_rdata = 32'h4000_0100; // RV32I
            ADDR_MIE:       csr_rdata = mie_reg;
            ADDR_MTVEC:     csr_rdata = {mtvec_reg, 2'b00};
            ADDR_MSCRATCH:  csr_rdata = mscratch_reg;
            ADDR_MEPC:      csr_rdata = mepc_reg;
            ADDR_MCAUSE:    csr_rdata = mcause_reg;
            ADDR_MTVAL:     csr_rdata = mtval_reg;
            ADDR_MIP:       csr_rdata = mip_o;
            ADDR_CYCLE:     csr_rdata = cycle_counter[31:0];
            ADDR_TIME:      csr_rdata = cycle_counter[31:0];  // alias
            ADDR_INSTRET:   csr_rdata = instret_counter[31:0];
            ADDR_CYCLEH:    csr_rdata = cycle_counter[63:32];
            ADDR_TIMEH:     csr_rdata = cycle_counter[63:32]; // alias
            ADDR_INSTRETH:  csr_rdata = instret_counter[63:32];
            ADDR_MVENDORID: csr_rdata = 32'h0;
            ADDR_MARCHID:   csr_rdata = 32'h0;
            ADDR_MIMPID:    csr_rdata = 32'h0;
            ADDR_MHARTID:   csr_rdata = 32'h0;
            default:        csr_rdata = 32'h0;
        endcase
    end

    // ---------------------------------------------------------------
    // Synchronous logic: reset, trap entry, mret, CSR writes, counters
    // ---------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            mstatus_mie    <= 1'b0;
            mstatus_mpie   <= 1'b0;
            mie_reg        <= 32'h0;
            mtvec_reg      <= 30'h0;
            mscratch_reg   <= 32'h0;
            mepc_reg       <= 32'h0;
            mcause_reg     <= 32'h0;
            mtval_reg      <= 32'h0;
            cycle_counter  <= 64'h0;
            instret_counter <= 64'h0;
        end else begin
            // Cycle counter increments every clock cycle
            cycle_counter <= cycle_counter + 64'h1;

            // Instret counter increments when pulsed
            if (instret_inc) begin
                instret_counter <= instret_counter + 64'h1;
            end

            // Trap entry has highest priority over normal CSR writes
            if (trap_enter) begin
                mepc_reg     <= trap_mepc & 32'hFFFF_FFFC;
                mcause_reg   <= trap_mcause;
                mtval_reg    <= trap_mtval;
                mstatus_mpie <= mstatus_mie;
                mstatus_mie  <= 1'b0;
            end else if (mret_exec) begin
                mstatus_mie  <= mstatus_mpie;
                mstatus_mpie <= 1'b1;
            end else if (csr_wen) begin
                case (csr_addr)
                    ADDR_MSTATUS: begin
                        // Only bits 3 (MIE) and 7 (MPIE) are writable
                        mstatus_mie  <= csr_wdata[3];
                        mstatus_mpie <= csr_wdata[7];
                    end
                    ADDR_MIE: begin
                        // Only bits 7 (MTIE) and 11 (MEIE) are writable
                        mie_reg <= csr_wdata & 32'h0000_0880;
                    end
                    ADDR_MTVEC: begin
                        // Bits 1:0 forced to 0 (MODE=0 direct only)
                        mtvec_reg <= csr_wdata[31:2];
                    end
                    ADDR_MSCRATCH: begin
                        mscratch_reg <= csr_wdata;
                    end
                    ADDR_MEPC: begin
                        // Bits 1:0 forced to 0 (4-byte aligned)
                        mepc_reg <= csr_wdata & 32'hFFFF_FFFC;
                    end
                    ADDR_MCAUSE: begin
                        mcause_reg <= csr_wdata;
                    end
                    ADDR_MTVAL: begin
                        mtval_reg <= csr_wdata;
                    end
                    // mip, misa, counters, vendor/arch/imp/hartid:
                    // writes are ignored (read-only or special)
                    default: begin
                        // no-op
                    end
                endcase
            end
        end
    end

endmodule
