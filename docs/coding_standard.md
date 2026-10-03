# RTL Coding Standard (summary — full version in MASTER_SPEC Appendix D)
1. Verilog-2005-compatible SystemVerilog subset in Phase 0.
2. One module per file; file name = module name; lowercase_with_underscores.
3. Signal suffixes: _q register, _d next value, _n active-low.
4. Sequential: non-blocking only. Combinational: blocking, with default assignments (no latches).
5. Every case has a default. Parameterize widths/depths. No magic numbers.
6. Synchronous active-low reset by default; every state element reset unless documented.
7. Async inputs pass through a 2-flop synchronizer (sync2).
8. No initial blocks/delays/system tasks in synthesizable code.
9. Header comment: purpose, REQ IDs, assumptions. // REQ-### trace comments.
