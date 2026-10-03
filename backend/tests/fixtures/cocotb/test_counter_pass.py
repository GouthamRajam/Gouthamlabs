"""cocotb test that should PASS on rtl/counter.v: count increments while enabled."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def counts_up(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    dut.en.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    dut.en.value = 1
    await ClockCycles(dut.clk, 5)
    await RisingEdge(dut.clk)
    # Read at the 6th enabled edge, before that edge's update lands: 5 increments are visible.
    assert int(dut.count.value) == 5, f"count={int(dut.count.value)}"
