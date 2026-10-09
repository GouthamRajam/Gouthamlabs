// Provenance: agent-generated (Phase 1.5 Pillar A)
//
// s2s_rv32i_regfile.v — 32x32-bit register file for the s2s_rv32i core.
// Two combinational read ports, one synchronous write port.
// x0 is hardwired to zero (not stored).
// See architecture.md section 8.3.

module s2s_rv32i_regfile (
    input  wire        clk,

    // Read port 1 (combinational)
    input  wire [4:0]  rs1_addr,
    output wire [31:0] rs1_data,

    // Read port 2 (combinational)
    input  wire [4:0]  rs2_addr,
    output wire [31:0] rs2_data,

    // Write port (synchronous, rising edge)
    input  wire        wr_en,
    input  wire [4:0]  wr_addr,
    input  wire [31:0] wr_data
);

    // Storage for x1..x31 (31 entries). x0 is not stored.
    reg [31:0] regs [1:31];

    // Combinational read — x0 always returns 0
    assign rs1_data = (rs1_addr == 5'b00000) ? 32'b0 : regs[rs1_addr];
    assign rs2_data = (rs2_addr == 5'b00000) ? 32'b0 : regs[rs2_addr];

    // Synchronous write — suppress writes to x0
    always @(posedge clk) begin
        if (wr_en && (wr_addr != 5'b00000)) begin
            regs[wr_addr] <= wr_data;
        end
    end

endmodule
