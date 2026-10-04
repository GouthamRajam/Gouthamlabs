"""Mutation engine (Myra, A3.12; M0.6 acceptance 2): realistic bugs injected into COPIES of
known-good RTL, never into the design's own files.

Deterministic: candidate sites are found with fixed patterns on comment-free code lines, then a
seeded, type-balanced sample is taken, so the same RTL always yields the same mutants.

Bug types (A3.12): wrong_operator, off_by_one, stuck_bit, missing_reset, swapped_condition,
dropped_handshake. A mutant that does not compile (Verilator, errors only) is discarded and
replaced by the next candidate; it is a broken file, not a bug the tests should catch.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass

TYPES = ("wrong_operator", "off_by_one", "stuck_bit", "missing_reset", "swapped_condition", "dropped_handshake")


@dataclass(frozen=True)
class Mutant:
    id: str
    type: str
    file: str  # rtl/<module>.v
    line: int  # 1-based
    before: str
    after: str
    description: str
    reqs: tuple[str, ...]  # REQ ids traced on or near the line (what behavior it breaks)

    def apply(self, text: str) -> str:
        lines = text.split("\n")
        assert lines[self.line - 1] == self.before, "mutant does not match the file"
        lines[self.line - 1] = self.after
        return "\n".join(lines)


def _code(line: str) -> tuple[str, str]:
    """(code, comment) of one line."""
    i = line.find("//")
    return (line, "") if i < 0 else (line[:i], line[i:])


def _outside_brackets(code: str, start: int) -> bool:
    return code[:start].count("[") == code[:start].count("]") and code[:start].count("{") == code[:start].count("}")


_OPS = [(r"(?<![+])\+(?![+=:])", "-", "+ -> -"), (r"(?<![-\[])-(?![-=>:])", "+", "- -> +"),
        (r"&&", "||", "&& -> ||"), (r"\|\|", "&&", "|| -> &&"), (r"==", "!=", "== -> !="),
        (r"!=", "==", "!= -> =="), (r"(?<![&])&(?![&])", "|", "& -> |"), (r"(?<![|])\|(?![|])", "&", "| -> &"),
        (r"\^", "&", "^ -> &"), (r"(?<![<>=!])<(?![<=])", "<=", "< -> <="), (r"(?<![<>=!])>(?![>=])", ">=", "> -> >=")]
_NB_ASSIGN = re.compile(r"^(\s*)(\w+)(\s*(?:\[[^\]]*\])?\s*)<=(.*);")
_COND = re.compile(r"\b(if|else if)\s*\((.*)\)\s*(begin)?\s*$")
_LITERAL = re.compile(r"(\d+)'([dDhHbB])([0-9a-fA-F_]+)")
_ASSIGN = re.compile(r"^(\s*assign\s+)(\w+)(\s*=\s*)(.*);")
_BLOCKING = re.compile(r"^(\s*(?:\w+\s*:\s*)?)(\w+)(\s*(?:\[[^\]]*\])?\s*)=(?!=)(.*);")
_REQ = re.compile(r"REQ-\d{3}")


def _reqs(lines: list[str], i: int) -> tuple[str, ...]:
    near = " ".join(lines[max(0, i - 3):i + 2])
    return tuple(sorted(set(_REQ.findall(near))))


_DECL = re.compile(r"\b(?:input|output|inout|reg|wire)\b(?:\s+(?:wire|reg|signed))*\s*(\[[^\]]+\])?\s*([A-Za-z_]\w*)")


def _widths(text: str) -> dict[str, str]:
    """Declared signal -> its range text ('' for 1-bit), from port and net declarations."""
    out: dict[str, str] = {}
    for line in text.split("\n"):
        code = _code(line)[0]
        for m in _DECL.finditer(code):
            out.setdefault(m[2], (m[1] or "").replace(" ", ""))
    return out


def candidates(files: dict[str, str]) -> list[Mutant]:
    out: list[Mutant] = []
    for path, text in sorted(files.items()):
        lines = text.split("\n")
        widths = _widths(text)
        in_block_comment = False
        reset_depth = None
        for i, raw in enumerate(lines):
            if in_block_comment:
                if "*/" in raw:
                    in_block_comment = False
                continue
            if raw.strip().startswith("/*"):
                in_block_comment = "*/" not in raw
                continue
            code, comment = _code(raw)
            s = code.strip()
            n = 0
            if s.startswith("localparam") and (m := _LITERAL.search(code)):
                # a wrong encoding/constant: off by one in a localparam value
                base = {"d": 10, "h": 16, "b": 2}[m[2].lower()]
                try:
                    val = int(m[3].replace("_", ""), base)
                    new = (val + 1) % (1 << int(m[1]))
                    digits = format(new, {10: "d", 16: "x", 2: "b"}[base]).zfill(len(m[3]) if base == 2 else 1)
                    n += 1
                    out.append(Mutant(f"{path.rsplit('/', 1)[-1].split('.')[0]}_L{i + 1}_off_by_one_{n}", "off_by_one",
                                      path, i + 1, raw, code[:m.start()] + f"{m[1]}'{m[2]}{digits}" + code[m.end():] + comment,
                                      f"{path}:{i + 1}: localparam {m[0]} -> {m[1]}'{m[2]}{digits}", _reqs(lines, i)))
                except ValueError:
                    pass
                continue
            if not s or s.startswith(("module", "input", "output", "inout", "parameter", "localparam",
                                       "wire", "reg", "integer", "`", "endmodule", ")", "(")):
                continue

            def add(kind: str, new_code: str, desc: str) -> None:
                nonlocal n
                n += 1
                out.append(Mutant(f"{path.rsplit('/', 1)[-1].split('.')[0]}_L{i + 1}_{kind}_{n}", kind, path, i + 1,
                                  raw, new_code + comment, f"{path}:{i + 1}: {desc}", _reqs(lines, i)))
            is_nb = bool(_NB_ASSIGN.match(code))
            # wrong operator (not inside [] ranges or {} replications; not the <= of an assignment)
            rhs_start = code.find("<=") + 2 if is_nb else (code.find("=") + 1 if "assign" in code else 0)
            bm = _BLOCKING.match(code) if not is_nb and "assign" not in code else None
            if bm:
                rhs_start = code.find("=") + 1
            for pat, rep, desc in _OPS:
                for m in re.finditer(pat, code):
                    if m.start() < rhs_start or not _outside_brackets(code, m.start()):
                        continue
                    add("wrong_operator", code[:m.start()] + rep + code[m.end():], desc)
            # inverted value: a register or combinational result driven with the bits flipped
            if is_nb or bm:
                mm = _NB_ASSIGN.match(code) if is_nb else bm
                rhs = mm[4].strip()
                if rhs and not rhs.startswith("~"):
                    op = "<=" if is_nb else "="
                    add("wrong_operator", f"{mm[1]}{mm[2]}{mm[3]}{op} ~({rhs});", f"{mm[2]} driven inverted")
            # wrong operand: a right-hand-side signal replaced by another signal of the same width
            mm = (_NB_ASSIGN.match(code) if is_nb else None) or bm or _ASSIGN.match(code)
            if mm:
                rhs_text = mm[4]
                for tok in re.finditer(r"\b[A-Za-z_]\w*\b", rhs_text):
                    w = widths.get(tok[0])
                    if w is None:
                        continue
                    alt = sorted(n for n, x in widths.items() if x == w and n not in (tok[0], mm[2]))
                    if alt:
                        start = code.index(rhs_text) + tok.start()
                        add("wrong_operator", code[:start] + alt[0] + code[start + len(tok[0]):],
                            f"operand {tok[0]} replaced by {alt[0]}")
                        break
            if bm and bm[4].strip() != bm[2]:
                add("stuck_bit", f"{bm[1]}{bm[2]}{bm[3]}= {bm[2]};", f"{bm[2]} keeps its old value (update lost)")
            # off by one on sized literals in expressions/comparisons
            for m in _LITERAL.finditer(code):
                if m.start() < rhs_start and not _COND.search(code):
                    continue
                base = {"d": 10, "h": 16, "b": 2}[m[2].lower()]
                try:
                    val = int(m[3].replace("_", ""), base)
                except ValueError:
                    continue
                width = int(m[1])
                new = (val + 1) % (1 << width) if width < 64 else val + 1
                digits = format(new, {10: "d", 16: "x", 2: "b"}[base])
                add("off_by_one", code[:m.start()] + f"{m[1]}'{m[2]}{digits}" + code[m.end():],
                    f"literal {m[0]} -> {m[1]}'{m[2]}{digits}")
                break
            # swapped condition
            if m := _COND.search(code):
                add("swapped_condition", code[:m.start(2)] + f"!({m[2]})" + code[m.end(2):], f"condition ({m[2]}) negated")
            # reset branch tracking: assignments right under `if (!rst_n)` / `if (rst)` are reset values
            rst = re.search(r"if\s*\(\s*(!\s*\w*rst\w*|~\s*\w*rst\w*|\w*rst\w*\s*==\s*1'b0|\w*reset\w*)\s*\)", code)
            if rst and (one := re.search(r"\)\s*(\w+)(\s*(?:\[[^\]]*\])?\s*)<=([^;]*);", code[rst.end() - 1:])):
                # single-line reset branch: `if (!rst_n) q <= 0;` -> the assignment is dropped
                start = rst.end() - 1 + one.start() + 1
                add("missing_reset", code[:start] + " ;" + code[rst.end() - 1 + one.end():],
                    f"reset assignment of {one[1]} removed")
            elif rst:
                reset_depth = i
            elif reset_depth is not None and is_nb and i - reset_depth <= 8:
                m = _NB_ASSIGN.match(code)
                add("missing_reset", f"{m[1]}// s2s-mutant: reset of {m[2]} removed", f"reset assignment of {m[2]} removed")
            if s.startswith("end") and reset_depth is not None and i - reset_depth > 0 and "else" in s:
                reset_depth = None
            elif reset_depth is not None and s.startswith("else"):
                reset_depth = None
            # stuck bit: a register that stops updating outside reset
            if is_nb and reset_depth is None:
                m = _NB_ASSIGN.match(code)
                if m[4].strip() != m[2]:
                    add("stuck_bit", f"{m[1]}{m[2]}{m[3]}<= {m[2]};", f"{m[2]} stuck (never updates)")
            # dropped handshake: an output-style continuous assign forced to a constant
            if m := _ASSIGN.match(code):
                if re.search(r"(ready|valid|ack|req|busy|done|full|empty|_o\b)", m[2]):
                    add("dropped_handshake", f"{m[1]}{m[2]}{m[3]}1'b1;", f"{m[2]} forced to 1 (handshake dropped)")
                else:
                    add("stuck_bit", f"{m[1]}{m[2]}{m[3]}'0;", f"{m[2]} stuck at 0")
    return out


def sample(cands: list[Mutant], n: int = 20, seed: int = 2026) -> list[Mutant]:
    """Type-balanced, deterministic order: round-robin over bug types, shuffled within each type."""
    rnd = random.Random(seed)
    by_type = {t: [c for c in cands if c.type == t] for t in TYPES}
    for v in by_type.values():
        rnd.shuffle(v)
    order: list[Mutant] = []
    while any(by_type.values()):
        for t in TYPES:
            if by_type[t]:
                order.append(by_type[t].pop())
    return order  # caller takes the first n that compile
