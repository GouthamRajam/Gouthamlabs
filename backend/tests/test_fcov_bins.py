"""Functional coverage: bin hits are counted per sampled clock edge (memoized evaluation must not change counts)."""
from s2s.verify import fcov

VCD = """$scope module TOP $end
$var wire 1 ! clk $end
$var wire 1 " en $end
$var wire 4 # count [3:0] $end
$upscope $end
$enddefinitions $end
#0
0!
0"
b0000 #
#1
1!
#2
0!
1"
b0011 #
#3
1!
#4
0!
#5
1!
#6
0!
b1111 #
#7
1!
"""


def test_bin_hits_counts_every_sampled_edge(tmp_path):
    p = tmp_path / "dump.vcd"
    p.write_text(VCD)
    bins = [{"name": "en_three", "expr": "en and count == 3"}, {"name": "full", "expr": "count == 15"},
            {"name": "idle", "expr": "not en"}]
    hits = fcov.bin_hits([p, p], "clk", bins, {"clk", "en", "count"})
    # edges sample (en,count): (0,0), (1,3), (1,3), (1,15); two copies of the waveform
    assert hits == {"en_three": 4, "full": 2, "idle": 2}


def test_and_short_circuits_like_python():
    names = {"a", "b"}
    tree = fcov.compile_expr("(b & 7) != 0 and ((a >> ((b & 7) - 1)) & 1) == 1", names)
    assert fcov.evaluate(tree, {"a": 0xFF, "b": 8}) is False  # guard false: the -1 shift is never computed
    assert fcov.evaluate(tree, {"a": 0b100, "b": 3}) is True
    tree_or = fcov.compile_expr("b == 0 or (a >> (b - 1)) == 1", names)
    assert fcov.evaluate(tree_or, {"a": 5, "b": 0}) is True
