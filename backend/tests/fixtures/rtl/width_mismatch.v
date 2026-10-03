// Known defect for M0.2 acceptance test 2: an 8-bit result assigned from a 9-bit sum.
module width_mismatch (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] sum
);
    wire [8:0] full;
    assign full = a + b;
    assign sum = full;
endmodule
