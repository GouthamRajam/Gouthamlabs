"""Old-vs-new RTL sequential equivalence for design changes (CEO decision 2026-10-07): the miter compares every
top-level output from the cycle after reset; a behaviour change is caught, a re-timed equivalent design passes."""
import pytest

from s2s.verify import rtl_equiv
from tests.platform.test_m05_offline import eda_available

PORTS = [{"name": "clk", "dir": "in", "width": 1}, {"name": "rst_n", "dir": "in", "width": 1},
         {"name": "inc", "dir": "in", "width": 1}, {"name": "q", "dir": "out", "width": 4}]
RESET = {"name": "rst_n", "active": "low"}

# old: q is a combinational function of the registered count (like sync_fifo's rd_data before the fix)
OLD = """module cnt_core(input clk, input rst_n, input inc, output [3:0] cnt);
  reg [3:0] c; always @(posedge clk) if (!rst_n) c <= 0; else if (inc) c <= c + 1; assign cnt = c;
endmodule
module top(input clk, input rst_n, input inc, output [3:0] q);
  wire [3:0] cnt; cnt_core u(.clk(clk), .rst_n(rst_n), .inc(inc), .cnt(cnt)); assign q = cnt ^ 4'b0101;
endmodule
"""
# new: the output is computed one cycle early and registered (the prefetch idea); same behaviour at the ports
NEW = """module cnt_core(input clk, input rst_n, input inc, output [3:0] cnt, output [3:0] cnt_next);
  reg [3:0] c; assign cnt_next = (!rst_n) ? 4'd0 : (inc ? c + 4'd1 : c);
  always @(posedge clk) c <= cnt_next; assign cnt = c;
endmodule
module top(input clk, input rst_n, input inc, output [3:0] q);
  wire [3:0] cnt, nx; reg [3:0] q_q;
  cnt_core u(.clk(clk), .rst_n(rst_n), .inc(inc), .cnt(cnt), .cnt_next(nx));
  always @(posedge clk) q_q <= nx ^ 4'b0101; assign q = q_q;
endmodule
"""


def test_rename_prefixes_definitions_and_instances():
    out = rtl_equiv.rename_modules(OLD, ["top", "cnt_core"])
    assert "module s2s_old_cnt_core(" in out and "module s2s_old_top(" in out and "s2s_old_cnt_core u(" in out
    assert "module top(" not in out


def test_miter_assumes_reset_first_and_compares_every_output():
    m = rtl_equiv.miter("top", PORTS, RESET)
    assert "s2s_old_top u_old" in m and "top u_new" in m
    assert "if (s2s_init) assume(rst_n == 1'b0);" in m
    assert "eq_q: assert (o_q == n_q);" in m and "input [3:0]" not in m.split("\n")[0]


@pytest.mark.slow
@pytest.mark.skipif(not eda_available(), reason="s2s-eda image not built")
@pytest.mark.parametrize("new,expect", [(NEW, "PASS"), (NEW.replace("4'b0101; assign q", "4'b0100; assign q"), "FAIL")])
def test_retimed_design_passes_and_a_changed_one_fails(tmp_path, new, expect):
    (tmp_path / "logs").mkdir()
    f = tmp_path / "new.v"
    f.write_text(new)
    r = rtl_equiv.check(tmp_path, {"old.v": OLD}, [f], "top", ["top", "cnt_core"], PORTS, RESET, 12, 600)
    assert r["status"] == expect, r["tail"]
    if expect == "FAIL":
        assert r["failed_assertions"] == ["eq_q"] or not r["passed"]


def test_guard_flag_maps_to_its_file():
    """sync_fifo 2026-10-07: a test-plan flag ('testplan: coverage bin ... was removed') was looked up as a file
    named 'testplan', so the final anti-cheat review asked Sentinel for a path outside its reads_from."""
    from s2s.agents.m06 import flag_file
    paths = {"tb/testplan.yaml", "tb/test_sync_fifo.py", "formal/formal_top.sv"}
    assert flag_file("testplan: coverage bin 'cov_x' was removed", paths) == "tb/testplan.yaml"
    assert flag_file("tb/test_sync_fifo.py: test 't' was deleted", paths) == "tb/test_sync_fifo.py"
