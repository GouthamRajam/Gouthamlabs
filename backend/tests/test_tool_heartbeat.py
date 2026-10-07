"""Phase 1 harness #3: while an EDA tool process is alive the runner beats for the step that started it, so the stall
watchdog stops raising false "stalled" alarms during long mutation / formal / OpenLane runs. A hung tool still ends
at its own timeout; without a step (no heartbeat installed) nothing beats."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from s2s.tools import runner


@pytest.fixture(autouse=True)
def local_mode(monkeypatch):
    monkeypatch.setenv("S2S_EDA_MODE", "local")
    monkeypatch.setenv("S2S_EDA_IMAGE_ID", "test")
    runner.image_id.cache_clear()
    yield
    runner.image_id.cache_clear()


def _run(tmp_path, secs, timeout=30, name="t"):
    return runner.run(["sleep", str(secs)], tmp_path, tmp_path / f"{name}.log", "yosys", timeout)


def test_beats_while_the_tool_runs(tmp_path):
    beats = []
    with runner.heartbeat_to(beats.append, 0.2):
        rec = _run(tmp_path, 1.1)
    assert rec.exit_code == 0 and not rec.timed_out
    assert len(beats) >= 3 and all(b.startswith("yosys running") for b in beats)


def test_timeout_still_kills_a_hung_tool(tmp_path):
    beats = []
    with runner.heartbeat_to(beats.append, 0.2):
        rec = _run(tmp_path, 30, timeout=1)
    assert rec.timed_out and rec.exit_code is None and rec.duration_s < 5 and beats


def test_no_step_no_heartbeat_and_a_failing_heartbeat_never_breaks_the_tool(tmp_path):
    assert _run(tmp_path, 0.3, name="a").exit_code == 0  # nothing installed: nothing to call

    def broken(_):
        raise RuntimeError("database down")
    with runner.heartbeat_to(broken, 0.1):
        assert _run(tmp_path, 0.5, name="b").exit_code == 0


def test_heartbeat_reaches_worker_threads(tmp_path):
    beats = []
    with runner.heartbeat_to(beats.append, 0.2):
        with ThreadPoolExecutor(2) as pool:
            list(pool.map(runner.carry_heartbeat(lambda i: _run(tmp_path, 0.7, name=f"w{i}")), range(2)))
    assert len(beats) >= 2
    with ThreadPoolExecutor(1) as pool:  # without carry_heartbeat the worker has no step to beat for
        beats.clear()
        with runner.heartbeat_to(beats.append, 0.2):
            pool.submit(lambda: _run(tmp_path, 0.6, name="x")).result()
    assert beats == []
