# Hand-written test fixture (scripted model answer). Not agent output.
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge
from ref_model import RefModel


async def cycle(dut, model, txn, i):
    await FallingEdge(dut.clk)
    for k, v in txn.items():
        getattr(dut, k).value = v
    exp = model.step(txn)["count"]
    await RisingEdge(dut.clk)
    await ReadOnly()
    got = int(dut.count.value)
    assert got == exp, f"cycle {i} {txn}: count={got} expected {exp}"


async def start(dut):
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    m = RefModel()
    m.reset()
    await cycle(dut, m, {"rst_n": 0, "en": 0, "up": 0, "load": 0, "load_value": 0}, -1)
    return m


@cocotb.test(timeout_time=50, timeout_unit="ms")
async def test_reset(dut):
    m = await start(dut)
    for i in range(40):
        await cycle(dut, m, {"rst_n": int(i % 7 != 6), "en": 1, "up": 1, "load": 0, "load_value": 0}, i)


@cocotb.test(timeout_time=50, timeout_unit="ms")
async def test_load(dut):
    m = await start(dut)
    for i, v in enumerate([0, 255, 0x5A, 0xA5] + [random.randint(0, 255) for _ in range(20)]):
        await cycle(dut, m, {"rst_n": 1, "en": random.randint(0, 1), "up": random.randint(0, 1), "load": 1, "load_value": v}, i)


@cocotb.test(timeout_time=200, timeout_unit="ms")
async def test_random(dut):
    m = await start(dut)
    for i in range(3000):
        await cycle(dut, m, {"rst_n": int(random.random() > 0.01), "en": int(random.random() < 0.8),
                             "up": int(random.random() < 0.5) if i > 600 else 1, "load": int(random.random() < 0.03),
                             "load_value": random.randint(0, 255)}, i)
    for i in range(300):
        await cycle(dut, m, {"rst_n": 1, "en": 1, "up": 0, "load": 0, "load_value": 0}, 3000 + i)


@cocotb.test(timeout_time=50, timeout_unit="ms")
async def test_hold(dut):
    m = await start(dut)
    await cycle(dut, m, {"rst_n": 1, "en": 0, "up": 1, "load": 1, "load_value": 77}, 0)
    for i in range(30):
        await cycle(dut, m, {"rst_n": 1, "en": 0, "up": random.randint(0, 1), "load": 0, "load_value": random.randint(0, 255)}, i)
