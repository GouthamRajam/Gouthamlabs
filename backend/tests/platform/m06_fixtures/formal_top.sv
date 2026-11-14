// Hand-written test fixture (scripted model answer). Not agent output.
module formal_top (input clk, input rst_n, input en, input up, input load, input [7:0] load_value);
  wire [7:0] count;
  counter8 dut (.clk(clk), .rst_n(rst_n), .en(en), .up(up), .load(load), .load_value(load_value), .count(count));
  reg past_valid = 1'b0;
  always @(posedge clk) past_valid <= 1'b1;
  always @(*) if (!past_valid) am_reset: assume (!rst_n);   // REQ-001: start in reset
  always @(posedge clk) if (past_valid) begin
    ap_reset: assert ($past(rst_n) || count == 8'd0);
    cp_reset: cover (!$past(rst_n));
    ap_load: assert (!(($past(rst_n) && $past(load))) || (count == $past(load_value)));
    cp_load: cover ($past(rst_n) && $past(load));
    ap_hold: assert (!(($past(rst_n) && !$past(load) && !$past(en))) || (count == $past(count)));
    cp_hold: cover ($past(rst_n) && !$past(load) && !$past(en));
    ap_up: assert (!(($past(rst_n) && !$past(load) && $past(en) && $past(up))) || (count == $past(count) + 8'd1));
    cp_up: cover ($past(rst_n) && !$past(load) && $past(en) && $past(up));
  end
endmodule
