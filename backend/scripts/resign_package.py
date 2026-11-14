"""Re-run ONLY the gdsii `sign` step (Proof) of a finished run: copy the run's current reports into the
tape-out package, rewrite MANIFEST.sha256, re-hash every file and record the manifest_signed check.
No EDA tool runs and no other step runs (decision 2026-10-06: re-sign after the readiness re-score).

Every GDS in the run (package copy, OpenLane's final and stream-outs) is hashed before and after; if any byte changed,
the script fails. Prints the GDS hashes and the package files whose manifest hash changed.
With --evidence <dir>, copies the changed package files and the run-level readiness/proof reports there
(the committed evidence copy under docs/milestones).

Usage: S2S_ARTIFACT_DIR=<...>/var/artifacts python -m scripts.resign_package <run_id> [--evidence <dir>]
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from sqlalchemy import select

from s2s.agents import m07
from s2s.agents.runtime import StepContext, artifact_dir
from s2s.db.models import Task
from s2s.db.session import session


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gds_hashes(run: Path) -> dict[str, str]:
    files = sorted(run.rglob("*.gds"))  # every layout in the run: package, OpenLane final, stream-outs
    return {str(p.relative_to(run)): _sha(p) for p in files}


def _manifest(run: Path) -> dict[str, str]:
    lines = (run / "tapeout/MANIFEST.sha256").read_text().splitlines()
    return {rel: h for h, rel in (ln.split("  ", 1) for ln in lines)}


def resign(run_id: str, evidence: Path | None = None) -> dict:
    assert os.environ.get("S2S_ARTIFACT_DIR"), "set S2S_ARTIFACT_DIR (the orchestrator's artifact store)"
    run = artifact_dir() / "runs" / run_id
    gds_before, man_before = gds_hashes(run), _manifest(run)
    assert gds_before, f"no GDS found under {run}"
    steps = m07.gdsii_steps()
    idx = next(i for i, f in enumerate(steps) if f.__name__ == "sign")
    with session() as s:
        task = s.scalars(select(Task).where(Task.run_id == run_id, Task.stage == "gdsii")).one()
        assert task.status == "completed", f"gdsii task {task.id} is {task.status}"
        ctx = StepContext(session=s, task=task, state={}, gateway=None, step_index=idx, step_count=len(steps))
        ctx.emit("plan", "Proof: re-sign the tape-out package after the 2026-10-06 readiness re-score - sign step "
                 "only (reports copied in, manifest rewritten and re-hashed); no EDA tool runs", agent_id="Proof")
        steps[idx](ctx)
        signed = json.loads((run / "reports/proof_manifest.json").read_text())
    gds_after, man_after = gds_hashes(run), _manifest(run)
    assert gds_after == gds_before, f"GDS changed: {gds_before} -> {gds_after}"
    changed = sorted(k for k in man_after if man_before.get(k) != man_after[k])
    changed += sorted(f"{k} (removed)" for k in man_before if k not in man_after)
    if evidence:
        for rel in [*(k for k in changed if not k.endswith("(removed)")), "MANIFEST.sha256"]:
            shutil.copy2(run / "tapeout" / rel, evidence / "tapeout" / rel)
        for rel in ("reports/proof_manifest.json", "reports/tapeout_readiness.json", "reports/tapeout_readiness.md"):
            shutil.copy2(run / rel, evidence / rel)
    return {"run": run_id, "gds_sha256_before": gds_before, "gds_sha256_after": gds_after,
            "gds_identical": gds_after == gds_before, "manifest_changed_files": changed,
            "manifest_sha256": signed["manifest_sha256"], "files": signed["files"], "mismatches": signed["mismatches"]}


if __name__ == "__main__":
    ev = Path(sys.argv[sys.argv.index("--evidence") + 1]) if "--evidence" in sys.argv else None
    print(json.dumps(resign(sys.argv[1], ev), indent=1))
