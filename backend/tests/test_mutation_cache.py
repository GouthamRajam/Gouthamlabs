"""Mutant verdicts survive a restart: a re-run reuses verdicts for the same RTL and tests, never timeouts,
and any testbench change invalidates them."""
import json
from pathlib import Path
from types import SimpleNamespace

from s2s.verify import mutation_run
from tests.test_mutation_timeouts import RTL, _res


def _setup(monkeypatch, behaviour):
    def fake_screen(cmd, workdir, log_path, key, timeout):
        args = json.loads(Path(cmd[-1]).read_text())
        out = [{"id": m["id"], "compiles": True, "equiv": "different"} for m in args["mutants"]]
        Path(log_path).write_text("S2S_SCREEN " + json.dumps(out) + "\n")
        return SimpleNamespace(log_path=log_path)
    monkeypatch.setattr(mutation_run.runner, "run", fake_screen)
    calls = []

    def fake_regress(sources, top, mod, tb, base, name, seeds, **kw):
        calls.append(name.split("/")[0])
        mid = name.split("/")[0].removesuffix("_retry")
        return _res() if mid == "orig" else behaviour(mid)
    monkeypatch.setattr(mutation_run, "run_cocotb_regress", fake_regress)
    return calls


def _run(tmp_path, tb):
    return mutation_run.run_mutation(workdir=tmp_path, rtl_files=RTL, top="cnt", tb_dir=tb, test_module="t",
                                     n=3, timeout_s=60, parallel=1, log=lambda *_: None)


def test_rerun_reuses_verdicts_but_not_timeouts(tmp_path, monkeypatch):
    role = {}

    def behaviour(mid):
        k = role.setdefault(mid, len(role))
        return _res(passed=False, timed_out=True) if k == 0 else _res(passed=False, failed=k % 2)
    calls = _setup(monkeypatch, behaviour)
    tb = tmp_path / "tb"; tb.mkdir(); (tb / "test_t.py").write_text("# v1\n")
    first = _run(tmp_path, tb)
    assert first["cached_verdicts"] == 0
    calls.clear()
    second = _run(tmp_path, tb)
    timed_out = next(m for m, k in role.items() if k == 0)
    assert second["cached_verdicts"] == 2
    assert {c for c in calls if c != "orig"} == {timed_out, timed_out + "_retry"}  # only the timeout re-ran
    assert [(m["id"], m["detected"]) for m in second["mutants"]] == [(m["id"], m["detected"]) for m in first["mutants"]]


def test_changed_tests_invalidate_cache(tmp_path, monkeypatch):
    calls = _setup(monkeypatch, lambda mid: _res(passed=False, failed=1))
    tb = tmp_path / "tb"; tb.mkdir(); (tb / "test_t.py").write_text("# v1\n")
    _run(tmp_path, tb)
    (tb / "test_t.py").write_text("# v2: a new test\n")
    calls.clear()
    out = _run(tmp_path, tb)
    assert out["cached_verdicts"] == 0 and len([c for c in calls if c != "orig"]) == 3
