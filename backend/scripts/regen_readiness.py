"""Re-score a finished run's Tape-out Readiness Report under the current config/readiness.yaml, from the
results the run already recorded (no tool is re-run; decision 2026-10-06).

Inputs, per run folder: tapeout/reports/tapeout_readiness.json (each check's recorded result, tool,
evidence), tapeout/reports/tapeout_checklist.json (B.9 items 4-8: the hard checks the run passed) and
reports/pv_signoff.json + reports/sta_signoff.json (details). Writes reports/tapeout_readiness.{json,md}.
The signed package (tapeout/) is left unchanged so its MANIFEST.sha256 signature stays valid; its
readiness copy keeps the M0.7 scoring and is marked superseded in the new report.

Usage: python -m scripts.regen_readiness <run_dir> [<run_dir> ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from s2s.physical import readiness

HARD_ITEMS = {"equivalence": 4, "timing": 5, "drc": 6, "lvs": 7, "antenna": 8}  # B.9 checklist numbers


def regen(run: Path) -> dict:
    pkg = run / "tapeout" / "reports"
    old = json.loads((pkg / "tapeout_readiness.json").read_text())
    design = (pkg / "tapeout_readiness.md").read_text().splitlines()[0].split(": ", 1)[1].strip()
    results = {r["check"]: {k: r[k] for k in ("result", "tool", "evidence", "note") if k in r} for r in old["rows"]}
    items = {i["n"]: i for i in json.loads((pkg / "tapeout_checklist.json").read_text())}
    hard = readiness.hard_checks({k: items[n]["done"] is True for k, n in HARD_ITEMS.items()},
                                 {k: items[n]["evidence"] for k, n in HARD_ITEMS.items()}, run / "reports")
    rep = readiness.score(results, hard)
    rep["regenerated"] = {"by": "backend/scripts/regen_readiness.py", "decision": "docs/DECISIONS.md 2026-10-06",
                          "superseded_copy": "tapeout/reports/tapeout_readiness.* (M0.7 scoring, signed; unchanged)",
                          "tools_rerun": False}
    (run / "reports" / "tapeout_readiness.json").write_text(json.dumps(rep, indent=1) + "\n")
    (run / "reports" / "tapeout_readiness.md").write_text(readiness.markdown(design, rep, {
        "evidence packet": "tapeout/evidence/index.json", "reproduce": "tapeout/reproduce.sh",
        "checklist": "tapeout/reports/tapeout_checklist.md", "manifest": "tapeout/MANIFEST.sha256",
        "superseded M0.7 copy (signed package, partial=0.5 for DFT; left unchanged so the signature stays valid)":
            "tapeout/reports/tapeout_readiness.md",
        "re-scored by (no tool re-run)": "backend/scripts/regen_readiness.py, decision docs/DECISIONS.md 2026-10-06"}))
    return {"design": design, "hard": hard["verdict"], "A": rep["baseline_A_pct"], "B": rep["baseline_B_pct"],
            "conditions": hard["conditions"]}


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(json.dumps(regen(Path(arg))))
