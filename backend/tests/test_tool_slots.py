"""Machine-wide tool slots (s2s.tools.runner): concurrent runs queue instead of oversubscribing the cores."""
import threading
import time

from s2s.tools import runner


def test_slots_cap_concurrency_across_threads(tmp_path, monkeypatch):
    monkeypatch.setenv("S2S_LOCK_DIR", str(tmp_path))
    monkeypatch.setenv("S2S_TOOL_SLOTS", "2")
    live, peak, lock = [0], [0], threading.Lock()

    def job(key):
        with runner.tool_slots_held(key):
            with lock:
                live[0] += 1
                peak[0] = max(peak[0], live[0])
            time.sleep(0.3)
            with lock:
                live[0] -= 1

    threads = [threading.Thread(target=job, args=("verilator",)) for _ in range(5)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert peak[0] == 2


def test_openlane_takes_two_slots(tmp_path, monkeypatch):
    monkeypatch.setenv("S2S_LOCK_DIR", str(tmp_path))
    monkeypatch.setenv("S2S_TOOL_SLOTS", "2")
    order = []

    def ol():
        with runner.tool_slots_held("openlane") as n:
            order.append(("ol_start", n))
            time.sleep(0.4)
            order.append(("ol_end", n))

    def sim():
        time.sleep(0.1)  # starts while OpenLane holds both slots
        with runner.tool_slots_held("verilator"):
            order.append(("sim", 1))

    a, b = threading.Thread(target=ol), threading.Thread(target=sim)
    a.start(); b.start(); a.join(); b.join()
    assert order == [("ol_start", 2), ("ol_end", 2), ("sim", 1)]
