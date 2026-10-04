// counter8: 8-bit up/down counter, synchronous active-low reset, enable, synchronous load.
// Implements REQ-001..REQ-004. Hand-written test fixture (scripted answer), not agent output.
module counter8 #(
    parameter integer WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    input  wire             up,
    input  wire             load,
    input  wire [WIDTH-1:0] load_value,
    output wire [WIDTH-1:0] count
);
    reg [WIDTH-1:0] count_q;
    reg [WIDTH:0]   count_d;

    always @(*) begin
        count_d = count_q;                          // REQ-004 hold
        if (load) begin
            count_d = load_value;                   // REQ-002
        end else if (en) begin
            if (up) count_d = count_q + 1'b1;       // REQ-003 (wraps modulo 2^WIDTH)
            else    count_d = count_q - 1'b1;       // REQ-003
        end
    end

    always @(posedge clk) begin
        if (!rst_n) count_q <= {WIDTH{1'b0}};       // REQ-001
        else        count_q <= count_d;
    end

    assign count = count_q;
endmodule
