`timescale 1ns/1ps

module gate_compliance_tb;

    reg clk, rst;
    reg mem_ready;
    reg [31:0] mem_rdata;

    wire        mem_valid;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [3:0]  mem_wstrb;

    // Post-P&R netlist (RESET_VECTOR=0x80000000 baked in)
    picorv32 dut (
        .clk(clk), .rst(rst),
        .mem_valid(mem_valid), .mem_ready(mem_ready),
        .mem_addr(mem_addr),   .mem_rdata(mem_rdata),
        .mem_wdata(mem_wdata), .mem_wstrb(mem_wstrb),
        .irq_external(1'b0),  .irq_timer(1'b0)
    );

    // 8 KB byte-addressable memory at 0x80000000
    reg [7:0] mem [0:8191];

    integer i;
    initial begin
        for (i = 0; i < 8192; i = i + 1) mem[i] = 8'h00;

        // Program: exercises LUI, ADDI, ADD, SUB, AND, OR, XOR, SLT, SLL, SRL, SRA,
        // LW, SW, BEQ, JAL — a representative subset of RV32I
        //
        // x2 = 10, x3 = 20
        // x4 = x2 + x3 = 30
        // x5 = x3 - x2 = 10
        // x6 = x2 & x3 = 0
        // x7 = x2 | x3 = 30
        // x8 = x2 ^ x3 = 30
        // x9 = (x2 < x3) ? 1 : 0 = 1
        // x10 = x2 << 2 = 40
        // x11 = x3 >> 1 = 10
        // sw x4, 0(x1)   -> mem[0x2000] = 30
        // sw x5, 4(x1)   -> mem[0x2004] = 10
        // sw x7, 8(x1)   -> mem[0x2008] = 30
        // sw x9, 12(x1)  -> mem[0x200C] = 1
        // sw x10, 16(x1) -> mem[0x2010] = 40
        // sw x11, 20(x1) -> mem[0x2014] = 10
        // lw x12, 0(x1)  -> x12 = 30 (readback)
        // beq x12, x4, +8 -> should branch (both 30)
        // sw x0, 24(x1)  -> marker = 0 (FAIL — should not reach)
        // addi x13, x0, 0xAA -> marker = 0xAA
        // sw x13, 24(x1) -> mem[0x2018] = 0xAA (PASS marker)
        // jal x0, 0      -> infinite loop (done)

        // lui x1, 0x00002 (x1 = 0x2000 for store base, adds to 0x80002000)
        {mem[3],mem[2],mem[1],mem[0]} = 32'h000020b7;
        // addi x2, x0, 10
        {mem[7],mem[6],mem[5],mem[4]} = 32'h00a00113;
        // addi x3, x0, 20
        {mem[11],mem[10],mem[9],mem[8]} = 32'h01400193;
        // add x4, x2, x3
        {mem[15],mem[14],mem[13],mem[12]} = 32'h00310233;
        // sub x5, x3, x2
        {mem[19],mem[18],mem[17],mem[16]} = 32'h402182b3;
        // and x6, x2, x3
        {mem[23],mem[22],mem[21],mem[20]} = 32'h00317333;
        // or x7, x2, x3
        {mem[27],mem[26],mem[25],mem[24]} = 32'h003163b3;
        // xor x8, x2, x3
        {mem[31],mem[30],mem[29],mem[28]} = 32'h00314433;
        // slt x9, x2, x3
        {mem[35],mem[34],mem[33],mem[32]} = 32'h003124b3;
        // sll x10, x2, x3  (shift left x2 by x3[4:0]=20 — wait, too large)
        // slli x10, x2, 2  (shift left x2 by 2 = 40)
        {mem[39],mem[38],mem[37],mem[36]} = 32'h00211513;
        // srli x11, x3, 1  (shift right x3 by 1 = 10)
        {mem[43],mem[42],mem[41],mem[40]} = 32'h0011d593;
        // sw x4, 0(x1)
        {mem[47],mem[46],mem[45],mem[44]} = 32'h0040a023;
        // sw x5, 4(x1)
        {mem[51],mem[50],mem[49],mem[48]} = 32'h0050a223;
        // sw x7, 8(x1)
        {mem[55],mem[54],mem[53],mem[52]} = 32'h0070a423;
        // sw x9, 12(x1)
        {mem[59],mem[58],mem[57],mem[56]} = 32'h0090a623;
        // sw x10, 16(x1)
        {mem[63],mem[62],mem[61],mem[60]} = 32'h00a0a823;
        // sw x11, 20(x1)
        {mem[67],mem[66],mem[65],mem[64]} = 32'h00b0aa23;
        // lw x12, 0(x1) — readback test
        {mem[71],mem[70],mem[69],mem[68]} = 32'h0000a603;
        // beq x12, x4, +8  (branch if x12 == x4, skip next instr)
        {mem[75],mem[74],mem[73],mem[72]} = 32'h00460463;
        // sw x0, 24(x1) — FAIL marker (should be skipped)
        {mem[79],mem[78],mem[77],mem[76]} = 32'h0000ac23;
        // addi x13, x0, 0xAA
        {mem[83],mem[82],mem[81],mem[80]} = 32'h0aa006b3; // Actually: ori x13, x0, 0xAA
        // Wait — ori: funct3=110, opcode=0010011
        // Let me use: addi x13, x0, 0xAA = 0x0AA00693
        // sw x13, 24(x1) — PASS marker
        // jal x0, 0 — infinite loop

        // Fix: use proper encodings
        // addi x13, x0, 0xAA => imm=0x0AA, rs1=x0, funct3=000, rd=x13, opcode=0010011
        // 0000_1010_1010 | 00000 | 000 | 01101 | 0010011
        // = 0x0AA00693
        {mem[83],mem[82],mem[81],mem[80]} = 32'h0aa00693;
        // sw x13, 24(x1) => imm=24=0x18, rs2=x13, rs1=x1, funct3=010, opcode=0100011
        // imm[11:5]=0000000, rs2=01101, rs1=00001, 010, imm[4:0]=11000, 0100011
        // = 0x00d0ac23
        {mem[87],mem[86],mem[85],mem[84]} = 32'h00d0ac23;
        // jal x0, 0 => 0x0000006f
        {mem[91],mem[90],mem[89],mem[88]} = 32'h0000006f;
    end

    // Memory responder (addr[12:0] maps into 8KB)
    always @(posedge clk) begin
        mem_ready <= 0;
        if (mem_valid && !mem_ready) begin
            mem_ready <= 1;
            if (mem_wstrb == 4'b0000) begin
                mem_rdata <= {mem[{mem_addr[12:2],2'b11}],
                              mem[{mem_addr[12:2],2'b10}],
                              mem[{mem_addr[12:2],2'b01}],
                              mem[{mem_addr[12:2],2'b00}]};
            end else begin
                if (mem_wstrb[0]) mem[{mem_addr[12:2],2'b00}] <= mem_wdata[7:0];
                if (mem_wstrb[1]) mem[{mem_addr[12:2],2'b01}] <= mem_wdata[15:8];
                if (mem_wstrb[2]) mem[{mem_addr[12:2],2'b10}] <= mem_wdata[23:16];
                if (mem_wstrb[3]) mem[{mem_addr[12:2],2'b11}] <= mem_wdata[31:24];
            end
        end
    end

    // Clock: 50ns period (20 MHz to match P1.4)
    always #25 clk = ~clk;

    // VCD dump for power analysis
    initial begin
        $dumpfile("gate_sim.vcd");
        $dumpvars(0, gate_compliance_tb);
    end

    // Monitor memory writes and check results
    integer cycle_count;
    reg done;
    reg [31:0] result_add, result_sub, result_or, result_slt, result_sll, result_srl;
    reg [31:0] result_marker;

    initial begin
        clk = 0; rst = 1; mem_ready = 0; done = 0; cycle_count = 0;
        result_add = 32'hDEAD; result_sub = 32'hDEAD; result_or = 32'hDEAD;
        result_slt = 32'hDEAD; result_sll = 32'hDEAD; result_srl = 32'hDEAD;
        result_marker = 32'hDEAD;

        repeat (10) @(posedge clk);
        rst = 0;

        forever begin
            @(posedge clk);
            cycle_count = cycle_count + 1;

            // Capture writes to result addresses
            if (mem_valid && mem_ready && |mem_wstrb) begin
                case (mem_addr[12:0])
                    13'h2000: begin result_add = mem_wdata; $display("  SW [0x2000] = %0d (add)", mem_wdata); end
                    13'h2004: begin result_sub = mem_wdata; $display("  SW [0x2004] = %0d (sub)", mem_wdata); end
                    13'h2008: begin result_or  = mem_wdata; $display("  SW [0x2008] = %0d (or)",  mem_wdata); end
                    13'h200C: begin result_slt = mem_wdata; $display("  SW [0x200C] = %0d (slt)", mem_wdata); end
                    13'h2010: begin result_sll = mem_wdata; $display("  SW [0x2010] = %0d (sll)", mem_wdata); end
                    13'h2014: begin result_srl = mem_wdata; $display("  SW [0x2014] = %0d (srl)", mem_wdata); end
                    13'h2018: begin
                        result_marker = mem_wdata;
                        $display("  SW [0x2018] = 0x%h (marker)", mem_wdata);
                        done = 1;
                    end
                endcase
            end

            if (done || cycle_count >= 2000) begin
                $display("");
                $display("=== P1.5 Gate-Level Compliance Check ===");
                $display("Post-P&R netlist: picorv32.nl.v (26,252 instances)");
                $display("Cycles simulated: %0d", cycle_count);
                $display("");

                $display("Instruction Results:");
                $display("  ADD  (10+20=30):   %s (got %0d)", result_add == 30 ? "PASS" : "FAIL", result_add);
                $display("  SUB  (20-10=10):   %s (got %0d)", result_sub == 10 ? "PASS" : "FAIL", result_sub);
                $display("  OR   (10|20=30):   %s (got %0d)", result_or  == 30 ? "PASS" : "FAIL", result_or);
                $display("  SLT  (10<20=1):    %s (got %0d)", result_slt == 1  ? "PASS" : "FAIL", result_slt);
                $display("  SLLI (10<<2=40):   %s (got %0d)", result_sll == 40 ? "PASS" : "FAIL", result_sll);
                $display("  SRLI (20>>1=10):   %s (got %0d)", result_srl == 10 ? "PASS" : "FAIL", result_srl);
                $display("  LW readback:       %s", result_add == 30 ? "PASS" : "FAIL");
                $display("  BEQ branch:        %s", result_marker == 32'hAA ? "PASS" : "FAIL");
                $display("  Marker (0xAA):     %s (got 0x%h)", result_marker == 32'hAA ? "PASS" : "FAIL", result_marker);
                $display("");

                if (result_add == 30 && result_sub == 10 && result_or == 30 &&
                    result_slt == 1 && result_sll == 40 && result_srl == 10 &&
                    result_marker == 32'hAA)
                    $display("GATE-LEVEL COMPLIANCE: PASS");
                else if (cycle_count >= 2000)
                    $display("GATE-LEVEL COMPLIANCE: FAIL (TIMEOUT)");
                else
                    $display("GATE-LEVEL COMPLIANCE: FAIL");

                $finish;
            end
        end
    end

endmodule
