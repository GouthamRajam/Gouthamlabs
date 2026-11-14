"""Phase 1 harness #9: processes are stopped by PID (the supervisor's PID files) only. Pattern-based killing
(`pkill -f`, `killall`, `pgrep ... | xargs kill`, `ps ... | awk ... kill`) matched and killed the operator's own shell
on 2026-10-07; it must never enter the code or scripts."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN = ["backend/s2s", "backend/scripts", "eda", "config", "scripts", ".github"]
PATTERN_KILL = re.compile(r"\bpkill\b|\bkillall\b|pgrep[^\n]*\|\s*xargs[^\n]*\bkill\b|\bps\b[^\n]*\|[^\n]*\bkill\b"
                          r"|kill\s+\$\(\s*pgrep")


def _files():
    for d in SCAN:
        root = REPO / d
        if root.exists():
            for f in root.rglob("*"):
                if f.is_file() and f.suffix in {".py", ".sh", ".yaml", ".yml", ".tcl", ".mk", ""} \
                        and "__pycache__" not in f.parts:
                    yield f
    yield from (p for p in REPO.glob("*") if p.is_file() and p.suffix in {".sh", ".yml", ".yaml", ""})


def test_no_pattern_based_process_killing_in_code_or_scripts():
    hits = []
    for f in _files():
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if PATTERN_KILL.search(line):
                hits.append(f"{f.relative_to(REPO)}:{n}: {line.strip()[:120]}")
    assert not hits, "stop processes by PID file (s2s.ops.supervisor), never by pattern:\n" + "\n".join(hits)


def test_the_detector_catches_the_known_forms():
    for bad in ("pkill -f s2s.orchestrator", "killall python", "pgrep -f run_m07 | xargs kill",
                "ps -eo pid,args | awk '/orchestrator/ {print $1}' | xargs -r kill", "kill $(pgrep -f uvicorn)"):
        assert PATTERN_KILL.search(bad), bad
    for ok in ("kill 30562", "os.killpg(rec['pgid'], signal.SIGTERM)", 'subprocess.run(["docker", "kill", container])'):
        assert not PATTERN_KILL.search(ok), ok
