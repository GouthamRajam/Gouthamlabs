// Miter for PicoRV32 RTL vs synthesized netlist equivalence
// Feeds identical inputs to both, asserts all outputs match

module miter (
    input        clk,
    input        rst,
    input [31:0] mem_rdata,
    input        mem_ready,
    input        irq_external,
    input        irq_timer
);

    // Gold (RTL) outputs
    wire        gold_mem_valid;
    wire [31:0] gold_mem_addr;
    wire [31:0] gold_mem_wdata;
    wire [3:0]  gold_mem_wstrb;

    // Gate (synthesized) outputs
    wire        gate_mem_valid;
    wire [31:0] gate_mem_addr;
    wire [31:0] gate_mem_wdata;
    wire [3:0]  gate_mem_wstrb;

    // Gold instance (RTL)
    picorv32 gold (
        .clk          (clk),
        .rst          (rst),
        .mem_valid    (gold_mem_valid),
        .mem_ready    (mem_ready),
        .mem_addr     (gold_mem_addr),
        .mem_wdata    (gold_mem_wdata),
        .mem_wstrb    (gold_mem_wstrb),
        .mem_rdata    (mem_rdata),
        .irq_external (irq_external),
        .irq_timer    (irq_timer)
    );

    // Gate instance (synthesized netlist)
    picorv32_gate gate_inst (
        .clk          (clk),
        .rst          (rst),
        .mem_valid    (gate_mem_valid),
        .mem_ready    (mem_ready),
        .mem_addr     (gate_mem_addr),
        .mem_wdata    (gate_mem_wdata),
        .mem_wstrb    (gate_mem_wstrb),
        .mem_rdata    (mem_rdata),
        .irq_external (irq_external),
        .irq_timer    (irq_timer)
    );

    // Equivalence: all outputs must match after reset is released
    reg past_valid = 0;
    always @(posedge clk)
        past_valid <= 1;

    always @(posedge clk) begin
        if (past_valid && !rst) begin
            assert (gold_mem_valid == gate_mem_valid);
            assert (gold_mem_addr  == gate_mem_addr);
            assert (gold_mem_wdata == gate_mem_wdata);
            assert (gold_mem_wstrb == gate_mem_wstrb);
        end
    end

    // Assume reset held for at least one cycle at start
    always @(posedge clk) begin
        if (!past_valid)
            assume (rst);
    end

endmodule
