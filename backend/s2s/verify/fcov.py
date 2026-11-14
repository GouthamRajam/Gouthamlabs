"""Functional coverage from the simulator's own waveform (M0.6, Cora; Vera defines the bins).

A bin is a boolean expression over DUT port names (e.g. "count == 255 and en and up"). The
values are read from the port-level VCD Verilator wrote during the regression and sampled just
before every rising edge of the clock (like an SVA sample), so a bin is hit only when the real
DUT pins showed that combination. The testbench cannot claim coverage it did not produce.

Expressions are parsed with a whitelist (names, integers, comparisons, and/or/not, + - * & | ^ ~
<< >> %, and bit select x[i]); model-written text is never executed.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator

_BIN = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b,
        ast.BitAnd: lambda a, b: a & b, ast.BitOr: lambda a, b: a | b, ast.BitXor: lambda a, b: a ^ b,
        ast.LShift: lambda a, b: a << b, ast.RShift: lambda a, b: a >> b, ast.Mod: lambda a, b: a % b if b else 0}
_CMP = {ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b, ast.Lt: lambda a, b: a < b,
        ast.LtE: lambda a, b: a <= b, ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b}


class BadExpression(ValueError):
    pass


def compile_expr(text: str, names: set[str]) -> ast.AST:
    """Parse and validate a bin expression against the allowed port names."""
    try:
        tree = ast.parse(text, mode="eval").body
    except SyntaxError as e:
        raise BadExpression(f"syntax error: {e.msg}") from None

    def check(n: ast.AST) -> None:
        if isinstance(n, ast.Constant) and type(n.value) in (int, bool):
            return
        if isinstance(n, ast.Name):
            if n.id not in names:
                raise BadExpression(f"'{n.id}' is not a DUT port")
            return
        if isinstance(n, ast.BoolOp):
            return [check(v) for v in n.values] and None
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.Not, ast.Invert, ast.USub)):
            return check(n.operand)
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            check(n.left)
            return check(n.right)
        if isinstance(n, ast.Compare) and all(type(o) in _CMP for o in n.ops):
            check(n.left)
            return [check(c) for c in n.comparators] and None
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name):
            check(n.value)
            return check(n.slice)
        raise BadExpression(f"'{ast.unparse(n)}' is not allowed in a coverage bin")
    check(tree)
    return tree


def evaluate(tree: ast.AST, v: dict[str, int | None]) -> bool:
    def ev(n: ast.AST):
        if isinstance(n, ast.Constant):
            return int(n.value)
        if isinstance(n, ast.Name):
            x = v.get(n.id)
            if x is None:  # X/Z: the bin is not hit on this sample
                raise _Unknown
            return x
        if isinstance(n, ast.BoolOp):  # short-circuit like Python: a guard can protect the operands after it
            if isinstance(n.op, ast.And):
                return int(all(ev(x) for x in n.values))
            return int(any(ev(x) for x in n.values))
        if isinstance(n, ast.UnaryOp):
            x = ev(n.operand)
            return int(not x) if isinstance(n.op, ast.Not) else (~x if isinstance(n.op, ast.Invert) else -x)
        if isinstance(n, ast.BinOp):
            return _BIN[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.Compare):
            left = ev(n.left)
            for op, c in zip(n.ops, n.comparators):
                right = ev(c)
                if not _CMP[type(op)](left, right):
                    return 0
                left = right
            return 1
        if isinstance(n, ast.Subscript):
            return (ev(n.value) >> ev(n.slice)) & 1
        raise BadExpression(ast.unparse(n))
    try:
        return bool(ev(tree))
    except _Unknown:
        return False


class _Unknown(Exception):
    pass


def vcd_samples(path: Path, clock: str) -> Iterator[dict[str, int | None]]:
    """Port values of the top scope just before each rising edge of `clock`."""
    ids: dict[str, str] = {}
    depth, top_seen = 0, False
    values: dict[str, int | None] = {}
    f = open(path, errors="replace")  # streamed: regression waveforms can be hundreds of MB
    lines = (ln.rstrip("\n") for ln in f)
    for line in lines:
        t = line.split()
        if not t:
            continue
        if t[0] == "$scope":
            depth += 1
            top_seen = True
        elif t[0] == "$upscope":
            depth -= 1
        elif t[0] == "$var" and depth == 1:  # the TOP wrapper scope: the DUT's ports
            ids[t[3]] = t[4]
        elif t[0] == "$enddefinitions":
            break
    if not top_seen or clock not in ids.values():
        f.close()
        return
    clk_id = next(k for k, n in ids.items() if n == clock)
    pending: dict[str, int | None] = {}
    for line in lines:
        if not line:
            continue
        if line[0] == "#":
            if pending:
                if pending.get(clk_id) == 1 and values.get(clk_id) == 0:
                    yield {ids[k]: x for k, x in values.items()}
                values.update(pending)
                pending = {}
            continue
        if line[0] in "01xXzZ" and len(line) > 1 and line[1:] in ids:
            pending[line[1:]] = None if line[0] in "xXzZ" else int(line[0])
        elif line[0] in "bB":
            bits, ident = line[1:].split()
            if ident in ids:
                pending[ident] = None if any(c in "xXzZ" for c in bits) else int(bits, 2)
    if pending and pending.get(clk_id) == 1 and values.get(clk_id) == 0:
        yield {ids[k]: x for k, x in values.items()}
    f.close()


def bin_hits(vcds: list[Path], clock: str, bins: list[dict], ports: set[str]) -> dict[str, int]:
    """Hits per bin name over all waveforms. Bins with invalid expressions raise BadExpression."""
    trees = {b["name"]: compile_expr(b["expr"], ports) for b in bins}
    hits = {name: 0 for name in trees}
    # a bin's value depends only on the sampled port values, so evaluate each distinct sample once and
    # count how often it occurs (same hit counts, much faster on long regressions)
    seen: dict[tuple, int] = {}
    for vcd in vcds:
        for sample in vcd_samples(vcd, clock):
            key = tuple(sorted(sample.items()))
            seen[key] = seen.get(key, 0) + 1
    for key, n in seen.items():
        sample = dict(key)
        for name, tree in trees.items():
            if evaluate(tree, sample):
                hits[name] += n
    return hits
