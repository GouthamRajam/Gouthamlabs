"""A timed-out mutant simulation is never counted as a caught bug (retried once at 2x, then NOT caught)."""
import json
from pathlib import Path
from types import SimpleNamespace

from s2s.verify import mutation_run

RTL = {"rtl/cnt.v": """module cnt(input clk, input rst_n, input en, output reg [3:0] q);
  always @(posedge clk) begin
    if (!rst_n) q <= 4'd0;
    else if (en) q <= q + 4'd1;
  end
endmodule
"""}


def _res(passed=True, timed_out=False, failed=0):
    return SimpleNamespace(passed=passed, timed_out=timed_out, reasons=[] if passed else ["x"], duration_s=10.0,
                           metrics={"failed_runs": failed, "test_runs": 0 if timed_out else 4,
                                    "tests_by_name": {"t": {"fail": failed}} if failed else {}})


def test_timeouts_are_not_catches(tmp_path, monkeypatch):
    def fake_screen(cmd, workdir, log_path, key, timeout):
        args = json.loads(Path(cmd[-1]).read_text())
        out = [{"id": m["id"], "compiles": True, "equiv": "different"} for m in args["mutants"]]
        Path(log_path).write_text("S2S_SCREEN " + json.dumps(out) + "\n")
        return SimpleNamespace(log_path=log_path)
    monkeypatch.setattr(mutation_run.runner, "run", fake_screen)
    calls, role = [], {}

    def fake_regress(sources, top, mod, tb, base, name, seeds, **kw):
        calls.append((name, kw["timeout_s"]))
        mid = name.split("/")[0]
        if mid == "orig":
            return _res()
        k = role.setdefault(mid.removesuffix("_retry"), len(role))  # behaviour by first-seen order
        if k == 0:
            return _res(passed=False, timed_out=True)          # times out twice
        if k == 1:
            return _res(passed=False, timed_out=not mid.endswith("_retry"))  # times out, then passes
        return _res(passed=False, failed=1)                    # a real failing test
    monkeypatch.setattr(mutation_run, "run_cocotb_regress", fake_regress)
    tb = tmp_path / "tb"; tb.mkdir()
    out = mutation_run.run_mutation(workdir=tmp_path, rtl_files=RTL, top="cnt", tb_dir=tb, test_module="t",
                                    n=3, timeout_s=60, parallel=1, log=lambda *_: None)
    by = {m["id"]: m for m in out["mutants"]}
    first, second, third = (by[i] for i, _ in sorted(role.items(), key=lambda kv: kv[1]))
    assert first["detected"] is False and first["timeouts"] == 2 and "NOT counted" in first["how"]
    assert second["detected"] is False and second["timeouts"] == 1
    assert third["detected"] is True
    assert out["detected"] == 1 and out["timed_out_not_counted"] == 1
    retry_limits = [t for n, t in calls if "_retry" in n]
    assert retry_limits and all(t == 2 * 60 for t in retry_limits)
