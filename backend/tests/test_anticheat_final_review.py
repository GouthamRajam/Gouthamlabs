"""Final anti-cheat step: an unreviewed guard flag goes to Sentinel (baseline vs final); approval clears it, a
blocking finding keeps anti_cheat_final failing (uart 2026-10-06: approval record lost with an interrupted step)."""
from types import SimpleNamespace

import pytest

from s2s.agents import m06

BASE = "for _ in range(P + 16):\n    await env.cycle()\n"
FINAL = "await env.tx_frame_sparse(0x01, 0, div, nbits=1)\n"


@pytest.mark.parametrize("severity,expect_ok", [("info", True), ("blocking", False)])
def test_unreviewed_flag_goes_to_sentinel(tmp_path, monkeypatch, severity, expect_ok):
    (tmp_path / "guard_baseline/tb").mkdir(parents=True)
    (tmp_path / "guard_baseline/tb/test_x.py").write_text(BASE)
    (tmp_path / "spec").mkdir(); (tmp_path / "spec/spec.yaml").write_text("design: x\n")
    monkeypatch.setattr(m06, "_snapshot", lambda c: {"tb/test_x.py": FINAL})
    monkeypatch.setattr(m06.guard, "diff_files", lambda b, a: ["tb/test_x.py: test 't' runs fewer iterations"])
    asked, recorded, checks = {}, {}, []

    def fake_ask(c, who, **kw):
        asked.update(who=who, inputs=kw["inputs"])
        return {"findings": [{"severity": severity, "what": "w"}]}
    monkeypatch.setattr(m06.llm, "ask", fake_ask)
    monkeypatch.setattr(m06, "_record", lambda c, name, probs, *a: recorded.update({name: probs}))
    ctx = SimpleNamespace(workdir=tmp_path, state={}, check=lambda *a, **k: checks.append(a))
    anticheat = next(s for s in m06.verification_steps() if s.__name__ == "anticheat")
    anticheat(ctx)
    assert asked["who"] == "Sentinel"
    assert asked["inputs"]["reports/guard_before_test_x.py.txt"] == BASE and asked["inputs"]["tb/test_x.py"] == FINAL
    assert (recorded["anti_cheat_final"] == []) is expect_ok
    assert checks and checks[0][0] == "anti_cheat_guard" and checks[0][2] is expect_ok
