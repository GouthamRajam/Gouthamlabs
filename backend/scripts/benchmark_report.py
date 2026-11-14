"""M0.8 benchmark report: per design pass/fail per stage, iterations, wall time, tokens, cost, PPA vs default flow.

    cd backend && python scripts/benchmark_report.py          # benchmark designs only
    cd backend && python scripts/benchmark_report.py --all    # also *_suite / *_seeded_flaw test designs

Read-only: queries the database and the run reports, writes docs/benchmark/benchmark.md and
docs/benchmark/benchmark.json, and prints the summary table.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
os.environ.setdefault("S2S_SECRETS_DIR", str(REPO / "var" / "secrets"))
os.environ.setdefault("S2S_ARTIFACT_DIR", str(REPO / "var" / "artifacts"))
sys.path.insert(0, str(BACKEND))

from s2s.agents.runtime import artifact_dir  # noqa: E402
from s2s.db.session import session  # noqa: E402
from s2s.reports import benchmark  # noqa: E402


def main() -> int:
    with session() as s:
        report = benchmark.build(s, artifact_dir(), include_all="--all" in sys.argv[1:])
        s.rollback()  # read-only
    out = REPO / "docs" / "benchmark"
    out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    (out / "benchmark.md").write_text(benchmark.markdown(report))
    print(benchmark.summary_markdown(report))
    print(f"\nwrote {out / 'benchmark.md'} and {out / 'benchmark.json'} ({len(report['designs'])} design(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
