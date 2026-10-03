// Known defect: the carry into bit 2 is dropped, so this is NOT equivalent to the gold.
module adder (input wire [3:0] a, input wire [3:0] b, output wire [4:0] s);
    wire [4:0] c;
    assign c[0] = 1'b0;
    genvar i;
    generate for (i = 0; i < 4; i = i + 1) begin : rc
        assign s[i]   = a[i] ^ b[i] ^ ((i == 2) ? 1'b0 : c[i]);
        assign c[i+1] = (a[i] & b[i]) | (c[i] & (a[i] ^ b[i]));
    end endgenerate
    assign s[4] = c[4];
endmodule
