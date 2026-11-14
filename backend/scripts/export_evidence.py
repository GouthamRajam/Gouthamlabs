"""Export the M0.7 tape-out packages (GDSII, netlists, reports) of the local run folders into the repo,
so they can be committed and viewed on another machine (snapshots/restore.sh copies them back).

    cd backend && python scripts/export_evidence.py [--artifact-dir DIR] [--out DIR]

For every <artifact-dir>/runs/<run_id>/ that has a tapeout/ folder, copies into
<out>/<design>/<run_id>/ (design = spec/spec.yaml `design`):
  tapeout/ (entire package), signoff/layout3d.json (if present), reports/*.md and reports/*.json,
  arch/arch.yaml (the API reads `top` from it) and spec/spec.yaml.
Then re-hashes every file listed in the copied tapeout/MANIFEST.sha256 and exits non-zero on any
mismatch or missing file. The source run folders are only read. Re-running replaces <design>/<run_id>/.
Defaults: --artifact-dir $S2S_ARTIFACT_DIR or <repo>/var/artifacts; --out $S2S_EVIDENCE_OUT or
<repo>/docs/milestones/m0.7-evidence.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

import yaml  # noqa: E402

from s2s.physical.package import sha256  # noqa: E402


def verify_manifest(pkg: Path) -> list[str]:
    """Problems found re-hashing every file listed in pkg/MANIFEST.sha256 (empty = all match)."""
    man = pkg / "MANIFEST.sha256"
    if not man.is_file():
        return ["MANIFEST.sha256 missing"]
    problems = []
    for line in man.read_text().splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        p = pkg / rel
        if not p.is_file():
            problems.append(f"missing: {rel}")
        elif sha256(p) != digest:
            problems.append(f"sha256 mismatch: {rel}")
    return problems


def export_run(rd: Path, out: Path) -> tuple[str, str, Path]:
    """Copy one run's package and reports to out/<design>/<run_id>/; returns (design, top, dest)."""
    design = yaml.safe_load((rd / "spec" / "spec.yaml").read_text())["design"]
    top = yaml.safe_load((rd / "arch" / "arch.yaml").read_text())["top"]
    dest = out / design / rd.name
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(rd / "tapeout", dest / "tapeout")
    for rel in ("spec/spec.yaml", "arch/arch.yaml", "signoff/layout3d.json"):
        if (rd / rel).is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(rd / rel, dest / rel)
    if (rd / "reports").is_dir():
        for f in sorted((rd / "reports").iterdir()):
            if f.is_file() and f.suffix in (".md", ".json"):
                (dest / "reports").mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest / "reports" / f.name)
    return design, top, dest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--artifact-dir", type=Path,
                    default=Path(os.environ.get("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))))
    ap.add_argument("--out", type=Path,
                    default=Path(os.environ.get("S2S_EVIDENCE_OUT", str(REPO / "docs" / "milestones" / "m0.7-evidence"))))
    a = ap.parse_args(argv)
    runs = sorted(p.parent for p in (a.artifact_dir / "runs").glob("*/tapeout") if p.is_dir())
    if not runs:
        print(f"no tape-out packages found under {a.artifact_dir / 'runs'} (nothing exported)")
        return 0
    rows, bad = [], 0
    for rd in runs:
        design, top, dest = export_run(rd, a.out)
        problems = verify_manifest(dest / "tapeout")
        for p in problems:
            print(f"[FAIL] {design} {rd.name}: {p}")
        bad += bool(problems)
        listed = sum(1 for ln in (dest / "tapeout" / "MANIFEST.sha256").read_text().splitlines() if ln.strip()) \
            if (dest / "tapeout" / "MANIFEST.sha256").is_file() else 0
        gds = dest / "tapeout" / "gds" / f"{top}.gds"
        rows.append((design, rd.name, top, f"{gds.stat().st_size}" if gds.is_file() else "missing",
                     str(listed), "yes" if (dest / "signoff" / "layout3d.json").is_file() else "no",
                     "OK" if not problems else f"FAIL ({len(problems)})"))
    head = ("design", "run_id", "top", "gds bytes", "manifest files", "layout3d", "manifest check")
    w = [max(len(r[i]) for r in rows + [head]) for i in range(len(head))]
    for r in [head, tuple("-" * n for n in w)] + rows:
        print("  ".join(c.ljust(n) for c, n in zip(r, w)).rstrip())
    print(f"\nexported {len(rows)} package(s) to {a.out}; manifest mismatches in {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
