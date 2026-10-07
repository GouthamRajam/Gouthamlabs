"""Flat OCV derate in signoff STA (CEO decision 2026-10-07): the derate reaches OpenSTA on every corner, and no
derate is applied to the nominal run."""
from pathlib import Path
from types import SimpleNamespace

from s2s.physical import signoff
from s2s.tools import opensta


def _capture(monkeypatch):
    scripts = {}

    def fake_run(cmd, workdir, log, key, timeout, **kw):
        scripts[Path(cmd[-1]).name] = Path(cmd[-1]).read_text()
        raise opensta.runner.EdaUnavailable("captured")
    monkeypatch.setattr(opensta.runner, "run", fake_run)
    return scripts


def test_derate_is_written_into_the_sta_script(tmp_path, monkeypatch):
    s = _capture(monkeypatch)
    opensta.run_opensta(tmp_path / "x.v", tmp_path / "x.sdc", "x", tmp_path, derate=(0.9, 1.1), tag="t")
    txt = s["sta_x_t.tcl"]
    assert "set_timing_derate -early 0.9\nset_timing_derate -late 1.1" in txt
    assert txt.index("set_timing_derate") < txt.index("report_checks")


def test_nominal_run_has_no_derate(tmp_path, monkeypatch):
    s = _capture(monkeypatch)
    opensta.run_opensta(tmp_path / "x.v", tmp_path / "x.sdc", "x", tmp_path, tag="n")
    assert "set_timing_derate" not in s["sta_x_n.tcl"]


def test_every_corner_gets_the_derate(tmp_path, monkeypatch):
    s = _capture(monkeypatch)
    spef = {rc: tmp_path / f"{rc}.spef" for rc in signoff.RC_CORNERS}
    out = signoff.sta_corners(tmp_path / "x.v", tmp_path / "x.sdc", "x", tmp_path, spef, 10)
    assert len(out) == 9 and len(s) == 9
    assert all(n.endswith("_ocv10.tcl") and "set_timing_derate -early 0.9\nset_timing_derate -late 1.1" in t
               for n, t in s.items())
