"""M0.6 plumbing, offline: real Postgres/Redis and REAL Verilator/Icarus/Yosys/SymbiYosys (s2s-eda),
SCRIPTED model answers (hand-written fixtures in m06_fixtures/). Checks the verification runtime
(independence, N-version, regression, coverage, formal, Dex routing, anti-cheating guard,
mutation) without spending money. The real-model runs are scripts/run_m06.py."""
from __future__ import annotations

import json
import shutil
from collections import deque
from pathlib import Path

import pytest
from sqlalchemy import select

from tests.platform.conftest import new_design
from tests.platform.test_m05_offline import ans, checks_of, eda_available, events, files

F5 = Path(__file__).parent / "m05_fixtures"
F6 = Path(__file__).parent / "m06_fixtures"
PLAN, TB, PROPS = (F6 / "testplan.yaml").read_text(), (F6 / "test_counter8.py").read_text(), (F6 / "formal_top.sv").read_text()
MODEL_A, MODEL_B, MODEL_WRONG = ((F6 / n).read_text() for n in ("ref_model.py", "ref_model_b.py", "ref_model_wrong.py"))
NO_FINDINGS = ans(findings=[])

pytestmark = pytest.mark.skipif(not eda_available(), reason="s2s-eda image not built")


def source_run(rtl: str | None = None) -> str:
    from s2s.agents.runtime import artifact_dir
    src = "run_fixture_m05_counter8"
    root = artifact_dir() / "runs" / src
    shutil.rmtree(root, ignore_errors=True)
    for d in ("spec", "arch", "rtl"):
        (root / d).mkdir(parents=True)
    (root / "spec/spec.yaml").write_text((F5 / "counter8_spec.yaml").read_text())
    (root / "spec/spec.md").write_text("# counter8 spec (fixture)\n")
    (root / "arch/arch.yaml").write_text((F5 / "counter8_arch.yaml").read_text())
    (root / "rtl/counter8.v").write_text(rtl or (F5 / "counter8.v").read_text())
    return src


def run_m06(platform, replies: list, rtl: str | None = None, stages=("test_build", "verification")):
    from s2s.agents.m05 import DesignAgent
    from s2s.agents.runtime import run_task
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.models.gateway import ModelGateway, ScriptedProvider
    from s2s.orchestrator.engine import create_run
    provider = ScriptedProvider(deque(replies))
    src = source_run(rtl)
    with session() as s:
        d = new_design(s, "counter8")
        run = create_run(s, d, from_stage="test_build", to_stage="verification", agent_kind="s2s",
                         inputs={"source_run": src})
        run_id = run.id
    out = {}
    for st in stages:
        with session() as s:
            t = s.scalar(select(Task).where(Task.run_id == run_id, Task.stage == st))
            t.status = "running"
            tid = t.id
        out[st] = run_task(tid, DesignAgent(), ModelGateway(provider))
        if out[st].status != "completed":
            break
    return run_id, out, provider


def report(run_id) -> dict:
    from s2s.agents.runtime import artifact_dir
    return json.loads((artifact_dir() / "runs" / run_id / "reports/verification_report.json").read_text())


TEST_BUILD = [files(("tb/testplan.yaml", PLAN)), files(("tb/ref_model_a.py", MODEL_A)),
              files(("tb/ref_model_b.py", MODEL_B)), files(("tb/test_counter8.py", TB)),
              files(("formal/formal_top.sv", PROPS)), NO_FINDINGS]


def test_counter8_verification_end_to_end(platform):
    run_id, out, provider = run_m06(platform, list(TEST_BUILD))
    print({k: (v.status, v.detail) for k, v in out.items()})
    from s2s.db.models import Check
    from s2s.db.session import session
    with session() as s:
        for c in s.scalars(select(Check).order_by(Check.id)):
            print("CHECK", c.check_name, c.passed, (c.metrics or {}).get("detail"))
    assert {k: v.status for k, v in out.items()} == {"test_build": "completed", "verification": "completed"}
    got = dict(checks_of(run_id))
    print(checks_of(run_id))
    for name in ("dut_port_list", "testplan_schema", "testplan_trace", "nversion_agreement", "testbench_static",
                 "formal_properties_static", "regression_100pct", "coverage_line", "coverage_toggle",
                 "coverage_functional", "requirements_traced", "formal_3_meaningful", "formal_vacuity",
                 "anti_cheat_final", "task_result_schema"):
        assert got[name] is True, name
    rep = report(run_id)
    print(json.dumps({k: rep[k] for k in ("coverage", "formal", "mutation")}, indent=1))
    m = rep["mutation"][-1]
    # The one-module fixture RTL is too small for 20 distinct, non-equivalent mutants: the check must
    # say so (fail), never pass on fewer. (The real designs yield 20; see run_m06.py.)
    assert m["rate"] >= 0.85
    assert got["mutation_detection"] is (m["total"] == 20)
    assert rep["formal"]["proven_meaningful"] >= 3 and not rep["formal"]["vacuous"]
    assert not provider.replies
    # independence: no 2B agent call carried an RTL file
    for c in provider.calls[:6]:
        assert "=== rtl/" not in c["messages"][0]["content"]
        assert "module counter8" not in c["messages"][0]["content"].split("INPUT FILES")[1]
    agents = {a for _, a, _, _ in events(run_id)}
    assert {"Nadia", "Rhea", "Vera", "Mira", "Theo", "Euclid", "Rex", "Cora", "Myra", "Sentinel"} <= agents


def test_nversion_difference_goes_to_vera(platform):
    adjudicate = ans(decision="model_a", reason="REQ-003: wrap modulo 256; model B wraps at 255", spec_question="")
    replies = [TEST_BUILD[0], TEST_BUILD[1], files(("tb/ref_model_b.py", MODEL_WRONG)), adjudicate, *TEST_BUILD[3:]]
    run_id, out, provider = run_m06(platform, replies, stages=("test_build",))
    assert out["test_build"].status == "completed"
    from s2s.agents.runtime import artifact_dir
    nv = json.loads((artifact_dir() / "runs" / run_id / "reports/nversion.json").read_text())
    print(nv["total_mismatches"], nv["mismatches"][0])
    assert nv["total_mismatches"] > 0
    assert "tb/ref_model_a.py" in provider.calls[3]["messages"][0]["content"]
    assert (artifact_dir() / "runs" / run_id / "tb/ref_model.py").read_text() == MODEL_A + ("" if MODEL_A.endswith("\n") else "\n")


def test_rtl_bug_is_found_triaged_and_fixed(platform):
    good = (F5 / "counter8.v").read_text()
    buggy = good.replace("count_d = load_value;                   // REQ-002",
                         "count_d = load_value + 1'b1;            // REQ-002")
    assert buggy != good
    dex = ans(bugs=[{"id": "b1", "classification": "DESIGN", "failures": ["test_load", "ap_load"],
                     "requirement": "REQ-002", "root_cause": "load adds 1 to load_value", "evidence": "seed 1",
                     "expected": "count == load_value", "actual": "load_value + 1", "module": "counter8",
                     "suggested_fix": "assign load_value directly"}])
    replies = [*TEST_BUILD, dex, files(("rtl/counter8.v", good))]
    run_id, out, provider = run_m06(platform, replies, rtl=buggy)
    assert out["verification"].status == "completed", out["verification"].detail
    rep = report(run_id)
    assert [b["classification"] for b in rep["real_rtl_bugs"]] == ["DESIGN"]
    assert rep["real_rtl_bugs"][0]["routed_to"] == "Ada"
    lint = [p for n, p in checks_of(run_id) if n == "verilator_lint"]
    assert lint == [True]  # Lumen re-checked the fixed RTL


def test_guard_rejects_a_weakened_test_fix(platform):
    # planted TEST bug: a wrong expectation at the end of test_load (count is never forced to 0 there)
    tb_bug = TB.replace('''        await cycle(dut, m, {"rst_n": 1, "en": random.randint(0, 1), "up": random.randint(0, 1), "load": 1, "load_value": v}, i)
''', '''        await cycle(dut, m, {"rst_n": 1, "en": random.randint(0, 1), "up": random.randint(0, 1), "load": 1, "load_value": v}, i)
    assert int(dut.count.value) == 0, "planted wrong expectation"
''')
    # the "fix" that cheats: the scoreboard comparison is deleted instead of the wrong expectation
    weak = tb_bug.replace('    assert got == exp, f"cycle {i} {txn}: count={got} expected {exp}"\n', "    pass\n")
    assert tb_bug != TB
    dex = ans(bugs=[{"id": "b1", "classification": "TEST", "failures": ["test_load"], "requirement": "REQ-002",
                     "root_cause": "x", "evidence": "y", "expected": "e", "actual": "a", "module": "",
                     "suggested_fix": "z"}])
    reject = ans(findings=[{"severity": "blocking", "target": "tb/test_counter8.py", "what": "assertion removed",
                            "evidence": "guard", "suggested_action": "restore"}])
    replies = [TEST_BUILD[0], TEST_BUILD[1], TEST_BUILD[2], files(("tb/test_counter8.py", tb_bug)), *TEST_BUILD[4:],
               dex, files(("tb/test_counter8.py", weak)), reject, dex, files(("tb/test_counter8.py", weak)), reject]
    run_id, out, provider = run_m06(platform, replies)
    evs = events(run_id)
    flagged = [e for e in evs if e[0] == "finding" and "Anti-cheating guard" in e[2]]
    print(flagged[0][3]["flags"])
    assert any("fewer assertions" in f for f in flagged[0][3]["flags"])
    assert [p for n, p in checks_of(run_id) if n == "anti_cheat_guard"][:1] == [False]
    from s2s.agents.runtime import artifact_dir
    assert "assert got == exp" in (artifact_dir() / "runs" / run_id / "tb/test_counter8.py").read_text()  # reverted
    assert out["verification"].status == "paused"  # the planted test bug was never legitimately fixed


def test_tautological_property_goes_back_to_euclid(platform):
    taut = PROPS.replace("    ap_reset: assert ($past(rst_n) || count == 8'd0);", "    ap_reset: assert ($past(rst_n) || 1'b1);")
    assert taut != PROPS
    replies = [*TEST_BUILD[:4], files(("formal/formal_top.sv", taut)), NO_FINDINGS,
               files(("formal/formal_top.sv", PROPS))]
    run_id, out, provider = run_m06(platform, replies)
    assert out["verification"].status == "completed", out["verification"].detail
    evs = events(run_id)
    h = [e for e in evs if e[0] == "handoff" and "formal quality" in e[2]]
    print(h[0][3]["issues"])
    assert any("ap_reset" in i and "tautology" in i for i in h[0][3]["issues"])
    assert dict(checks_of(run_id))["formal_3_meaningful"] is True
    assert report(run_id)["formal"]["tautologies"] == []


def test_large_plan_is_written_as_env_plus_test_batches(platform, monkeypatch):
    from s2s.agents import m06
    monkeypatch.setattr(m06, "THEO_SINGLE_ANSWER_MAX_TESTS", 2)
    monkeypatch.setattr(m06, "THEO_BATCH", 2)
    head, *tests = TB.split("@cocotb.test(")
    env = head  # imports + helpers (cycle, start), no tests
    imp = "import random\nimport cocotb\nfrom tb_counter8 import cycle, start\n\n"
    b1 = imp + "".join("@cocotb.test(" + t for t in tests[:2])
    b2 = imp + "".join("@cocotb.test(" + t for t in tests[2:])
    replies = [*TEST_BUILD[:3], files(("tb/tb_counter8.py", env)), files(("tb/test_counter8_1.py", b1)),
               files(("tb/test_counter8_2.py", b2)), *TEST_BUILD[4:]]
    run_id, out, provider = run_m06(platform, replies)
    assert {k: v.status for k, v in out.items()} == {"test_build": "completed", "verification": "completed"}, out
    got = dict(checks_of(run_id))
    assert got["testbench_env_static"] and got["testbench_batch_static"] and got["testbench_static"]
    assert got["regression_100pct"] and got["requirements_traced"]
    assert "test_reset, test_load" in provider.calls[4]["messages"][0]["content"]


def test_impossible_bin_is_reclassified_as_an_illegal_state(platform):
    """Operator decision: an unreachable coverage bin becomes a must-never-happen assertion (not a waiver).
    Mechanics only (setup + change request): Vera moves the bin, Euclid adds the assertion, the guard flags
    the removed bin and Sentinel must approve. (On counter8 no behavioural illegal state exists - "count >
    255" is impossible by construction and the formal tautology check rightly rejects it - so the end-to-end
    proof is the real sync_fifo run.)"""
    from s2s.agents.m06 import verification_steps
    from s2s.agents.runtime import Agent, run_task
    from s2s.db.models import Design, Run, Task
    from s2s.db.session import session
    from s2s.models.gateway import ModelGateway, ScriptedProvider
    from s2s.orchestrator.engine import create_run
    from s2s.agents.runtime import artifact_dir
    imp = "  - {name: count_above_255, expr: \"count > 255\", req: REQ-003}\n"
    run1, _, _ = run_m06(platform, [files(("tb/testplan.yaml", PLAN + imp)), *TEST_BUILD[1:]], stages=("test_build",))
    plan_new = PLAN + ("illegal_states:\n  - {name: count_above_255, expr: \"count > 255\", req: REQ-003, "
                       "assertion: never_count_above_255, reason: \"an 8-bit count cannot exceed 255\"}\n")
    props_new = PROPS.replace("  end\nendmodule", "    ap_never_count_above_255: assert (!(count > 9'd255));\n"
                              "    cp_never_count_above_255: cover (count == 8'd255);\n  end\nendmodule")
    provider = ScriptedProvider(deque([files(("tb/testplan.yaml", plan_new)), files(("formal/formal_top.sv", props_new)),
                                       ans(findings=[])]))

    class FirstSteps(Agent):
        def steps(self, task):
            return verification_steps()[:3]  # setup, change_requests, stop_if_blocked
    with session() as s:
        dsn = s.get(Design, s.get(Run, run1).design_id)
        run2 = create_run(s, dsn, from_stage="verification", to_stage="verification", agent_kind="s2s",
                          inputs={"source_run": run1, "change_requests": [
                              {"kind": "reclassify_bin_to_illegal_state", "bin": "count_above_255",
                               "reason": "an 8-bit count can never exceed 255"}]}).id
        t = s.scalar(select(Task).where(Task.run_id == run2))
        t.status, tid = "running", t.id
    out = run_task(tid, FirstSteps(), ModelGateway(provider))
    assert out.status == "completed", out.detail
    root = artifact_dir() / "runs" / run2
    import yaml
    plan = yaml.safe_load((root / "tb/testplan.yaml").read_text())
    assert "count_above_255" not in [b["name"] for b in plan["coverage_bins"]]
    assert plan["illegal_states"][0]["assertion"] == "never_count_above_255"
    assert "ap_never_count_above_255" in (root / "formal/formal_top.sv").read_text()
    assert (root / "guard_baseline/tb/testplan.yaml").read_text().count("count_above_255") == 1  # baseline kept
    flagged = [e for e in events(run2) if e[0] == "finding" and "Anti-cheating guard" in e[2]]
    print(flagged[0][3]["flags"])
    assert any("coverage bin 'count_above_255' was removed" in f for f in flagged[0][3]["flags"])
    assert [p for n, p in checks_of(run2) if n == "anti_cheat_guard"] == [True]  # flagged, approved by Sentinel
    assert not provider.replies
