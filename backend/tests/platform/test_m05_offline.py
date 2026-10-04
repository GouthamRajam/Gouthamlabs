"""M0.5 plumbing, offline: real Postgres/Redis, real Verilator/Yosys (s2s-eda), SCRIPTED model.

The model answers here are hand-written fixtures (ScriptedProvider), so these tests check the
runtime (paths, checks, routing, events, metering, pauses) without spending money. The
acceptance run with the real model is scripts/run_m05.py and test_m05_acceptance.py.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import pytest
from sqlalchemy import select

from tests.platform.conftest import new_design

FIX = Path(__file__).parent / "m05_fixtures"


def eda_available() -> bool:
    from s2s.tools import runner
    try:
        runner.image_id()
        return True
    except runner.EdaUnavailable:
        return False


def ans(**extra) -> dict:
    return {"plan": "Plan: read inputs, write, check, report.", "status": "success", "summary": "done",
            "assumptions": ["fixture assumption"], "open_issues": [],
            "self_assessment": {"confidence": "high", "reason": "fixture"}, **extra}


def files(*pairs) -> dict:
    return ans(files=[{"path": p, "content": c} for p, c in pairs])


SPEC = (FIX / "counter8_spec.yaml").read_text()
ARCH = (FIX / "counter8_arch.yaml").read_text()
RTL = (FIX / "counter8.v").read_text()
RTL_BUG = (FIX / "counter8_lintbug.v").read_text()
REPORT = ans(report_markdown="# Report\nNo external standard applies.")
NO_FINDINGS = ans(findings=[])
SAGE = ans(report_markdown="# Retrospective", lessons=[])


def run_stages(platform, replies: list, stages=("spec", "architecture", "rtl")):
    from s2s.agents.m05 import DesignAgent
    from s2s.agents.runtime import run_task
    from s2s.db.models import Task
    from s2s.db.session import session
    from s2s.models.gateway import ModelGateway, ScriptedProvider
    from s2s.orchestrator.engine import create_run
    provider = ScriptedProvider(deque(replies))
    with session() as s:
        d = new_design(s, "counter8")
        d.request_text = "8-bit up/down counter with synchronous reset, enable and load."
        run = create_run(s, d, to_stage=stages[-1], agent_kind="s2s")
        run_id = run.id
    outcomes = {}
    for st in stages:
        with session() as s:
            t = s.scalar(select(Task).where(Task.run_id == run_id, Task.stage == st))
            t.status = "running"
            tid = t.id
        outcomes[st] = run_task(tid, DesignAgent(), ModelGateway(provider))
        if outcomes[st].status != "completed":
            break
    return run_id, outcomes, provider


def events(run_id):
    from s2s.db.models import Event
    from s2s.db.session import session
    with session() as s:
        return [(e.type, e.agent_id, e.summary, e.detail) for e in
                s.scalars(select(Event).where(Event.run_id == run_id).order_by(Event.ts, Event.id))]


def checks_of(run_id):
    from s2s.db.models import Check, Task
    from s2s.db.session import session
    with session() as s:
        return [(c.check_name, c.passed) for c in s.scalars(
            select(Check).join(Task, Task.id == Check.task_id).where(Task.run_id == run_id).order_by(Check.id))]


pytestmark = pytest.mark.skipif(not eda_available(), reason="s2s-eda image not built")


def test_counter8_all_three_stages_with_scripted_answers(platform):
    replies = [REPORT, files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# counter8 spec")), NO_FINDINGS,
               files(("arch/arch.yaml", ARCH)), REPORT, NO_FINDINGS,
               files(("rtl/counter8.v", RTL)), REPORT, SAGE]
    run_id, out, provider = run_stages(platform, replies)
    assert {k: v.status for k, v in out.items()} == {"spec": "completed", "architecture": "completed",
                                                     "rtl": "completed"}
    got = dict(checks_of(run_id))
    print(checks_of(run_id))
    for name in ("spec_schema", "spec_consistency", "sentinel_spec_review", "arch_schema", "arch_consistency",
                 "sentinel_arch_review", "rtl_structure", "verilator_lint", "yosys_elab", "rtl_ports_match_arch",
                 "task_result_schema"):
        assert got[name] is True, name
    evs = events(run_id)
    agents = {a for _, a, _, _ in evs}
    assert {"Iris", "Ivy", "Sage", "Sentinel", "Kepler", "Pascal", "Lumen", "Watt", "Ada"} <= agents
    assert any(t == "handoff" and a == "Reid" and "assigned counter8 to Ada" in s for t, a, s, _ in evs)
    # every model call metered under the agent that made it
    from s2s.db.models import UsageRecord
    from s2s.db.session import session
    with session() as s:
        by_agent = sorted(s.scalars(select(UsageRecord.agent_id).where(UsageRecord.run_id == run_id,
                                                                       UsageRecord.source == "llm")))
    assert by_agent == sorted(["Ivy", "Iris", "Sentinel", "Kepler", "Pascal", "Sentinel", "Ada", "Watt", "Sage"])
    assert not provider.replies
    # writers get the Appendix B example and the exact schema their file is checked against
    iris, kepler = provider.calls[1]["messages"][0]["content"], provider.calls[3]["messages"][0]["content"]
    assert "Appendix B.1 example" in iris and '"std_cell_library"' in iris and "rx_valid" in iris
    assert "Appendix B.2 example" in kepler and '"ppa_estimate"' in kepler
    # Ada was given the coding standard and Sage's knowledge
    ada_call = provider.calls[6]
    assert "Coding standard" in ada_call["messages"][0]["content"] and ada_call["effort"] == "medium"
    assert ada_call["schema"]["required"][-1] == "files"


def test_lint_failure_goes_back_to_ada_with_the_tool_output(platform):
    replies = [REPORT, files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# spec")), NO_FINDINGS,
               files(("arch/arch.yaml", ARCH)), REPORT, NO_FINDINGS,
               files(("rtl/counter8.v", RTL_BUG)), files(("rtl/counter8.v", RTL)), REPORT, SAGE]
    run_id, out, provider = run_stages(platform, replies)
    assert out["rtl"].status == "completed"
    lint = [p for n, p in checks_of(run_id) if n == "verilator_lint"]
    assert lint == [False, True]
    retry_prompt = provider.calls[7]["messages"][0]["content"]
    print(retry_prompt[retry_prompt.index("previous_attempts"):][:400])
    assert "WIDTH" in retry_prompt and "counter8.v:29" in retry_prompt
    assert any(t == "handoff" and a == "Lumen" for t, a, _, _ in events(run_id))


def test_spec_consistency_failure_then_fix(platform):
    no_reset = SPEC.replace("reset_value: 0}", "}").replace(
        '  - {id: REQ-001, type: reset', '  - {id: REQ-001, type: functional')
    replies = [REPORT, files(("spec/spec.yaml", no_reset), ("spec/spec.md", "# s")),
               files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# s")), NO_FINDINGS]
    run_id, out, provider = run_stages(platform, replies, stages=("spec",))
    assert out["spec"].status == "completed"
    assert [p for n, p in checks_of(run_id) if n == "spec_consistency"] == [False, True]
    assert "no requirement of type 'reset'" in provider.calls[2]["messages"][0]["content"]


def test_blocking_findings_twice_pause_for_a_human(platform):
    blocking = ans(findings=[{"severity": "blocking", "target": "spec/spec.yaml: REQ-003", "what": "x",
                              "evidence": "y", "suggested_action": "z"}])
    replies = [REPORT, files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# s")), blocking,
               files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# s")), blocking]
    run_id, out, provider = run_stages(platform, replies, stages=("spec",))
    assert out["spec"].status == "paused"
    evs = events(run_id)
    assert sum(t == "finding" for t, *_ in evs) == 2
    esc = [e for e in evs if e[0] == "escalation"][-1]
    print(esc[2])
    assert "blocking Sentinel finding" in esc[2]
    # the review evidence survived the pause (written before the stop step)
    assert [p for n, p in checks_of(run_id) if n == "sentinel_spec_review"] == [False, False]


def test_writes_outside_allowed_paths_are_refused(platform):
    replies = [REPORT, files(("spec/spec.yaml", SPEC), ("rtl/evil.v", "module evil; endmodule"))]
    run_id, out, _ = run_stages(platform, replies, stages=("spec",))
    assert out["spec"].status == "failed"
    assert "may not write rtl/evil.v" in out["spec"].detail["error"]
    from s2s.agents.runtime import artifact_dir
    assert not (artifact_dir() / "runs" / run_id / "rtl" / "evil.v").exists()
    assert not (artifact_dir() / "runs" / run_id / "spec" / "spec.yaml").exists()


def test_spend_cap_pauses_the_design_agents(platform):
    import yaml
    from s2s.config import REPO_ROOT
    fin = yaml.safe_load((REPO_ROOT / "config" / "finance.yaml").read_text())
    fin["spend_caps"] = {"per_design_usd": 0.0001, "daily_usd": 100}
    platform.set_config("finance", fin)
    replies = [REPORT, files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# s")), NO_FINDINGS]
    run_id, out, provider = run_stages(platform, replies, stages=("spec",))
    assert out["spec"].status == "paused"
    assert len(provider.calls) == 1  # the first call crossed the cap; no further call was made
    esc = [e for e in events(run_id) if e[0] == "escalation"][-1]
    print(esc[2])
    assert "per-design spend cap reached" in esc[2]


def test_orchestrator_runs_the_design_agents_through_g1(platform, monkeypatch):
    """The real orchestrator loop (in-process) with the scripted model: assignment briefs, G1 auto-gate
    after architecture, rtl, run completion, management loop."""
    import time
    from s2s.db.session import session
    from s2s.models.gateway import ModelGateway, ScriptedProvider
    from s2s.orchestrator import engine
    replies = deque([REPORT, files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# s")), NO_FINDINGS,
                     files(("arch/arch.yaml", ARCH)), REPORT, NO_FINDINGS, files(("rtl/counter8.v", RTL)),
                     REPORT, SAGE])
    provider = ScriptedProvider(replies)
    monkeypatch.setitem(engine.GATEWAYS, "s2s", lambda: ModelGateway(provider))
    with session() as s:
        d = new_design(s, "counter8")
        run_id = engine.create_run(s, d, to_stage="rtl", agent_kind="s2s").id
    orc = engine.Orchestrator(max_parallel=2, poll_s=0.05)
    orc.start()
    end = time.monotonic() + 120
    while time.monotonic() < end:
        orc.tick()
        from s2s.db.models import Run
        with session() as s:
            if s.get(Run, run_id).status in ("completed", "failed"):
                break
        time.sleep(0.05)
    orc.pool.shutdown(wait=True)
    orc._lock_conn.close()
    from s2s.db.models import Run
    with session() as s:
        assert s.get(Run, run_id).status == "completed"
    evs = events(run_id)
    assert any(t == "gate.decided" and "G1 auto-approved" in s for t, _, s, _ in evs)
    assert [a for t, a, s, _ in evs if t == "handoff" and "assigned '" in s] == ["Juno", "Juno", "Reid"]
    assert not provider.replies


ARCH2 = ARCH.replace("""modules:
  - name: counter8
    kind: datapath
    ports_from_spec: true
    params: {WIDTH: 8}
    implements: [REQ-001, REQ-002, REQ-003, REQ-004]""", """modules:
  - name: counter8
    kind: interface
    ports_from_spec: true
    instances: [counter_core]
    implements: [REQ-001]
  - name: counter_core
    kind: datapath
    params: {WIDTH: 8}
    ports:
      - {name: clk, dir: in, width: 1}
      - {name: rst_n, dir: in, width: 1}
      - {name: en, dir: in, width: 1}
      - {name: up, dir: in, width: 1}
      - {name: load, dir: in, width: 1}
      - {name: load_value, dir: in, width: WIDTH}
      - {name: count, dir: out, width: WIDTH}
    implements: [REQ-001, REQ-002, REQ-003, REQ-004]""")
CORE = RTL.replace("module counter8 #(", "module counter_core #(")
WRAP = """// counter8 top: wiring only. REQ-001 (reset handled in counter_core). Test fixture.
module counter8 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire       up,
    input  wire       load,
    input  wire [7:0] load_value,
    output wire [7:0] count
);
    counter_core #(.WIDTH(8)) u_core (.clk(clk), .rst_n(rst_n), .en(en), .up(up), .load(load),
                                      .load_value(load_value), .count(count));
endmodule
"""


def test_rtl_engineers_write_only_their_assigned_modules(platform):
    tampered_core = CORE.replace("// REQ-004 hold", "// REQ-004 hold (rewritten by Ada-I)")
    replies = [REPORT, files(("spec/spec.yaml", SPEC), ("spec/spec.md", "# s")), NO_FINDINGS,
               files(("arch/arch.yaml", ARCH2)), REPORT, NO_FINDINGS,
               files(("rtl/counter_core.v", CORE)),                                       # Ada
               files(("rtl/counter8.v", WRAP), ("rtl/counter_core.v", tampered_core)),   # Ada-I oversteps
               REPORT, SAGE]
    run_id, out, provider = run_stages(platform, replies)
    assert out["rtl"].status == "completed"
    evs = events(run_id)
    refused = [e for e in evs if e[0] == "finding" and "refused" in e[2]]
    print(refused[0][2])
    assert refused[0][1] == "Reid" and refused[0][3]["refused"] == ["rtl/counter_core.v"]
    from s2s.agents.runtime import artifact_dir
    assert "rewritten by Ada-I" not in (artifact_dir() / "runs" / run_id / "rtl/counter_core.v").read_text()
    writers = {e[3]["path"]: e[1] for e in evs if e[0] == "artifact.created" and e[3].get("path", "").startswith("rtl/")}
    assert writers == {"rtl/counter_core.v": "Ada", "rtl/counter8.v": "Ada-I"}
    assert "belong(s) to other RTL engineers" in provider.calls[7]["messages"][0]["content"]
    sentinel_report = [e for e in evs if e[0] == "artifact.created" and e[3].get("path") == "reports/sentinel_spec.json"]
    assert sentinel_report[0][1] == "Sentinel"
