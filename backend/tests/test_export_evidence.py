"""scripts/export_evidence.py, offline: a fake run folder with a tape-out package is exported, its manifest
re-checked, and a corrupted file makes the script exit non-zero. The source run folder is never modified."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from s2s.physical.package import write_manifest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_evidence.py"
RUN = "run_01TESTEXPORT0000000000000"


def fake_run(art: Path) -> Path:
    rd = art / "runs" / RUN
    files = {
        "spec/spec.yaml": "design: counter8\n",
        "arch/arch.yaml": "top: counter8_top\n",
        "tapeout/gds/counter8_top.gds": "GDSII bytes",
        "tapeout/netlist/counter8_top.nl.v": "module counter8_top(); endmodule\n",
        "tapeout/reports/sta.json": "{}\n",
        "tapeout/reproduce.sh": "#!/usr/bin/env bash\n",
        "signoff/layout3d.json": "{\"layers\": []}\n",
        "reports/tapeout_readiness.md": "# ready\n",
        "reports/dfm_scorecard.json": "{}\n",
        "reports/run.log": "not exported\n",
        "pnr/big.odb": "not exported\n",
    }
    for rel, text in files.items():
        (rd / rel).parent.mkdir(parents=True, exist_ok=True)
        (rd / rel).write_text(text)
    write_manifest(rd / "tapeout")
    # a run without a package is skipped
    (art / "runs" / "run_01TESTNOPKG00000000000000" / "spec").mkdir(parents=True)
    return rd


def run(art: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--artifact-dir", str(art), "--out", str(out)],
                          capture_output=True, text=True)


def snapshot(d: Path) -> dict[str, bytes]:
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def test_export_copies_and_verifies(tmp_path):
    art, out = tmp_path / "artifacts", tmp_path / "docs"
    rd = fake_run(art)
    before = snapshot(rd)
    r = run(art, out)
    assert r.returncode == 0, r.stdout + r.stderr
    dest = out / "counter8" / RUN
    for rel in ("tapeout/gds/counter8_top.gds", "tapeout/netlist/counter8_top.nl.v", "tapeout/reports/sta.json",
                "tapeout/reproduce.sh", "tapeout/MANIFEST.sha256", "signoff/layout3d.json", "spec/spec.yaml",
                "arch/arch.yaml", "reports/tapeout_readiness.md", "reports/dfm_scorecard.json"):
        assert (dest / rel).read_bytes() == (rd / rel).read_bytes(), rel
    assert not (dest / "reports/run.log").exists() and not (dest / "pnr").exists()
    assert not (out / "run_01TESTNOPKG00000000000000").exists()
    assert "counter8" in r.stdout and RUN in r.stdout and "OK" in r.stdout
    assert snapshot(rd) == before  # source untouched

    # idempotent: a stale file in the destination is removed by the re-run
    (dest / "stale.txt").write_text("x")
    assert run(art, out).returncode == 0
    assert not (dest / "stale.txt").exists()

    # a corrupted file in the package fails the manifest check
    (rd / "tapeout/gds/counter8_top.gds").write_text("tampered")
    r = run(art, out)
    assert r.returncode != 0
    assert "sha256 mismatch: gds/counter8_top.gds" in r.stdout


def test_no_packages(tmp_path):
    (tmp_path / "artifacts" / "runs").mkdir(parents=True)
    r = run(tmp_path / "artifacts", tmp_path / "docs")
    assert r.returncode == 0
    assert "no tape-out packages found" in r.stdout
    assert not (tmp_path / "docs").exists()
