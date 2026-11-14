"""Dex triage suite (M0.6 acceptance 5): 10 seeded failures with known classes (DESIGN / TEST / SPEC).

Each scenario is a known edit to the counter8 fixture (spec, RTL, testbench or reference model).
The harness RUNS the regression for every scenario with the real simulator; a scenario that does
not actually fail is rejected (never classified). Dex then sees exactly what it would see in a real
run (spec, plan, testbench, model, RTL and the real failure output) and classifies it; the answer is
scored against the known class.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FIX5 = Path(__file__).resolve().parents[2] / "tests/platform/m05_fixtures"
FIX6 = Path(__file__).resolve().parents[2] / "tests/platform/m06_fixtures"


@dataclass(frozen=True)
class Scenario:
    id: str
    truth: str  # DESIGN | TEST | SPEC
    what: str   # how it was seeded (never shown to Dex)
    spec: tuple = ()   # (old, new) replacements on spec.yaml
    rtl: tuple = ()
    tb: tuple = ()
    model: tuple = ()


R_LOAD = "count_d = load_value;                   // REQ-002"
R_INC = "if (up) count_d = count_q + 1'b1;       // REQ-003 (wraps modulo 2^WIDTH)"
R_DEC = "else    count_d = count_q - 1'b1;       // REQ-003"
R_RST = "if (!rst_n) count_q <= {WIDTH{1'b0}};       // REQ-001"
M_STEP = 'self.count = (self.count + (1 if txn["up"] else -1)) % 256'

SCENARIOS = [
    Scenario("D1", "DESIGN", "RTL loads only when enable is also high",
             rtl=(("if (load) begin", "if (load && en) begin"),)),
    Scenario("D2", "DESIGN", "RTL saturates at 255 instead of wrapping",
             rtl=((R_INC, "if (up) count_d = (count_q == {WIDTH{1'b1}}) ? count_q : count_q + 1'b1;  // REQ-003"),)),
    Scenario("D3", "DESIGN", "RTL resets to 1 instead of 0",
             rtl=((R_RST, "if (!rst_n) count_q <= {{(WIDTH-1){1'b0}}, 1'b1};  // REQ-001"),)),
    Scenario("D4", "DESIGN", "RTL counts down when up=1 and up when up=0",
             rtl=((R_INC, "if (up) count_d = count_q - 1'b1;       // REQ-003"),
                  (R_DEC, "else    count_d = count_q + 1'b1;       // REQ-003"))),
    Scenario("T1", "TEST", "reference model decrements by 2",
             model=((M_STEP, 'self.count = (self.count + (1 if txn["up"] else -2)) % 256'),)),
    Scenario("T2", "TEST", "testbench reads count before the clock edge (sampling one cycle early)",
             tb=(("    await RisingEdge(dut.clk)\n    await ReadOnly()\n    got = int(dut.count.value)",
                  "    await ReadOnly()\n    got = int(dut.count.value)\n    await RisingEdge(dut.clk)"),)),
    Scenario("T3", "TEST", "test_hold expects count to be 0 while holding a loaded 77",
             tb=(('        await cycle(dut, m, {"rst_n": 1, "en": 0, "up": random.randint(0, 1), "load": 0, "load_value": random.randint(0, 255)}, i)\n',
                  '        await cycle(dut, m, {"rst_n": 1, "en": 0, "up": random.randint(0, 1), "load": 0, "load_value": random.randint(0, 255)}, i)\n'
                  '        assert int(dut.count.value) == 0, f"hold: count={int(dut.count.value)} expected 0"\n'),)),
    Scenario("S1", "SPEC", "spec contradicts itself on load vs enable priority; RTL and model each follow one REQ",
             spec=(('text: "When en is 1 and load is 0, count increments by 1 if up is 1, else decrements by 1, wrapping modulo 256."',
                    'text: "Whenever en is 1, count increments by 1 if up is 1, else decrements by 1, wrapping modulo 256; enable takes priority over every other control."'),),
             model=(('elif txn["load"]:\n            self.count = txn["load_value"] & 0xFF\n        elif txn["en"]:\n            self.count = (self.count + (1 if txn["up"] else -1)) % 256',
                     'elif txn["en"]:\n            self.count = (self.count + (1 if txn["up"] else -1)) % 256\n        elif txn["load"]:\n            self.count = txn["load_value"] & 0xFF'),)),
    Scenario("S2", "SPEC", "spec says both 'wraps modulo 256' and 'saturates at 255'; RTL wraps, model saturates",
             spec=(('acceptance: "255+1 == 0 and 0-1 == 255 checked; 10,000 random cycles match a reference model."}',
                    'acceptance: "255+1 == 0 and 0-1 == 255 checked; 10,000 random cycles match a reference model."}\n'
                    '  - {id: REQ-005, type: functional, text: "count saturates: it never goes above 255 or below 0.", '
                    'acceptance: "count stays at 255 when counting up at 255, and at 0 when counting down at 0."}'),),
             model=((M_STEP, 'self.count = min(255, self.count + 1) if txn["up"] else max(0, self.count - 1)'),)),
    Scenario("S3", "SPEC", "spec no longer says what happens when en=0 and load=0; model clears, RTL holds",
             spec=(('  - {id: REQ-004, type: functional, text: "When en is 0 and load is 0, count holds its value.", acceptance: "count unchanged over 100 random cycles with en=0."}\n', ''),),
             model=(('        return {"count": self.count}', '        else:\n            self.count = 0\n        return {"count": self.count}'),)),
]


def _apply(text: str, edits: tuple, what: str) -> str:
    for old, new in edits:
        if old not in text:
            raise ValueError(f"scenario edit does not apply to {what}: {old[:60]!r}")
        text = text.replace(old, new)
    return text


def build(sc: Scenario, d: Path) -> dict[str, str]:
    """Write the scenario's files under d; returns path -> text (what Dex may read)."""
    spec = _apply((FIX5 / "counter8_spec.yaml").read_text(), sc.spec, "spec")
    spec = re.sub(r"(?m)^# Hand-written.*\n", "", spec)
    rtl = _apply((FIX5 / "counter8.v").read_text(), sc.rtl, "rtl")
    rtl = rtl.replace("Hand-written test fixture (scripted answer), not agent output.", "")
    tb = _apply((FIX6 / "test_counter8.py").read_text(), sc.tb, "tb").replace(
        "# Hand-written test fixture (scripted model answer). Not agent output.\n", "")
    model = _apply((FIX6 / "ref_model.py").read_text(), sc.model, "model").replace(
        "# Hand-written test fixture (scripted model answer). Not agent output.\n", "")
    plan = (FIX6 / "testplan.yaml").read_text().replace(
        "# Hand-written test fixture (scripted model answer for offline plumbing tests). Not agent output.\n", "")
    files = {"spec/spec.yaml": spec, "rtl/counter8.v": rtl, "tb/test_counter8.py": tb, "tb/ref_model.py": model,
             "tb/testplan.yaml": plan, "arch/arch.yaml": (FIX5 / "counter8_arch.yaml").read_text()}
    for p, t in files.items():
        (d / p).parent.mkdir(parents=True, exist_ok=True)
        (d / p).write_text(t)
    return files
