"""flow.clear_from: re-running a stage on a tag that already went further must not resume from the later state."""
import os

from s2s.physical import flow as olf


def _run(tmp_path, names):
    run = tmp_path / "pnr" / "runs" / "it5"
    for i, name in enumerate(names):
        d = run / name
        d.mkdir(parents=True)
        f = d / "state_out.json"
        f.write_text("{}")
        os.utime(f, (1000 + i, 1000 + i))
    return run


def test_rerun_of_placement_drops_cts_and_routing(tmp_path):
    run = _run(tmp_path, ["10-odb-applydeftemplate", "11-openroad-globalplacement", "12-openroad-detailedplacement",
                          "13-openroad-cts", "14-openroad-globalrouting", "15-openroad-stapostpnr"])
    assert olf.clear_from(run, "placement") == ["11-openroad-globalplacement", "12-openroad-detailedplacement",
                                                "13-openroad-cts", "14-openroad-globalrouting",
                                                "15-openroad-stapostpnr"]
    newest = max(run.glob("*/state_out.json"), key=lambda p: p.stat().st_mtime)
    assert newest.parent.name == "10-odb-applydeftemplate"  # OpenLane now resumes from the floorplan


def test_fresh_stage_is_a_no_op(tmp_path):
    run = _run(tmp_path, ["10-odb-applydeftemplate"])
    assert olf.clear_from(run, "placement") == []
    assert olf.clear_from(tmp_path / "missing", "placement") == []
    assert (run / "10-odb-applydeftemplate").exists()


def test_clears_from_the_first_occurrence(tmp_path):
    run = _run(tmp_path, ["11-openroad-globalrouting", "12-x", "13-openroad-globalrouting"])
    assert olf.clear_from(run, "routing") == ["11-openroad-globalrouting", "12-x", "13-openroad-globalrouting"]
