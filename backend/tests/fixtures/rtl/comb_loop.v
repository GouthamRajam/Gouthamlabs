// Known defect: combinational loop (x depends on y depends on x).
module comb_loop (
    input  wire a,
    output wire y
);
    wire x;
    assign x = a & y;
    assign y = ~x;
endmodule
