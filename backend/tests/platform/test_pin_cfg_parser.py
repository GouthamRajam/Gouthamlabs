"""pin_order.cfg is checked by OpenLane's own parser (ioplace_parser in s2s-eda), not by a guess."""
import pytest

from s2s.physical import flow as olf
from tests.platform.test_m05_offline import eda_available

pytestmark = pytest.mark.skipif(not eda_available(), reason="s2s-eda image not built")


def _run(tmp_path, text):
    cfg = tmp_path / "pnr" / "pin_order.cfg"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(text)
    (tmp_path / "logs").mkdir()
    return olf.pin_cfg_parser_problems(cfg, tmp_path)


def test_parser_accepts_simple_patterns(tmp_path):
    assert _run(tmp_path, "#W\nclk\nrst_n\nen\n#E\ncount.*\n") == []


def test_parser_rejects_character_range(tmp_path):
    problems = _run(tmp_path, "#W\n^clk$\n#E\ncount\\[[0-7]\\]\n")
    assert problems and "ioplace_parser" in problems[0]
