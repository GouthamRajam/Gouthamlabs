#!/usr/bin/env python3
"""Generate behavioral Verilog models for all SKY130 cells in the post-P&R netlist.
Drive strength variants share the same logic — only the module name differs."""

import re, sys

# Map base cell name -> (ports, behavior)
# Format: (output_port, input_ports_list, assign_expression)
# For inverted-output cells: "oi" suffix means inverted output on Y
CELL_LOGIC = {
    # Basic gates
    "and2":    ("X", ["A","B"], "A & B"),
    "and3":    ("X", ["A","B","C"], "A & B & C"),
    "and4":    ("X", ["A","B","C","D"], "A & B & C & D"),
    "or2":     ("X", ["A","B"], "A | B"),
    "or3":     ("X", ["A","B","C"], "A | B | C"),
    "or4":     ("X", ["A","B","C","D"], "A | B | C | D"),
    "nand2":   ("Y", ["A","B"], "~(A & B)"),
    "nand3":   ("Y", ["A","B","C"], "~(A & B & C)"),
    "nand4":   ("Y", ["A","B","C","D"], "~(A & B & C & D)"),
    "nor2":    ("Y", ["A","B"], "~(A | B)"),
    "nor3":    ("Y", ["A","B","C"], "~(A | B | C)"),
    "nor4":    ("Y", ["A","B","C","D"], "~(A | B | C | D)"),
    "xor2":    ("X", ["A","B"], "A ^ B"),
    "xnor2":   ("Y", ["A","B"], "~(A ^ B)"),
    "inv":     ("Y", ["A"], "~A"),
    "buf":     ("X", ["A"], "A"),
    "clkbuf":  ("X", ["A"], "A"),
    "clkinv":  ("Y", ["A"], "~A"),
    "clkinvlp":("Y", ["A"], "~A"),
    "bufinv":  ("Y", ["A"], "~A"),
    "mux2":    ("X", ["A0","A1","S"], "S ? A1 : A0"),
    "mux4":    ("X", ["A0","A1","A2","A3","S0","S1"], "S1 ? (S0 ? A3 : A2) : (S0 ? A1 : A0)"),
    "maj3":    ("X", ["A","B","C"], "(A & B) | (A & C) | (B & C)"),

    # Inverted-input gates: b suffix = one inverted input, bb = two
    "and2b":   ("X", ["A_N","B"], "(~A_N) & B"),
    "and3b":   ("X", ["A_N","B","C"], "(~A_N) & B & C"),
    "and4b":   ("X", ["A_N","B","C","D"], "(~A_N) & B & C & D"),
    "and4bb":  ("X", ["A_N","B_N","C","D"], "(~A_N) & (~B_N) & C & D"),
    "or3b":    ("X", ["A","B","C_N"], "A | B | (~C_N)"),
    "or4b":    ("X", ["A","B","C","D_N"], "A | B | C | (~D_N)"),
    "or4bb":   ("X", ["A","B","C_N","D_N"], "A | B | (~C_N) | (~D_N)"),
    "nand2b":  ("Y", ["A_N","B"], "~((~A_N) & B)"),
    "nand3b":  ("Y", ["A_N","B","C"], "~((~A_N) & B & C)"),
    "nor4b":   ("Y", ["A","B","C","D_N"], "~(A | B | C | (~D_N))"),

    # Complex AO/OA gates
    # a21o: (A1 & A2) | B1
    "a21o":    ("X", ["A1","A2","B1"], "(A1 & A2) | B1"),
    "a21oi":   ("Y", ["A1","A2","B1"], "~((A1 & A2) | B1)"),
    "a21bo":   ("X", ["A1","A2","B1_N"], "(A1 & A2) | (~B1_N)"),
    "a21boi":  ("Y", ["A1","A2","B1_N"], "~((A1 & A2) | (~B1_N))"),
    # a22o: (A1 & A2) | (B1 & B2)
    "a22o":    ("X", ["A1","A2","B1","B2"], "(A1 & A2) | (B1 & B2)"),
    "a22oi":   ("Y", ["A1","A2","B1","B2"], "~((A1 & A2) | (B1 & B2))"),
    # a2bb2o: (~A1_N & ~A2_N) | (B1 & B2)
    "a2bb2o":  ("X", ["A1_N","A2_N","B1","B2"], "((~A1_N) & (~A2_N)) | (B1 & B2)"),
    # a31o: (A1 & A2 & A3) | B1
    "a31o":    ("X", ["A1","A2","A3","B1"], "(A1 & A2 & A3) | B1"),
    "a31oi":   ("Y", ["A1","A2","A3","B1"], "~((A1 & A2 & A3) | B1)"),
    # a32o: (A1 & A2 & A3) | (B1 & B2)
    "a32o":    ("X", ["A1","A2","A3","B1","B2"], "(A1 & A2 & A3) | (B1 & B2)"),
    "a32oi":   ("Y", ["A1","A2","A3","B1","B2"], "~((A1 & A2 & A3) | (B1 & B2))"),
    # a211o: (A1 & A2) | B1 | C1
    "a211o":   ("X", ["A1","A2","B1","C1"], "(A1 & A2) | B1 | C1"),
    "a211oi":  ("Y", ["A1","A2","B1","C1"], "~((A1 & A2) | B1 | C1)"),
    # a221o: (A1 & A2) | (B1 & B2) | C1
    "a221o":   ("X", ["A1","A2","B1","B2","C1"], "(A1 & A2) | (B1 & B2) | C1"),
    "a221oi":  ("Y", ["A1","A2","B1","B2","C1"], "~((A1 & A2) | (B1 & B2) | C1)"),
    # a311o: (A1 & A2 & A3) | B1 | C1
    "a311o":   ("X", ["A1","A2","A3","B1","C1"], "(A1 & A2 & A3) | B1 | C1"),
    "a311oi":  ("Y", ["A1","A2","A3","B1","C1"], "~((A1 & A2 & A3) | B1 | C1)"),
    # a2111o: (A1 & A2) | B1 | C1 | D1
    "a2111o":  ("X", ["A1","A2","B1","C1","D1"], "(A1 & A2) | B1 | C1 | D1"),
    # a41o: (A1 & A2 & A3 & A4) | B1
    "a41o":    ("X", ["A1","A2","A3","A4","B1"], "(A1 & A2 & A3 & A4) | B1"),

    # OA gates: o21a = (A1 | A2) & B1
    "o21a":    ("X", ["A1","A2","B1"], "(A1 | A2) & B1"),
    "o21ai":   ("Y", ["A1","A2","B1"], "~((A1 | A2) & B1)"),
    "o21ba":   ("X", ["A1","A2","B1_N"], "(A1 | A2) & (~B1_N)"),
    "o21bai":  ("Y", ["A1","A2","B1_N"], "~((A1 | A2) & (~B1_N))"),
    "o22a":    ("X", ["A1","A2","B1","B2"], "(A1 | A2) & (B1 | B2)"),
    "o22ai":   ("Y", ["A1","A2","B1","B2"], "~((A1 | A2) & (B1 | B2))"),
    "o2bb2a":  ("X", ["A1_N","A2_N","B1","B2"], "((~A1_N) | (~A2_N)) & (B1 | B2)"),
    "o31a":    ("X", ["A1","A2","A3","B1"], "(A1 | A2 | A3) & B1"),
    "o31ai":   ("Y", ["A1","A2","A3","B1"], "~((A1 | A2 | A3) & B1)"),
    "o32a":    ("X", ["A1","A2","A3","B1","B2"], "(A1 | A2 | A3) & (B1 | B2)"),
    "o211a":   ("X", ["A1","A2","B1","C1"], "(A1 | A2) & B1 & C1"),
    "o211ai":  ("Y", ["A1","A2","B1","C1"], "~((A1 | A2) & B1 & C1)"),
    "o221a":   ("X", ["A1","A2","B1","B2","C1"], "(A1 | A2) & (B1 | B2) & C1"),
    "o221ai":  ("Y", ["A1","A2","B1","B2","C1"], "~((A1 | A2) & (B1 | B2) & C1)"),
    "o311a":   ("X", ["A1","A2","A3","B1","C1"], "(A1 | A2 | A3) & B1 & C1"),
    "o311ai":  ("Y", ["A1","A2","A3","B1","C1"], "~((A1 | A2 | A3) & B1 & C1)"),
    "o41a":    ("X", ["A1","A2","A3","A4","B1"], "(A1 | A2 | A3 | A4) & B1"),
    "o41ai":   ("Y", ["A1","A2","A3","A4","B1"], "~((A1 | A2 | A3 | A4) & B1)"),
    "o2111a":  ("X", ["A1","A2","B1","C1","D1"], "(A1 | A2) & B1 & C1 & D1"),
    "o2111ai": ("Y", ["A1","A2","B1","C1","D1"], "~((A1 | A2) & B1 & C1 & D1)"),
    "o2bb2ai": ("Y", ["A1_N","A2_N","B1","B2"], "~(((~A1_N) | (~A2_N)) & (B1 | B2))"),
    "o32ai":   ("Y", ["A1","A2","A3","B1","B2"], "~((A1 | A2 | A3) & (B1 | B2))"),
}

# Read cell names from netlist
netlist = sys.argv[1]
with open(netlist) as f:
    text = f.read()
cells = sorted(set(re.findall(r'sky130_fd_sc_hd__(\w+)', text)))

out = []
out.append("// Auto-generated behavioral models for sky130_fd_sc_hd cells")
out.append("// Post-P&R netlist coverage — no timing, no power pins")
out.append("`timescale 1ns/1ps\n")

generated = set()
missing = []

for cell in cells:
    modname = f"sky130_fd_sc_hd__{cell}"
    if modname in generated:
        continue

    # Extract base name (strip drive strength suffix)
    m = re.match(r'^(.+?)_(\d+)$', cell)
    if not m:
        missing.append(cell)
        continue
    base = m.group(1)
    drive = m.group(2)

    # Physical-only cells: no logic behavior needed
    if base in ("diode", "fill", "decap", "tapvpwrvgnd", "conb"):
        if base == "diode":
            out.append(f"module {modname} (DIODE);")
            out.append(f"  input DIODE;")
        elif base == "tapvpwrvgnd":
            out.append(f"module {modname} ();")
        elif base in ("fill", "decap"):
            out.append(f"module {modname} ();")
        elif base == "conb":
            out.append(f"module {modname} (HI, LO);")
            out.append(f"  output HI, LO;")
            out.append(f"  assign HI = 1'b1; assign LO = 1'b0;")
        out.append(f"endmodule\n")
        generated.add(modname)
        continue

    # DFF
    if base == "dfxtp":
        out.append(f"module {modname} (Q, CLK, D);")
        out.append(f"  output reg Q; input CLK, D;")
        out.append(f"  always @(posedge CLK) Q <= D;")
        out.append(f"endmodule\n")
        generated.add(modname)
        continue

    # Scan DFF
    if base == "sdfxtp":
        out.append(f"module {modname} (Q, CLK, D, SCD, SCE);")
        out.append(f"  output reg Q; input CLK, D, SCD, SCE;")
        out.append(f"  always @(posedge CLK) Q <= SCE ? SCD : D;")
        out.append(f"endmodule\n")
        generated.add(modname)
        continue

    # Delay cells — just buffers for behavioral sim
    if base in ("dlygate4sd3", "dlymetal6s2s"):
        out.append(f"module {modname} (X, A);")
        out.append(f"  output X; input A;")
        out.append(f"  assign X = A;")
        out.append(f"endmodule\n")
        generated.add(modname)
        continue

    # Look up logic
    if base in CELL_LOGIC:
        oport, iports, expr = CELL_LOGIC[base]
        ports = [oport] + iports
        out.append(f"module {modname} ({', '.join(ports)});")
        out.append(f"  output {oport}; input {', '.join(iports)};")
        out.append(f"  assign {oport} = {expr};")
        out.append(f"endmodule\n")
        generated.add(modname)
        continue

    missing.append(cell)

print('\n'.join(out))

if missing:
    print(f"\n// WARNING: {len(missing)} cells not modeled: {missing}", file=sys.stderr)
