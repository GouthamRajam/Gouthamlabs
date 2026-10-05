"""D2 prove-then-exclude in Myra's screen: a mutant leaves the measurement only with an unbounded proof; undecided
or different mutants are kept and counted. dprove verdicts are read from ABC's own line (real logs, uart 2026-10-05)."""
import json
from pathlib import Path
from types import SimpleNamespace

from s2s.verify import mutation_run
from tests.test_mutation_timeouts import RTL, _res

G = Path(__file__).parent / "golden" / "mutation_equiv"


def test_dprove_verdicts_from_real_logs():
    assert mutation_run.classify_dprove((G / "dprove_equivalent.log").read_text()) == "equivalent"
    assert mutation_run.classify_dprove((G / "dprove_undecided.log").read_text()) == "undecided"
    assert mutation_run.classify_dprove("PDR stats: Cex = 0") == "undecided"  # a stats line is not a verdict
    assert mutation_run.classify_dprove("") == "undecided"


def test_only_proven_equivalent_mutants_are_screened_out(tmp_path, monkeypatch):
    verdict = {}  # mutant id -> what the unbounded proof says

    def fake_run(cmd, workdir, log_path, key, timeout, **kw):
        if cmd[0].endswith("python3"):  # Myra's bounded screen: undecided for everything
            args = json.loads(Path(cmd[-1]).read_text())
            out = [{"id": m["id"], "compiles": True, "equiv": "unknown"} for m in args["mutants"]]
            Path(log_path).write_text("S2S_SCREEN " + json.dumps(out) + "\n")
        elif cmd[0] == "sby":  # builds the miter model; PDR does not finish
            # the real runner mounts only `workdir` in the tool container: every file sby reads must be inside it
            files = (Path(workdir) / cmd[-1]).read_text().split("[files]\n")[1].split()
            srcs = [Path(f) for f in files[1::2]]
            assert srcs and all(p.is_file() and Path(workdir) in p.parents for p in srcs), srcs
            mid = Path(workdir).parent.name
            v = verdict.setdefault(mid, ["equivalent", "undecided"][len(verdict) % 2])
            (Path(workdir) / "eq" / "model").mkdir(parents=True, exist_ok=True)
            (Path(workdir) / "eq" / "model" / "design_aiger.aig").write_text("aig")
            Path(log_path).write_text("SBY [eq] engine_0: running\n")
        else:  # yosys-abc dprove
            mid = Path(workdir).parent.name
            Path(log_path).write_text((G / f"dprove_{verdict[mid]}.log").read_text())
        return SimpleNamespace(log_path=log_path, timed_out=False, duration_s=1.0)
    monkeypatch.setattr(mutation_run.runner, "run", fake_run)
    monkeypatch.setattr(mutation_run, "run_cocotb_regress",
                        lambda *a, **k: _res() if a[5].startswith("orig") else _res(passed=False, failed=1))
    tb = tmp_path / "tb"; tb.mkdir()
    out = mutation_run.run_mutation(workdir=tmp_path, rtl_files=RTL, top="cnt", tb_dir=tb, test_module="t",
                                    n=2, timeout_s=60, parallel=1, log=lambda *_: None)
    proven = {s["id"] for s in out["screened_out"] if "proven equivalent" in s["reason"]}
    kept = {m["id"] for m in out["mutants"]}
    assert proven and all(verdict[i] == "equivalent" for i in proven)          # excluded only with a proof
    assert all(verdict[i] == "undecided" for i in kept) and len(kept) == 2      # undecided kept and counted
    assert all("ABC dprove" in s["reason"] and "proof log" in s["reason"] for s in out["screened_out"]
               if s["id"] in proven)
