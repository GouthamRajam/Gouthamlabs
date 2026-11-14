// Provenance: hand-authored by Claude in interactive Code session (not S2S agent pipeline)
// compliance_tb.v — Testbench for running riscv-arch-test on s2s_rv32i_core.
// Uses HTIF-style termination: tohost=1 → PASS, tohost=3 → FAIL.
// Dumps signature region to "dut_signature.txt" for comparison against Sail.

`timescale 1ns/1ps

module compliance_tb;

    parameter MEM_SIZE_BYTES = 262144; // 256 KB
    parameter MEM_BASE       = 32'h8000_0000;
    parameter TIMEOUT_CYCLES = 10_000_000;

    reg         clk;
    reg         rst_n;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [3:0]  mem_wstrb;
    reg  [31:0] mem_rdata;
    wire        mem_valid;
    reg         mem_ready;

    reg [7:0] mem [0:MEM_SIZE_BYTES-1];

    integer cycle_count;
    integer sig_fd;
    integer i;

    reg [31:0] sig_begin;
    reg [31:0] sig_end;
    reg [31:0] tohost_addr;
    reg [31:0] tohost_val;
    reg        test_done;
    reg        test_pass;

    // DUT
    s2s_rv32i_core #(
        .RESET_VECTOR(MEM_BASE)
    ) dut (
        .clk          (clk),
        .rst_n        (rst_n),
        .mem_addr     (mem_addr),
        .mem_wdata    (mem_wdata),
        .mem_wstrb    (mem_wstrb),
        .mem_rdata    (mem_rdata),
        .mem_valid    (mem_valid),
        .mem_ready    (mem_ready),
        .irq_external (1'b0),
        .irq_timer    (1'b0)
    );

    // Clock: 50 MHz (20 ns period)
    initial clk = 0;
    always #10 clk = ~clk;

    // Memory load
    initial begin
        for (i = 0; i < MEM_SIZE_BYTES; i = i + 1)
            mem[i] = 8'h00;
        $readmemh("test.hex", mem);
    end

    // Read addresses from plusargs
    initial begin
        if (!$value$plusargs("sig_begin=%h", sig_begin))
            sig_begin = 32'h0;
        if (!$value$plusargs("sig_end=%h", sig_end))
            sig_end = 32'h0;
        if (!$value$plusargs("tohost=%h", tohost_addr))
            tohost_addr = 32'h8000_8000;
    end

    // Memory index within the 256 KB range
    wire [17:0] mem_idx = mem_addr[17:0];
    wire        mem_in_range = (mem_addr >= MEM_BASE) &&
                               (mem_addr < (MEM_BASE + MEM_SIZE_BYTES));

    // Synchronous memory model: responds one cycle after request
    always @(posedge clk) begin
        mem_ready <= 1'b0;
        mem_rdata <= 32'h0;
        if (mem_valid) begin
            mem_ready <= 1'b1;
            if (mem_in_range) begin
                if (mem_wstrb == 4'b0000) begin
                    // Read
                    mem_rdata <= {mem[{mem_idx[17:2], 2'd3}],
                                  mem[{mem_idx[17:2], 2'd2}],
                                  mem[{mem_idx[17:2], 2'd1}],
                                  mem[{mem_idx[17:2], 2'd0}]};
                end else begin
                    // Write
                    if (mem_wstrb[0]) mem[{mem_idx[17:2], 2'd0}] <= mem_wdata[7:0];
                    if (mem_wstrb[1]) mem[{mem_idx[17:2], 2'd1}] <= mem_wdata[15:8];
                    if (mem_wstrb[2]) mem[{mem_idx[17:2], 2'd2}] <= mem_wdata[23:16];
                    if (mem_wstrb[3]) mem[{mem_idx[17:2], 2'd3}] <= mem_wdata[31:24];
                end
            end
            // Out-of-range: mem_ready asserts, reads return 0, writes ignored
        end
    end

    // HTIF tohost monitoring — check memory writes for tohost
    always @(posedge clk) begin
        if (mem_valid && mem_in_range && (mem_wstrb != 4'b0000) &&
            (mem_addr == tohost_addr)) begin
            tohost_val <= mem_wdata;
            if (mem_wdata == 32'd1) begin
                test_done <= 1'b1;
                test_pass <= 1'b1;
            end else if (mem_wdata == 32'd3) begin
                test_done <= 1'b1;
                test_pass <= 1'b0;
            end
        end
    end

    // Debug: trace PC on each fetch
    `ifdef TRACE_PC
    always @(posedge clk) begin
        if (rst_n && dut.state == 3'd0 && dut.mem_valid && mem_ready)
            $display("TRACE PC=%08h INSN=%08h", dut.pc, mem_rdata);
    end
    `endif

    // Main test logic
    initial begin
        test_done  = 1'b0;
        test_pass  = 1'b0;
        tohost_val = 32'h0;
        cycle_count = 0;

        // Reset
        rst_n = 1'b0;
        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        // Run until test completes or timeout
        while (!test_done && (cycle_count < TIMEOUT_CYCLES)) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
        end

        if (!test_done) begin
            $display("TIMEOUT after %0d cycles", cycle_count);
            $display("RESULT: TIMEOUT");
        end else if (test_pass) begin
            $display("Test PASSED (tohost=1) after %0d cycles", cycle_count);
            $display("RESULT: PASS");
        end else begin
            $display("Test FAILED (tohost=%0d) after %0d cycles", tohost_val, cycle_count);
            $display("RESULT: FAIL");
        end

        // Dump signature region
        if (sig_begin != 0 && sig_end != 0 && sig_end > sig_begin) begin
            sig_fd = $fopen("dut_signature.txt", "w");
            if (sig_fd) begin
                for (i = sig_begin; i < sig_end; i = i + 4) begin
                    $fwrite(sig_fd, "%02x%02x%02x%02x\n",
                        mem[i - MEM_BASE + 3],
                        mem[i - MEM_BASE + 2],
                        mem[i - MEM_BASE + 1],
                        mem[i - MEM_BASE + 0]);
                end
                $fclose(sig_fd);
                $display("Signature dumped: %0d words (%0d bytes)",
                    (sig_end - sig_begin) / 4, sig_end - sig_begin);
            end
        end else begin
            $display("WARNING: signature region not set (sig_begin=0x%08h sig_end=0x%08h)",
                sig_begin, sig_end);
        end

        $finish;
    end

endmodule
