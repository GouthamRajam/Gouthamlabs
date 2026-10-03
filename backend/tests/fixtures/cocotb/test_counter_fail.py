"""cocotb test that should FAIL on rtl/counter.v: it expects 7 where the correct value is 5
(known defect in the test; see test_counter_pass.py)."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def counts_up_wrong_expectation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    dut.en.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    dut.en.value = 1
    await ClockCycles(dut.clk, 5)
    await RisingEdge(dut.clk)
    assert int(dut.count.value) == 7, f"count={int(dut.count.value)}"
