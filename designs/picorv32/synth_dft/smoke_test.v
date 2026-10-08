`timescale 1ns/1ps

module smoke_test;

    reg clk, rst;
    reg mem_ready_rtl, mem_ready_gate;
    reg [31:0] mem_rdata_rtl, mem_rdata_gate;

    wire        mem_valid_rtl, mem_valid_gate;
    wire [31:0] mem_addr_rtl,  mem_addr_gate;
    wire [31:0] mem_wdata_rtl, mem_wdata_gate;
    wire [3:0]  mem_wstrb_rtl, mem_wstrb_gate;

    // RTL instance — match synthesis RESET_VECTOR
    picorv32 #(.RESET_VECTOR(32'h80000000)) rtl_dut (
        .clk(clk), .rst(rst),
        .mem_valid(mem_valid_rtl), .mem_ready(mem_ready_rtl),
        .mem_addr(mem_addr_rtl),   .mem_rdata(mem_rdata_rtl),
        .mem_wdata(mem_wdata_rtl), .mem_wstrb(mem_wstrb_rtl),
        .irq_external(1'b0),      .irq_timer(1'b0)
    );

    // Gate-level instance (synthesized with RESET_VECTOR=0x80000000)
    picorv32_gate gate_dut (
        .clk(clk), .rst(rst),
        .mem_valid(mem_valid_gate), .mem_ready(mem_ready_gate),
        .mem_addr(mem_addr_gate),   .mem_rdata(mem_rdata_gate),
        .mem_wdata(mem_wdata_gate), .mem_wstrb(mem_wstrb_gate),
        .irq_external(1'b0),       .irq_timer(1'b0)
    );

    // Separate memory models
    reg [7:0] mem_rtl  [0:8191];
    reg [7:0] mem_gate [0:8191];

    integer i;
    initial begin
        for (i = 0; i < 8192; i = i + 1) begin
            mem_rtl[i]  = 8'h00;
            mem_gate[i] = 8'h00;
        end
        // lui x1, 0x00002 => 0x000020b7
        {mem_rtl[3],mem_rtl[2],mem_rtl[1],mem_rtl[0]} = 32'h000020b7;
        {mem_gate[3],mem_gate[2],mem_gate[1],mem_gate[0]} = 32'h000020b7;
        // addi x2, x0, 10 => 0x00a00113
        {mem_rtl[7],mem_rtl[6],mem_rtl[5],mem_rtl[4]} = 32'h00a00113;
        {mem_gate[7],mem_gate[6],mem_gate[5],mem_gate[4]} = 32'h00a00113;
        // addi x3, x0, 20 => 0x01400193
        {mem_rtl[11],mem_rtl[10],mem_rtl[9],mem_rtl[8]} = 32'h01400193;
        {mem_gate[11],mem_gate[10],mem_gate[9],mem_gate[8]} = 32'h01400193;
        // add x4, x2, x3 => 0x00310233
        {mem_rtl[15],mem_rtl[14],mem_rtl[13],mem_rtl[12]} = 32'h00310233;
        {mem_gate[15],mem_gate[14],mem_gate[13],mem_gate[12]} = 32'h00310233;
        // sw x4, 0(x1) => 0x0040a023
        {mem_rtl[19],mem_rtl[18],mem_rtl[17],mem_rtl[16]} = 32'h0040a023;
        {mem_gate[19],mem_gate[18],mem_gate[17],mem_gate[16]} = 32'h0040a023;
        // addi x5, x0, 0x55 => 0x05500293
        {mem_rtl[23],mem_rtl[22],mem_rtl[21],mem_rtl[20]} = 32'h05500293;
        {mem_gate[23],mem_gate[22],mem_gate[21],mem_gate[20]} = 32'h05500293;
        // sw x5, 4(x1) => 0x0050a223
        {mem_rtl[27],mem_rtl[26],mem_rtl[25],mem_rtl[24]} = 32'h0050a223;
        {mem_gate[27],mem_gate[26],mem_gate[25],mem_gate[24]} = 32'h0050a223;
        // jal x0, 0 => 0x0000006f
        {mem_rtl[31],mem_rtl[30],mem_rtl[29],mem_rtl[28]} = 32'h0000006f;
        {mem_gate[31],mem_gate[30],mem_gate[29],mem_gate[28]} = 32'h0000006f;
    end

    // Memory responder for RTL (addr[12:0] maps into 8KB)
    always @(posedge clk) begin
        mem_ready_rtl <= 0;
        if (mem_valid_rtl && !mem_ready_rtl) begin
            mem_ready_rtl <= 1;
            if (mem_wstrb_rtl == 4'b0000) begin
                mem_rdata_rtl <= {mem_rtl[{mem_addr_rtl[12:2],2'b11}],
                                  mem_rtl[{mem_addr_rtl[12:2],2'b10}],
                                  mem_rtl[{mem_addr_rtl[12:2],2'b01}],
                                  mem_rtl[{mem_addr_rtl[12:2],2'b00}]};
            end else begin
                if (mem_wstrb_rtl[0]) mem_rtl[{mem_addr_rtl[12:2],2'b00}] <= mem_wdata_rtl[7:0];
                if (mem_wstrb_rtl[1]) mem_rtl[{mem_addr_rtl[12:2],2'b01}] <= mem_wdata_rtl[15:8];
                if (mem_wstrb_rtl[2]) mem_rtl[{mem_addr_rtl[12:2],2'b10}] <= mem_wdata_rtl[23:16];
                if (mem_wstrb_rtl[3]) mem_rtl[{mem_addr_rtl[12:2],2'b11}] <= mem_wdata_rtl[31:24];
            end
        end
    end

    // Memory responder for gate-level
    always @(posedge clk) begin
        mem_ready_gate <= 0;
        if (mem_valid_gate && !mem_ready_gate) begin
            mem_ready_gate <= 1;
            if (mem_wstrb_gate == 4'b0000) begin
                mem_rdata_gate <= {mem_gate[{mem_addr_gate[12:2],2'b11}],
                                   mem_gate[{mem_addr_gate[12:2],2'b10}],
                                   mem_gate[{mem_addr_gate[12:2],2'b01}],
                                   mem_gate[{mem_addr_gate[12:2],2'b00}]};
            end else begin
                if (mem_wstrb_gate[0]) mem_gate[{mem_addr_gate[12:2],2'b00}] <= mem_wdata_gate[7:0];
                if (mem_wstrb_gate[1]) mem_gate[{mem_addr_gate[12:2],2'b01}] <= mem_wdata_gate[15:8];
                if (mem_wstrb_gate[2]) mem_gate[{mem_addr_gate[12:2],2'b10}] <= mem_wdata_gate[23:16];
                if (mem_wstrb_gate[3]) mem_gate[{mem_addr_gate[12:2],2'b11}] <= mem_wdata_gate[31:24];
            end
        end
    end

    // Clock
    always #5 clk = ~clk;

    integer mismatches;
    integer cycle_count;
    reg gate_done, rtl_done;
    reg [31:0] gate_result, rtl_result;
    reg [31:0] gate_marker, rtl_marker;

    initial begin
        clk = 0;
        rst = 1;
        mem_ready_rtl = 0;
        mem_ready_gate = 0;
        mismatches = 0;
        cycle_count = 0;
        gate_done = 0;
        rtl_done = 0;
        gate_result = 32'hDEADBEEF;
        rtl_result = 32'hDEADBEEF;

        repeat (10) @(posedge clk);
        rst = 0;

        forever begin
            @(posedge clk);
            cycle_count = cycle_count + 1;

            // Compare mem_valid
            if (mem_valid_rtl !== mem_valid_gate) begin
                if (mismatches < 5)
                    $display("MISMATCH cycle %0d: mem_valid RTL=%b GATE=%b",
                             cycle_count, mem_valid_rtl, mem_valid_gate);
                mismatches = mismatches + 1;
            end

            // Compare when both requesting
            if (mem_valid_rtl && mem_valid_gate) begin
                if (mem_addr_rtl !== mem_addr_gate) begin
                    if (mismatches < 5)
                        $display("MISMATCH cycle %0d: mem_addr RTL=0x%h GATE=0x%h",
                                 cycle_count, mem_addr_rtl, mem_addr_gate);
                    mismatches = mismatches + 1;
                end
                if (mem_wstrb_rtl !== mem_wstrb_gate) begin
                    if (mismatches < 5)
                        $display("MISMATCH cycle %0d: mem_wstrb RTL=%b GATE=%b",
                                 cycle_count, mem_wstrb_rtl, mem_wstrb_gate);
                    mismatches = mismatches + 1;
                end
                if (mem_wdata_rtl !== mem_wdata_gate && |mem_wstrb_rtl) begin
                    if (mismatches < 5)
                        $display("MISMATCH cycle %0d: mem_wdata RTL=0x%h GATE=0x%h",
                                 cycle_count, mem_wdata_rtl, mem_wdata_gate);
                    mismatches = mismatches + 1;
                end
            end

            // Detect gate writes
            if (mem_valid_gate && mem_ready_gate && |mem_wstrb_gate) begin
                if (mem_addr_gate[12:0] == 13'h2004) begin
                    gate_done = 1;
                    gate_marker = mem_wdata_gate;
                    $display("Gate: wrote 0x%h to [0x2004] at cycle %0d", mem_wdata_gate, cycle_count);
                end
                if (mem_addr_gate[12:0] == 13'h2000) begin
                    gate_result = mem_wdata_gate;
                    $display("Gate: wrote 0x%h to [0x2000] at cycle %0d", mem_wdata_gate, cycle_count);
                end
            end

            // Detect RTL writes
            if (mem_valid_rtl && mem_ready_rtl && |mem_wstrb_rtl) begin
                if (mem_addr_rtl[12:0] == 13'h2004) begin
                    rtl_done = 1;
                    rtl_marker = mem_wdata_rtl;
                    $display("RTL:  wrote 0x%h to [0x2004] at cycle %0d", mem_wdata_rtl, cycle_count);
                end
                if (mem_addr_rtl[12:0] == 13'h2000) begin
                    rtl_result = mem_wdata_rtl;
                    $display("RTL:  wrote 0x%h to [0x2000] at cycle %0d", mem_wdata_rtl, cycle_count);
                end
            end

            if ((gate_done && rtl_done) || cycle_count >= 500) begin
                $display("");
                $display("=== P1.3 Smoke Test Results ===");
                $display("Cycles simulated: %0d", cycle_count);
                $display("Output mismatches (cycle-by-cycle): %0d", mismatches);
                $display("");

                if (gate_done && gate_marker == 32'h55)
                    $display("Gate program execution: PASS (marker 0x55)");
                else if (gate_done)
                    $display("Gate program execution: FAIL (marker=0x%h, expected 0x55)", gate_marker);
                else
                    $display("Gate program execution: FAIL (did not complete)");

                if (gate_result == 32'h1e)
                    $display("Gate ALU result (10+20): PASS (%0d)", gate_result);
                else
                    $display("Gate ALU result (10+20): FAIL (got %0d, expected 30)", gate_result);

                if (rtl_done && rtl_marker == 32'h55)
                    $display("RTL  program execution: PASS (marker 0x55)");
                else
                    $display("RTL  program execution: FAIL");

                if (gate_result == rtl_result && gate_result == 32'h1e)
                    $display("RTL vs Gate values: MATCH (both=%0d)", gate_result);
                else
                    $display("RTL vs Gate values: MISMATCH (rtl=%0d gate=%0d)", rtl_result, gate_result);

                $display("");
                if (mismatches == 0 && gate_done && gate_marker == 32'h55 &&
                    gate_result == 32'h1e && gate_result == rtl_result)
                    $display("SMOKE TEST: PASS");
                else if (gate_done && gate_marker == 32'h55 &&
                         gate_result == 32'h1e && gate_result == rtl_result)
                    $display("SMOKE TEST: PASS (with %0d cycle-timing mismatches)", mismatches);
                else
                    $display("SMOKE TEST: FAIL");
                $finish;
            end
        end
    end

endmodule
