"""N-version check of reference models (MASTER_SPEC 6.7.5 #5, Part 17; A3.7 Mira).

Two Mira instances write reference models independently, from the spec and Vera's test plan only.
Both are run, inside s2s-eda with networking off (the models are model-written code), on the
same seeded random transaction sequence built from the test plan's transaction schema, and their
outputs are compared step by step. Differences go to Vera for review (never silently resolved).

Model contract (tb/ref_model.py):  class RefModel: reset(); step(txn: dict) -> dict of outputs.
"""
from __future__ import annotations

import json
from pathlib import Path

from s2s.tools import runner

_RUN = r'''
import importlib.util, json, random, sys, traceback
from pathlib import Path
a = json.loads(Path(sys.argv[1]).read_text())
def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem + str(abs(hash(path))), path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.RefModel()
out = {"steps": 0, "mismatches": [], "errors": []}
try:
    A, B = load(a["a"]), load(a["b"])
except Exception:
    out["errors"].append("load: " + traceback.format_exc()[-800:]); print("S2S_NVERSION " + json.dumps(out)); sys.exit(0)
rnd = random.Random(a["seed"])
fields, outputs = a["fields"], a["outputs"]
A.reset(); B.reset()
for i in range(a["n"]):
    if a["reset_every"] and i and i % a["reset_every"] == 0:
        A.reset(); B.reset()
    txn = {k: rnd.getrandbits(w) if w > 1 else rnd.randint(0, 1) for k, w in fields.items()}
    try:
        ra, rb = A.step(dict(txn)), B.step(dict(txn))
    except Exception:
        out["errors"].append(f"step {i} {txn}: " + traceback.format_exc()[-800:]); break
    ra = {k: ra.get(k) for k in outputs}; rb = {k: rb.get(k) for k in outputs}
    out["steps"] += 1
    if ra != rb and len(out["mismatches"]) < 10:
        out["mismatches"].append({"step": i, "txn": txn, "model_a": ra, "model_b": rb})
    elif ra != rb:
        out.setdefault("more", 0); out["more"] += 1
print("S2S_NVERSION " + json.dumps(out, default=str))
'''


def run_nversion(workdir: Path, model_a: Path, model_b: Path, transaction: dict, n: int = 2000,
                 seed: int = 1) -> dict:
    d = workdir / "nversion"
    d.mkdir(exist_ok=True)
    args = {"a": str(model_a.resolve()), "b": str(model_b.resolve()), "seed": seed, "n": n,
            "fields": {k: int(v) for k, v in transaction["fields"].items()},
            "outputs": list(transaction["outputs"]), "reset_every": int(transaction.get("reset_every") or 0)}
    (d / "args.json").write_text(json.dumps(args))
    (d / "run.py").write_text(_RUN)
    rec = runner.run(["/opt/cocotb/bin/python3", str(d / "run.py"), str(d / "args.json")], workdir,
                     workdir / "logs" / "nversion.log", "cocotb", 600)
    text = Path(rec.log_path).read_text()
    line = next((ln for ln in text.splitlines() if ln.startswith("S2S_NVERSION ")), None)
    if line is None or rec.exit_code != 0:
        return {"steps": 0, "mismatches": [], "errors": [f"harness did not finish (exit {rec.exit_code}): {text[-600:]}"]}
    res = json.loads(line[len("S2S_NVERSION "):])
    res["total_mismatches"] = len(res["mismatches"]) + res.get("more", 0)
    return res
