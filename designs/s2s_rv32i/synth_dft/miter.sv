// Miter for s2s_rv32i_core RTL vs synthesized netlist equivalence
// Feeds identical inputs to both, asserts all outputs match

module miter (
    input        clk,
    input        rst_n,
    input [31:0] mem_rdata,
    input        mem_ready,
    input        irq_external,
    input        irq_timer
);

    // Gold (RTL) outputs
    wire [31:0] gold_mem_addr;
    wire [31:0] gold_mem_wdata;
    wire [3:0]  gold_mem_wstrb;
    wire        gold_mem_valid;

    // Gate (synthesized) outputs
    wire [31:0] gate_mem_addr;
    wire [31:0] gate_mem_wdata;
    wire [3:0]  gate_mem_wstrb;
    wire        gate_mem_valid;

    // Gold instance (RTL)
    s2s_rv32i_core #(.RESET_VECTOR(32'h80000000)) gold (
        .clk          (clk),
        .rst_n        (rst_n),
        .mem_addr     (gold_mem_addr),
        .mem_wdata    (gold_mem_wdata),
        .mem_wstrb    (gold_mem_wstrb),
        .mem_rdata    (mem_rdata),
        .mem_valid    (gold_mem_valid),
        .mem_ready    (mem_ready),
        .irq_external (irq_external),
        .irq_timer    (irq_timer)
    );

    // Gate instance (synthesized netlist)
    s2s_rv32i_core_gate gate_inst (
        .clk          (clk),
        .rst_n        (rst_n),
        .mem_addr     (gate_mem_addr),
        .mem_wdata    (gate_mem_wdata),
        .mem_wstrb    (gate_mem_wstrb),
        .mem_rdata    (mem_rdata),
        .mem_valid    (gate_mem_valid),
        .mem_ready    (mem_ready),
        .irq_external (irq_external),
        .irq_timer    (irq_timer)
    );

    // Equivalence: all outputs must match after reset is released
    reg past_valid = 0;
    always @(posedge clk)
        past_valid <= 1;

    always @(posedge clk) begin
        if (past_valid && rst_n) begin
            assert (gold_mem_valid == gate_mem_valid);
            assert (gold_mem_addr  == gate_mem_addr);
            assert (gold_mem_wdata == gate_mem_wdata);
            assert (gold_mem_wstrb == gate_mem_wstrb);
        end
    end

    // Assume reset held for at least one cycle at start
    always @(posedge clk) begin
        if (!past_valid)
            assume (!rst_n);
    end

endmodule
