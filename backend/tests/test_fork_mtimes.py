"""flow.fork keeps state file timestamps (OpenLane resumes from the most recently modified state_out.json)."""
import os

from s2s.physical import flow as olf


def test_fork_keeps_state_order(tmp_path):
    src = tmp_path / "pnr" / "runs" / "it1"
    for i, name in enumerate(["01-a", "02-b", "03-c"]):
        d = src / name
        d.mkdir(parents=True)
        f = d / "state_out.json"
        f.write_text('{"odb": "%s/%s/x.odb"}' % (src, name))
        os.utime(f, (1000 + i, 1000 + i))
    olf.fork(tmp_path / "pnr", "it1", "it2", "placement")  # no placement step dir: copies all steps
    dst = tmp_path / "pnr" / "runs" / "it2"
    newest = max(dst.glob("*/state_out.json"), key=lambda p: p.stat().st_mtime)
    assert newest.parent.name == "03-c"
    assert str(dst) in newest.read_text() and str(src) not in newest.read_text()
