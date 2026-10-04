"""M0.5 acceptance tests (MASTER_SPEC 13.2), re-checked independently of the run's own records.

    cd backend && python scripts/m05_acceptance.py <run_id>

  1. spec.yaml and arch.yaml from the run folder pass schema and consistency checks (re-run here).
  2. The RTL passes Verilator lint (-Wall) and Yosys elaboration with zero errors: both tools are
     run again here, in a fresh folder, on the run's RTL files.
  3. Sentinel produces at least one finding on a seeded flawed spec (counter8 spec with no reset
     behavior). A REAL model call, metered under its own design "counter8_seeded_flaw".
  4. All agent actions appear in the Live Office: every event of the run is in the API's /events
     (what the Live Office loads) and in the Redis live stream (what /ws/events pushes), and every
     acting agent has a seat in /org.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
os.environ.setdefault("S2S_SECRETS_DIR", str(REPO / "var" / "secrets"))
os.environ.setdefault("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))
sys.path.insert(0, str(BACKEND))

import httpx  # noqa: E402
import yaml  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from s2s.agents import llm  # noqa: E402
from s2s.agents.runtime import Agent, StepContext, artifact_dir, run_task  # noqa: E402
from s2s.config import settings  # noqa: E402
from s2s.db.models import Design, Event, Project, Task, UsageRecord  # noqa: E402
from s2s.db.session import session  # noqa: E402
from s2s.design import checks  # noqa: E402
from s2s.design.schemas import REVIEW_ANSWER  # noqa: E402
from s2s.events.bus import redis_client  # noqa: E402
from s2s.ids import new_id  # noqa: E402
from s2s.models.gateway import ModelGateway  # noqa: E402
from s2s.orchestrator.engine import create_run  # noqa: E402
from s2s.tools.verilator_lint import run_verilator_lint  # noqa: E402
from s2s.tools.yosys_elab import run_yosys_elab  # noqa: E402

API = os.environ.get("S2S_API", "http://127.0.0.1:8000")
results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def test_1(root: Path) -> None:
    spec = yaml.safe_load((root / "spec/spec.yaml").read_text())
    arch = yaml.safe_load((root / "arch/arch.yaml").read_text())
    probs = {"spec schema (B.1)": checks.spec_schema(spec), "spec consistency": checks.spec_consistency(spec),
             "arch schema (B.2)": checks.arch_schema(arch), "arch consistency": checks.arch_consistency(arch, spec)}
    for k, v in probs.items():
        record(f"1. {k}", not v, "0 problems" if not v else "; ".join(v[:5]))
    print(f"   spec: {len(spec['requirements'])} requirements, {len(spec['interfaces'])} interfaces, "
          f"target {spec['target_clock_mhz']} MHz; arch: top {arch['top']}, modules "
          f"{[m['name'] + '(' + m['kind'] + ')' for m in arch['modules']]}")


def test_2(root: Path) -> None:
    arch = yaml.safe_load((root / "arch/arch.yaml").read_text())
    fresh = artifact_dir() / "acceptance" / root.name
    shutil.rmtree(fresh, ignore_errors=True)
    (fresh / "rtl").mkdir(parents=True)
    for f in sorted((root / "rtl").glob("*.v")):
        shutil.copy(f, fresh / "rtl" / f.name)
    files = sorted((fresh / "rtl").glob("*.v"))
    for name, fn in (("verilator_lint", run_verilator_lint), ("yosys_elab", run_yosys_elab)):
        r = fn(files, arch["top"], fresh)
        print(f"   $ {' '.join(r.command)}\n   tool {r.tool} {r.tool_version}  exit {r.exit_code}  "
              f"errors {r.error_count}  warnings {r.warning_count}  status {r.status}")
        print("   log tail: " + " | ".join(Path(r.log_path).read_text().strip().splitlines()[-3:]))
        record(f"2. {name} (re-run)", r.passed and r.error_count == 0, f"{r.error_count} errors, {r.warning_count} warnings")


class SeededSpecReview(Agent):
    """Write the seeded flawed spec, then ONE Sentinel review (no revision loop)."""
    def steps(self, task: Task):
        def seed(ctx: StepContext) -> None:
            ctx.workdir.mkdir(parents=True, exist_ok=True)
            flawed = (BACKEND / "tests/platform/m05_fixtures/counter8_spec.yaml").read_text()
            flawed = flawed.replace("Hand-written test fixture", "SEEDED FLAW (missing reset behavior). Hand-written fixture")
            flawed = flawed.replace(", reset_value: 0}", "}")
            flawed = "\n".join(ln for ln in flawed.splitlines() if "REQ-001, type: reset" not in ln) + "\n"
            (ctx.workdir / "spec").mkdir(exist_ok=True)
            (ctx.workdir / "spec/spec.yaml").write_text(flawed)
            (ctx.workdir / "request.md").write_text((REPO / "designs/counter8/request.md").read_text())
            ctx.artifact("spec", "spec/spec.yaml", flawed.encode(), agent_id="Iris")

        def review(ctx: StepContext) -> None:
            data = llm.ask(ctx, "Sentinel", goal="Independently review the spec for counter8. File findings only "
                           "for real, specific problems; say why each matters.",
                           inputs={p: (ctx.workdir / p).read_text() for p in ("request.md", "spec/spec.yaml")},
                           exit_criteria=["every finding is specific: artifact, location, evidence, suggested action"],
                           schema=REVIEW_ANSWER, extra_note="Put each finding in `findings` (an empty list if none). ")
            for f in data["findings"]:
                ctx.emit("finding", f"Sentinel [{f['severity']}] {f['target']}: {f['what'][:200]}",
                         agent_id="Sentinel", team=llm.agent("Sentinel").team, to_agent_id="Iris", detail=f)
            ctx.state["findings"] = data["findings"]
            ctx.task.outputs = {"findings": data["findings"]}
        return [seed, review]


def test_3() -> None:
    with session() as s:
        prj = Project(id=new_id("prj"), name="M0.5 acceptance")
        s.add(prj)
        s.flush()
        d = Design(id=new_id("des"), project_id=prj.id, name="counter8_seeded_flaw",
                   request_text="Seeded flawed spec for Sentinel (M0.5 acceptance test 3)")
        s.add(d)
        s.flush()
        run = create_run(s, d, to_stage="spec", agent_kind="s2s")
        t = s.scalar(select(Task).where(Task.run_id == run.id))
        t.status, t.title = "running", "Sentinel review of a seeded flawed spec"
        tid, run_id = t.id, run.id
    out = run_task(tid, SeededSpecReview(), ModelGateway.from_settings())
    with session() as s:
        t = s.get(Task, tid)
        findings = (t.outputs or {}).get("findings", [])
        cost = s.scalar(select(func.coalesce(func.sum(UsageRecord.cost_usd), 0)).where(UsageRecord.run_id == run_id))
    print(f"   seeded run {run_id}: task {out.status}; {len(findings)} finding(s); cost ${float(cost):.4f}")
    for f in findings:
        print(f"   - [{f['severity']}] {f['target']}: {f['what'][:240]}")
    about_reset = [f for f in findings if "reset" in (f["what"] + f["target"] + f["evidence"]).lower()]
    record("3. Sentinel finds the seeded flaw", out.status == "completed" and len(findings) >= 1 and bool(about_reset),
           f"{len(findings)} finding(s), {len(about_reset)} about reset behavior")


def test_4(run_id: str) -> None:
    with session() as s:
        db_events = s.scalars(select(Event).where(Event.run_id == run_id)).all()
    ids = {e.id for e in db_events}
    api: list[dict] = []
    before = None
    while True:
        page = httpx.get(f"{API}/events", params={"run_id": run_id, "limit": 500, **({"before": before} if before else {})},
                         timeout=30).json()
        api += page
        if len(page) < 500:
            break
        before = page[-1]["id"]
    stream = redis_client().xrange(settings().event_stream)
    live = {json.loads(x[1]["event"])["id"] for x in stream if json.loads(x[1]["event"]).get("run_id") == run_id}
    org = httpx.get(f"{API}/org", timeout=30).json()
    seats: set[str] = set()

    def walk(u: dict) -> None:
        if u.get("manager_agent_id"):
            seats.add(u["manager_agent_id"])
        for c in u.get("children", []):
            walk(c)
    for dv in org["divisions"]:
        walk(dv)
    actors = {e.agent_id for e in db_events if e.agent_id}
    by_type: dict[str, int] = {}
    for e in db_events:
        by_type[e.type] = by_type.get(e.type, 0) + 1
    print(f"   {len(db_events)} events in the database; {len(api)} via API /events; {len(live)} in the live stream")
    print(f"   by type: {dict(sorted(by_type.items()))}")
    print(f"   acting agents: {sorted(actors)}")
    record("4a. every event served by /events (Live Office load/replay)", {e['id'] for e in api} == ids,
           f"{len(api)}/{len(ids)}")
    record("4b. every event pushed on the live stream (/ws/events)", live == ids, f"{len(live)}/{len(ids)}")
    record("4c. every acting agent has a Live Office seat", actors <= seats, f"missing: {sorted(actors - seats)}")
    m05 = {"Juno", "Iris", "Kepler", "Pascal", "Ivy", "Reid", "Ada", "Ada-C", "Ada-I", "Watt", "Lumen", "Sentinel", "Sage"}
    print(f"   M0.5 roster agents that acted in this run: {sorted(actors & m05)}; "
          f"not needed by counter8: {sorted(m05 - actors)}")


def main() -> int:
    run_id = sys.argv[1]
    root = artifact_dir() / "runs" / run_id
    print(f"M0.5 acceptance on {run_id} ({root})\n")
    test_1(root)
    test_2(root)
    test_3()
    test_4(run_id)
    ok = all(r[1] for r in results)
    print(f"\n{sum(r[1] for r in results)}/{len(results)} acceptance checks passed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
