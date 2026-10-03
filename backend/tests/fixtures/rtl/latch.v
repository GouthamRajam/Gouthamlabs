// Known defect: incomplete combinational assignment infers a latch on q.
module latch (
    input  wire en,
    input  wire d,
    output reg  q
);
    always @(*) begin
        if (en) q = d;
    end
endmodule
