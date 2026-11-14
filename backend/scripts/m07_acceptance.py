"""M0.7 acceptance tests (MASTER_SPEC 13.2), re-executed independently of the runs' own records.

    cd backend && python scripts/m07_acceptance.py <m07_run_id> [<m07_run_id> ...] [--dfm-seeded]

Per design, from the run's tape-out package copied into a fresh folder (nothing read from the run's
check records except the clock period from spec.yaml):
  1. GDSII exists; Magic DRC 0 and KLayout DRC 0 (re-run on the packaged GDS); LVS match (re-run:
     Magic extraction from the GDS + Netgen vs the powered netlist); antenna 0 (re-run on the final
     ODB); setup and hold >= 0 at all 9 PDK corners at the spec clock (re-run OpenSTA; the SDC's
     clock period is compared with spec.yaml).
  3. The run's DFM report lists density per layer and near-limit metrics.
  4. reproduce.sh, run again in a fresh container with only the package mounted, passes (it re-runs
     DRC, LVS and STA on the packaged files and the whole OpenLane flow from the packaged RTL).
Once (--dfm-seeded):
  3b. Seeded DFM issues in a generated test layout are all detected (tests/test_m07_dfm_seeded.py).
Acceptance 2 (tight clock, Orion/Chronos WNS improvement) is not part of this script.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
os.environ.setdefault("S2S_SECRETS_DIR", str(REPO / "var" / "secrets"))
os.environ.setdefault("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))
sys.path.insert(0, str(BACKEND))

import yaml  # noqa: E402

from s2s.agents.runtime import artifact_dir  # noqa: E402
from s2s.physical import flow as olf, signoff as so  # noqa: E402
from s2s.tools import runner  # noqa: E402
from s2s.tools.klayout_drc import run_klayout_drc  # noqa: E402
from s2s.tools.magic_drc import run_magic_drc  # noqa: E402

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def per_design(run_id: str) -> None:
    root = artifact_dir() / "runs" / run_id
    spec = yaml.safe_load((root / "spec/spec.yaml").read_text())
    name = spec["design"]
    top = yaml.safe_load((root / "arch/arch.yaml").read_text())["top"]
    print(f"\n=== {name} ({run_id}) ===", flush=True)
    w = artifact_dir() / "acceptance_m07" / run_id
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(root / "tapeout", w / "pkg")
    pkg = w / "pkg"
    gds = pkg / "gds" / f"{top}.gds"
    record(f"{name}: 1 GDSII exists", gds.exists() and gds.stat().st_size > 0, f"{gds.name}, {gds.stat().st_size} bytes")

    mg = run_magic_drc(gds, top, w)
    record(f"{name}: 1 Magic DRC = 0", mg.passed and mg.metrics.get("drc_violations") == 0,
           f"{mg.metrics.get('drc_violations')} violation(s) (magic {mg.tool_version})")
    kl = run_klayout_drc(gds, top, w)
    record(f"{name}: 1 KLayout DRC = 0", kl.passed and kl.metrics.get("drc_violations") == 0,
           f"{kl.metrics.get('drc_violations')} violation(s) (klayout {kl.tool_version}, sky130A_mr.drc)")
    lv = so.lvs(gds, pkg / "netlist" / f"{top}.pnl.v", top, w)
    record(f"{name}: 1 LVS clean", lv.passed and lv.metrics.get("lvs_status") == "match",
           f"{lv.metrics.get('verdict')}; devices {lv.metrics.get('counts', {}).get('devices')}")
    odb = root / "pnr" / "runs" / json.loads((root / "pnr/s2s_physical.json").read_text())["tag"] / "final" / "odb" / f"{top}.odb"
    shutil.copy(odb, w / odb.name)
    _, ant = so.antenna(w / odb.name, w)
    record(f"{name}: 1 antenna violations = 0", ant["net_violations"] == 0 and ant["pin_violations"] == 0,
           f"{ant['net_violations']} net / {ant['pin_violations']} pin violation(s); worst net at "
           f"{ant['worst'][0]['pct_of_limit'] if ant['worst'] else None}% of its limit")
    want = round(1000.0 / float(spec["clocks"][0]["freq_mhz"]), 6)
    sdc_probs, found = olf.sdc_problems((pkg / "constraints/constraints.sdc").read_text(), clocks=spec["clocks"],
                                        inputs=olf.port_bits(spec)[1], outputs=olf.port_bits(spec)[2])
    record(f"{name}: 1 SDC clock = spec target", not [p for p in sdc_probs if "period" in p or "create_clock" in p],
           f"SDC {found['clocks']} ns vs spec {want} ns ({spec['clocks'][0]['freq_mhz']} MHz)")
    sta = so.sta_corners(pkg / "netlist" / f"{top}.nl.v", pkg / "constraints/constraints.sdc", top, w,
                         {rc: pkg / "spef" / rc / f"{top}.{rc}.spef" for rc in so.RC_CORNERS})
    ws = {c: (r.metrics["setup_worst_slack"], r.metrics["hold_worst_slack"]) for c, r in sta.items()}
    ok = len(sta) == 9 and all(r.passed for r in sta.values())
    record(f"{name}: 1 setup/hold met at all 9 corners", ok,
           f"worst setup {min(v[0] for v in ws.values())} ns, worst hold {min(v[1] for v in ws.values())} ns "
           f"over {len(ws)} corners")

    card = root / "reports" / "dfm_tool.json"
    d = json.loads(card.read_text()) if card.exists() else {}
    layers = d.get("layers", {})
    ok = bool(layers) and all("density_global" in L and "density_window_max" in L for L in layers.values()) and \
        any("near_limit_edge_fraction" in L for L in layers.values())
    record(f"{name}: 3 DFM report: density per layer + near-limit metrics", ok,
           ", ".join(f"{n} {L.get('density_global')}/{L.get('max_density')}" for n, L in layers.items())
           + f"; items {d.get('summary')}")

    clean = w / "repro"
    shutil.copytree(pkg, clean / "pkg")
    rec = runner.run(["bash", "reproduce.sh"], clean / "pkg", clean / "reproduce.log", "openlane", 7200)
    line = next((ln for ln in Path(rec.log_path).read_text().splitlines() if ln.startswith("S2S_REPRODUCE_RESULT ")), None)
    res = json.loads(line.split(" ", 1)[1]) if line else {"passed": False, "items": "no result"}
    record(f"{name}: 4 reproduce.sh in a fresh container", rec.exit_code == 0 and res.get("passed") is True,
           f"{res.get('items')} ({rec.duration_s:.0f} s)")


def dfm_seeded() -> None:
    print("\n=== seeded DFM issues ===", flush=True)
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_m07_dfm_seeded.py"], cwd=BACKEND,
                       capture_output=True, text=True)
    record("3b seeded DFM issues detected", p.returncode == 0, p.stdout.strip().splitlines()[-1] if p.stdout else p.stderr[-300:])


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for r in args:
        per_design(r)
    if "--dfm-seeded" in sys.argv:
        dfm_seeded()
    passed = sum(ok for _, ok, _ in results)
    print(f"\n{passed}/{len(results)} acceptance checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
