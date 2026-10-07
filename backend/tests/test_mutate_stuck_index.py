"""A 'stuck' mutant of an indexed register keeps the element, never the whole array: sync_fifo change #2's
mutant `mem_q[wr_addr] <= mem_q;` passed Verilator's lint screen (-Wno-fatal) and then failed its C++ build,
stopping the mutation run (2026-10-07)."""
from s2s.verify.mutate import candidates

RTL = """module m (input clk, input rst_n, input we, input [3:0] a, input [7:0] d, output reg [7:0] q);
reg [7:0] mem_q [0:15];
always @(posedge clk) begin
    if (we)
        mem_q[a] <= d;
end
always @(posedge clk) begin
    if (!rst_n)
        q <= 8'd0;
    else
        q <= mem_q[a];
end
always @(*) begin
    tmp[a] = d;
end
endmodule
"""


def test_stuck_mutant_of_indexed_target_holds_its_element():
    stuck = [c for c in candidates({"rtl/m.v": RTL}) if c.type == "stuck_bit"]
    lines = [c.after.split("//")[0].strip() for c in stuck]
    assert "mem_q[a] <= mem_q[a];" in lines
    assert "tmp[a] = tmp[a];" in lines
    assert "q <= q;" in lines  # unindexed targets unchanged
    assert not any(l.endswith("<= mem_q;") or l.endswith("= tmp;") for l in lines)
