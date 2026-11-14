"""Re-run ONLY the gdsii documentation steps of a finished run - `release_notes` (Gideon, writes
tapeout/release_notes.md) and `sloane` (Sloane, writes reports/division4_report.md) - then the `sign` step
(scripts/resign_package.py). No EDA tool runs. Model calls go through the coding-agent bridge (personal
localhost mode; no API key is read). Every .gds in the run is hashed before and after; any change fails.

Usage: S2S_ARTIFACT_DIR=<...>/var/artifacts python -m scripts.rerun_gdsii_docs <run_id> [--evidence <dir>]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from sqlalchemy import select

from s2s.agents import m07
from s2s.agents.runtime import StepContext, artifact_dir
from s2s.db.models import Task
from s2s.db.session import session
from s2s.models.gateway import BridgeProvider, ModelGateway
from scripts.resign_package import gds_hashes, resign

DOC_STEPS = ("release_notes", "sloane")


def rerun(run_id: str, evidence: Path | None = None) -> dict:
    run = artifact_dir() / "runs" / run_id
    before = gds_hashes(run)
    steps = m07.gdsii_steps()
    gw = ModelGateway(BridgeProvider())
    for name in DOC_STEPS:
        idx = next(i for i, f in enumerate(steps) if f.__name__ == name)
        with session() as s:
            task = s.scalars(select(Task).where(Task.run_id == run_id, Task.stage == "gdsii")).one()
            assert task.status == "completed", f"gdsii task {task.id} is {task.status}"
            ctx = StepContext(session=s, task=task, state={}, gateway=gw, step_index=idx, step_count=len(steps))
            if name == DOC_STEPS[0]:
                ctx.emit("plan", "Gideon/Sloane: re-write the release notes and the Division 4 report from the "
                         "re-scored readiness report (decision 2026-10-06), then Proof re-signs; no EDA tool runs",
                         agent_id="Gideon")
            steps[idx](ctx)
    signed = resign(run_id, evidence)
    if evidence:
        shutil.copy2(run / "reports/division4_report.md", evidence / "reports/division4_report.md")
    after = gds_hashes(run)
    assert after == before, f"GDS changed: {before} -> {after}"
    return {**signed, "gds_sha256_before_docs": before, "gds_sha256_after_all": after, "gds_identical_all": True}


if __name__ == "__main__":
    ev = Path(sys.argv[sys.argv.index("--evidence") + 1]) if "--evidence" in sys.argv else None
    print(json.dumps(rerun(sys.argv[1], ev), indent=1))
