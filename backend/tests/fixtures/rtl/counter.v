// 8-bit counter with synchronous active-low reset. Lint-clean under verilator -Wall.
module counter (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    output wire [7:0] count
);
    reg [7:0] count_q;
    always @(posedge clk) begin
        if (!rst_n)  count_q <= 8'd0;
        else if (en) count_q <= count_q + 8'd1;
    end
    assign count = count_q;
endmodule
