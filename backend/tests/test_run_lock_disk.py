"""One runner per task (a second concurrent run is refused, never executed) and the disk-headroom check."""
import contextlib
import fcntl
from collections import namedtuple
from types import SimpleNamespace

import pytest

from s2s.agents import runtime
from s2s.tools import runner


def test_second_runner_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("S2S_LOCK_DIR", str(tmp_path))
    ran, events = [], []
    monkeypatch.setattr(runtime, "_run_task", lambda *a, **k: ran.append(a) or runtime.Outcome("completed"))

    @contextlib.contextmanager
    def fake_session():
        yield SimpleNamespace(get=lambda model, tid: SimpleNamespace(run_id="run_x", stage="place_route"))
    monkeypatch.setattr(runtime, "db_session", fake_session)
    monkeypatch.setattr(runtime, "emit", lambda s, kind, summary, **kw: events.append((kind, summary)))
    with open(tmp_path / "task_t1.lock", "a") as held:  # another process/thread holds the task
        fcntl.flock(held, fcntl.LOCK_EX)
        out = runtime.run_task("t1", agent=None)
    assert out.status == "refused" and not ran
    assert events and "second concurrent run" in events[0][1]
    assert runtime.run_task("t1", agent=None).status == "completed" and len(ran) == 1  # free again


def test_disk_headroom(tmp_path, monkeypatch):
    usage = namedtuple("u", "total used free")
    monkeypatch.setattr(runner.shutil, "disk_usage", lambda p: usage(10e9, 9e9, 1e9))
    monkeypatch.setenv("S2S_MIN_FREE_GB", "2")
    with pytest.raises(runner.EdaUnavailable, match="1.0 GB free"):
        runner.check_disk_headroom(tmp_path)
    monkeypatch.setenv("S2S_MIN_FREE_GB", "0.5")
    runner.check_disk_headroom(tmp_path)  # enough: no error
