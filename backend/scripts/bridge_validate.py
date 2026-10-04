"""Check a Claude Code bridge answer before S2S reads it (personal dev mode, S2S_MODEL_PROVIDER=bridge).

    python scripts/bridge_validate.py <request.json> <answer.json>

Prints OK, or the exact schema problems. Exit 0 only when valid."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s2s.models.gateway import bridge_problem  # noqa: E402

req = json.loads(Path(sys.argv[1]).read_text())
problem = bridge_problem(Path(sys.argv[2]).read_text(), req.get("output_schema"))
print("OK" if not problem else f"INVALID: {problem}")
sys.exit(0 if not problem else 1)
