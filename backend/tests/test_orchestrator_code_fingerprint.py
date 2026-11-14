"""A long-running orchestrator keeps the code it started with (lesson s2s-ops-003): its code fingerprint changes
when any source file changes, so a stale orchestrator is reported instead of silently running old code."""
from s2s.orchestrator import engine


def test_fingerprint_changes_with_any_source_file(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 2\n")
    fp = engine.code_fingerprint(tmp_path)
    assert engine.code_fingerprint(tmp_path) == fp
    (tmp_path / "pkg" / "a.py").write_text("x = 2\n")
    assert engine.code_fingerprint(tmp_path) != fp


def test_real_source_tree_has_a_fingerprint():
    assert len(engine.code_fingerprint()) == 16
