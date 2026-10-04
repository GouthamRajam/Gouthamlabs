"""M0.5 deterministic checks, knowledge base, agent definitions and prompts (no services needed)."""
from __future__ import annotations

import copy
import re
from pathlib import Path

import yaml

from s2s.agents import llm
from s2s.design import checks
from s2s.knowledge import kb

FIX = Path(__file__).parent / "platform" / "m05_fixtures"
REPO = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((FIX / "counter8_spec.yaml").read_text())
ARCH = yaml.safe_load((FIX / "counter8_arch.yaml").read_text())
M05_AGENTS = ["Juno", "Iris", "Kepler", "Pascal", "Ivy", "Reid", "Ada", "Ada-C", "Ada-I", "Watt", "Lumen",
              "Sentinel", "Sage"]


def test_good_spec_and_arch_pass():
    assert checks.spec_schema(SPEC) == []
    assert checks.spec_consistency(SPEC) == []
    assert checks.arch_schema(ARCH) == []
    assert checks.arch_consistency(ARCH, SPEC) == []


def test_spec_missing_reset_behavior_is_caught():
    bad = copy.deepcopy(SPEC)
    bad["requirements"] = [r for r in bad["requirements"] if r["type"] != "reset"]
    del bad["interfaces"][-1]["reset_value"]
    problems = checks.spec_consistency(bad)
    print(problems)
    assert any("no requirement of type 'reset'" in p for p in problems)
    assert any("output 'count' has no reset_value" in p for p in problems)


def test_spec_schema_and_consistency_failures():
    bad = copy.deepcopy(SPEC)
    bad["requirements"][0]["id"] = "R1"
    bad["pdk"] = "gf180mcuC"
    assert any("requirements/0/id" in p for p in checks.spec_schema(bad))
    bad = copy.deepcopy(SPEC)
    bad["target_clock_mhz"] = 50
    bad["resets"][0]["name"] = "rst"
    bad["interfaces"][1]["name"] = "rst"
    problems = checks.spec_consistency(bad)
    assert any("target_clock_mhz 50" in p for p in problems)
    assert any("must end in _n" in p for p in problems)


def test_arch_consistency_failures():
    bad = copy.deepcopy(ARCH)
    bad["modules"][0]["implements"] = ["REQ-001", "REQ-009"]
    bad["ppa_estimate"]["slack_margin_pct"] = 5
    bad["modules"][0]["ports_from_spec"] = False
    bad["modules"][0]["ports"] = [{"name": "clk", "dir": "in", "width": 1},
                                  {"name": "count", "dir": "out", "width": "WIDTH-1"}]
    problems = checks.arch_consistency(bad, SPEC)
    print("\n".join(problems))
    for want in ("REQ-002 is not implemented", "REQ-009, which is not in the spec", "below 15%",
                 "spec interface 'rst_n' is missing", "top port 'count' is ('out', 7)"):
        assert any(want in p for p in problems), want


def test_rtl_structure():
    good = {"rtl/counter8.v": (FIX / "counter8.v").read_text()}
    assert checks.rtl_structure(good, ARCH) == []
    bad = {"rtl/count.v": "module counter8; initial x = 1; endmodule\n"}
    problems = checks.rtl_structure(bad, ARCH)
    assert any("file name must equal module name" in p for p in problems)
    assert any("initial block" in p for p in problems)


def test_width_parser_never_executes_text():
    assert checks._width("WIDTH-1", {"WIDTH": 8}) == 7
    assert checks._width("__import__('os').system('true')", {}) is None


def test_kb_seed_entries_are_sourced_and_searchable():
    for e in kb.seed_entries():
        assert {"id", "title", "lesson", "source", "date", "confidence", "owner"} <= set(e), e["id"]
        assert e["source"]["url"]
    hits = kb.search("8-bit up/down counter with synchronous reset, enable and load")
    print([h["id"] for h in hits])
    assert hits and hits[0]["id"] == "kb-fc-007"
    assert any(e["kind"] == "failure_case" for e in kb.seed_entries())


def test_every_m05_agent_has_a_definition_and_a_verbatim_prompt():
    spec = (REPO / "docs" / "MASTER_SPEC.md").read_text()
    for name in M05_AGENTS:
        a = llm.agent(name)
        body = llm._prompt(a.prompt)
        assert body and body in spec, f"{a.prompt} is not verbatim from MASTER_SPEC"
        if a.preamble == "design":
            assert llm.system_prompt(a).startswith(f"You are {name}, the {a.role} of S2S")
    for f in ("A.0_preamble.md", "A3_preamble_additions.md", "A.20_task_envelope.md"):
        assert llm._prompt(f) in spec


def test_read_and_write_paths():
    iris = llm.agent("Iris")
    assert llm.path_allowed("spec/spec.yaml", iris.writes_to)
    assert not llm.path_allowed("rtl/counter8.v", iris.writes_to)
    assert not llm.path_allowed("spec/../rtl/x.v", iris.writes_to)
    assert not llm.path_allowed("/etc/passwd", iris.writes_to)
    assert not any(llm.path_allowed(p, llm.agent("Sentinel").writes_to) for p in ("spec/spec.yaml", "rtl/a.v"))
    assert re.search(r"^\s*module counter8", (FIX / "counter8.v").read_text(), re.M)
