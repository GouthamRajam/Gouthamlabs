// Formal harness for rtl/counter.v. LIMIT selects the asserted upper bound:
// with en held low after reset the count stays 0, so "count <= LIMIT" is provable;
// the FAIL fixture instead asserts the count never moves, which en=1 violates.
module counter_formal (
    input wire clk,
    input wire rst_n,
    input wire en
);
    wire [7:0] count;
    counter dut (.clk(clk), .rst_n(rst_n), .en(en), .count(count));

    reg past_valid = 1'b0;
    always @(posedge clk) past_valid <= 1'b1;
    always @(*) if (!past_valid) assume (!rst_n);

`ifdef CHECK_STUCK
    // Wrong property (FAIL fixture): claims the counter never leaves 0.
    always @(*) if (past_valid) assert (count == 8'd0);
`else
    // Right property (PASS fixture): after reset, count only changes by +1 when enabled.
    always @(posedge clk)
        if (past_valid && $past(rst_n) && rst_n)
            assert (count == $past(count) + ($past(en) ? 8'd1 : 8'd0));
`endif
endmodule
