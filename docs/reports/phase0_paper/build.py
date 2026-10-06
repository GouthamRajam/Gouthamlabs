"""Build the Phase 0 results paper (PDF) from data.json (collect.py) and the figures (figs.py)."""
import json, sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

S, OUT = sys.argv[1], sys.argv[2]
D = json.load(open(f"{S}/data.json"))
N = list(D)
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="Times-Roman", fontSize=10, leading=13.2, alignment=TA_JUSTIFY,
                      spaceAfter=5)
small = ParagraphStyle("s", parent=body, fontSize=8, leading=10, alignment=0, spaceAfter=0)
cell = ParagraphStyle("c", parent=small, fontName="Helvetica", fontSize=7.2, leading=8.8)
cellb = ParagraphStyle("cb", parent=cell, fontName="Helvetica-Bold")
cap = ParagraphStyle("cap", parent=body, fontSize=8.5, leading=10.5, alignment=TA_CENTER, spaceBefore=3, spaceAfter=9,
                     fontName="Times-Italic")
h1 = ParagraphStyle("h1", parent=body, fontName="Times-Bold", fontSize=12, leading=15, spaceBefore=9, spaceAfter=4, keepWithNext=1,
                    alignment=0)
h2 = ParagraphStyle("h2", parent=h1, fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=3, fontName="Times-BoldItalic", keepWithNext=1)
title = ParagraphStyle("t", parent=body, fontName="Times-Bold", fontSize=17, leading=21, alignment=TA_CENTER, spaceAfter=6)
auth = ParagraphStyle("a", parent=body, alignment=TA_CENTER, fontSize=10, spaceAfter=2)
absS = ParagraphStyle("abs", parent=body, fontSize=9.2, leading=12, leftIndent=12 * mm, rightIndent=12 * mm)
P = lambda t, s=body: Paragraph(t, s)


def table(rows, widths, header_rows=1, note=None):
    data = [[P(str(c), cellb if r < header_rows else cell) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=header_rows)
    st = [("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black), ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.5, colors.black),
          ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
          ("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5)]
    for r in range(header_rows, len(rows)):
        if (r - header_rows) % 2:
            st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f3f5f8")))
    t.setStyle(TableStyle(st))
    return t


f1 = lambda x, n=1: f"{x:.{n}f}"
uW = lambda w: f"{w * 1e6:.1f}"
s = []
s += [P("Agent-Driven RTL-to-GDSII on the Open SKY130 Process:<br/>Signoff Results for Five Digital Blocks", title),
      P("S2S (Spec-to-Silicon) project, Goutham Labs", auth),
      P("Phase 0 technical report, 6 October 2026. Pre-silicon results only; no wafers were fabricated.", auth),
      Spacer(1, 6)]
s.append(P(
    "<b>Abstract.</b> We report the implementation and signoff results of five synchronous digital blocks (counter8, alu8, "
    "sync_fifo, uart, spi_master) taken from a written specification to a GDSII layout by a multi-agent design system on the "
    "open SkyWater SKY130 130 nm process (sky130_fd_sc_hd library), using only open-source tools (Yosys, OpenROAD/OpenLane "
    "2.3.10, OpenSTA, Magic, KLayout, Netgen, SymbiYosys/eqy). Every number is produced by a tool run whose log and inputs are "
    "kept in a signed evidence package. All five layouts are DRC-clean in two independent checkers, LVS-matched, antenna-clean "
    "and meet setup and hold at all nine PVT/RC corners. Clock frequencies are 50-100 MHz; die areas are 3,119-98,116 "
    "um<super>2</super>. Estimated total power at the typical corner ranges from 146.6 uW to 5.75 mW at 20% input activity, "
    "and the worst static IR drop is 1.37 mV (0.08% of 1.8 V) against a 90 mV limit. One block (spi_master) passes only under "
    "a clock-net fanout rule of 20, and electromigration, dynamic IR, scan/ATPG test coverage, reliability and foundry-certified "
    "signoff are not yet assessed. We list, check by check, what a production tape-out additionally requires.", absS))

s.append(P("1. Introduction", h1))
s.append(P(
    "A digital chip is released for manufacturing (\"tape-out\") only when a set of absolute checks pass: the layout obeys the "
    "foundry's geometric rules (DRC), the layout is the same circuit as the netlist (LVS), the circuit meets its clock at every "
    "process, voltage and temperature corner (static timing analysis), and the netlist is logically the same as the verified "
    "RTL (equivalence). Around these hard gates sit engineering judgments on power, power-grid resistance, manufacturability and "
    "test. This report gives the measured values for each of these on five blocks, states which checks were run, and separates "
    "what is proven from what is estimated or deferred. The aim is a lab-scale research baseline: small, fully reproducible "
    "designs on an open process, with every figure traceable to a tool log."))

s.append(P("2. Method", h1))
s.append(P(
    "<b>Process and library.</b> SkyWater SKY130A (130 nm, 1.8 V core), standard-cell library sky130_fd_sc_hd. "
    "<b>Flow.</b> Specification and RTL are produced and verified by agents (simulation with Verilator/Icarus/cocotb, coverage, "
    "SymbiYosys properties, mutation testing). Synthesis (Yosys), floorplan, placement, clock-tree synthesis (TritonCTS), routing "
    "and stream-out run in OpenLane 2.3.10. Signoff checks are then re-run independently on the final streamed GDS: DRC with "
    "Magic and KLayout, LVS with Magic extraction + Netgen, antenna with OpenROAD, density with the PDK KLayout deck, 9-corner "
    "STA with OpenSTA on extracted parasitics (SPEF), power with OpenSTA report_power, static IR with OpenROAD PSM, and "
    "RTL-to-final-netlist equivalence with eqy or a Yosys LEC fallback. "
    "<b>Corners.</b> Three library corners (SS 100 &deg;C 1.60 V, TT 25 &deg;C 1.80 V, FF -40 &deg;C 1.95 V) x three RC "
    "extraction corners (min, nom, max) = 9 timing corners. "
    "<b>Integrity.</b> Each block's tape-out package holds the GDS, netlists, SDC, SPEF, reports and a reproduce.sh that "
    "re-runs the checks in a clean container; a SHA-256 manifest covers every file (Appendix A). Tool pass/fail decides each "
    "check; the agents never decide it."))

s.append(P("3. Designs and implementation", h1))
rows = [["Block", "Function", "Clock", "Cells (synth)", "Synth area um<super>2</super>", "Die area um<super>2</super>",
         "Placed inst.", "Util.", "Wire length um", "Vias", "Nets"]]
fn = {"counter8": "8-bit up/down counter with load", "alu8": "8-bit ALU, 8 ops, flags", "sync_fifo": "synchronous FIFO",
      "uart": "UART TX/RX, prog. baud", "spi_master": "SPI master, prog. clock"}
for d in N:
    v = D[d]
    rows.append([d, fn[d], f"{1e3 / v['period_ns']:.0f} MHz ({v['period_ns']:.2f} ns)", v["synth_cells"], f1(v["synth_area_um2"]),
                 f1(v["die_area_um2"]), v["instances"], f"{v['utilization'] * 100:.1f}%", f"{v['wirelength_um']:,}",
                 f"{v['vias']:,}", v["nets"]])
s.append(KeepTogether([table(rows, [17, 27, 20, 13, 15, 16, 13, 11, 16, 13, 10]),
P("Table 1. Implementation summary. Placed instances include tap cells, timing buffers and hold buffers; utilization is "
           "placed standard-cell area over core area. Wire length and via count are from the detailed router.", cap)]))
s.append(KeepTogether([Image(f"{S}/fig_layouts.png", width=178 * mm, height=178 * mm * 792 / 3300),
P("Figure 1. Final layouts rendered from the signed GDSII files (li1 and met1-met5 shown; to scale per panel). The "
           "horizontal met1 rails are the standard-cell power rows; vertical met4 and horizontal met5 straps form the power grid.", cap)]))

s.append(P("4. Results", h1))
s.append(P("4.1 Physical verification", h2))
rows = [["Block", "DRC Magic", "DRC KLayout", "LVS (Netgen)", "Devices", "Antenna nets", "XOR (stream-out)", "Result"]]
for d in N:
    v = D[d]
    rows.append([d, v["drc_magic"], v["drc_klayout"], v["lvs"], v["lvs_devices"], v["antenna_nets"], v["xor"], "PASS"])
s.append(KeepTogether([table(rows, [20, 17, 18, 38, 15, 18, 22, 17]),
P("Table 2. Physical verification on the final streamed GDS. Two DRC engines with the SKY130 open rule decks agree at 0 "
           "violations; LVS matches device-for-device and net-for-net.", cap)]))

s.append(P("4.2 Timing", h2))
rows = [["Block", "Clock period ns", "Worst setup slack ns (corner)", "Setup slack TT ns", "Worst hold slack ns (corner)",
         "Corners met", "Clock-tree skew ns (worst)", "Slew / cap viol.", "Hold buffers"]]
for d in N:
    v = D[d]
    rows.append([d, f"{v['period_ns']:.3f}", f"+{v['setup_ws'][0]:.4f} ({v['setup_ws'][1]})", f"+{v['tt_setup']:.4f}",
                 f"+{v['hold_ws'][0]:.4f} ({v['hold_ws'][1]})", f"{v['corners_passed']}/{v['corners']}",
                 f"{v['tree_skew_ns_max']:.4f}", f"{v['slew_viol']} / {v['cap_viol']}", v["hold_buffers"]])
s.append(KeepTogether([table(rows, [17, 14, 30, 15, 30, 13, 17, 14, 13]),
P("Table 3. Post-route static timing with extracted parasitics at 9 corners (OpenSTA, propagated clocks, 0.25 ns clock "
           "uncertainty). Total negative slack is 0 at every corner for every block.", cap)]))
s.append(P(
    "Setup is limited at the slow corner (SS 100 &deg;C 1.60 V, max RC) and hold at the fast corner (FF -40 &deg;C 1.95 V, min "
    "RC), as expected. The thinnest setup margin is sync_fifo at +0.243 ns (2.4% of its 10 ns period), on the combinational read "
    "path to rd_data; the thinnest hold margins are 0.10-0.14 ns at FF (alu8: 0.42 ns). Maximum-fanout design rules: four blocks have no "
    "violator; spi_master has eight leaf clock buffers driving 11-17 flip-flops each, which exceeds the SDC data-net limit of 10 "
    "and passes only under an explicit clock-tree rule of 20 (Section 4.6)."))

s.append(P("4.3 Power", h2))
rows = [["Block", "Total SS 100C 1.60V uW", "Total TT 25C 1.80V uW", "Total FF -40C 1.95V uW", "TT internal uW",
         "TT switching uW", "TT leakage nW", "SS leakage nW", "Energy / cycle TT pJ", "Power density TT W/cm<super>2</super>"]]
for d in N:
    v = D[d]; p = v["power"]; t = p["tt_025C_1v80"]
    rows.append([d, uW(p["ss_100C_1v60"]["total_w"]), uW(t["total_w"]), uW(p["ff_n40C_1v95"]["total_w"]), uW(t["internal_w"]),
                 uW(t["switching_w"]), f"{t['leakage_w'] * 1e9:.2f}", f"{p['ss_100C_1v60']['leakage_w'] * 1e9:.0f}",
                 f"{t['total_w'] * v['period_ns'] * 1e-9 * 1e12:.2f}", f"{t['total_w'] / (v['die_area_um2'] * 1e-8):.2f}"])
s.append(KeepTogether([table(rows, [17, 18, 18, 18, 16, 17, 15, 15, 17, 20]),
P("Table 4. Estimated power (OpenSTA report_power, vector-less, 20% switching activity on inputs, post-route netlist "
           "with parasitics). Energy per cycle = total power x clock period. Power density uses die area.", cap)]))
s.append(KeepTogether([Image(f"{S}/fig_power_ir.png", width=165 * mm, height=165 * mm * 792 / 2420),
P("Figure 2. Left: estimated total power per corner (log scale). Right: worst static IR drop on VPWR at TT against the "
           "90 mV (5% of 1.8 V) limit (log scale).", cap)]))
s.append(P(
    "Internal (cell short-circuit and internal node) power dominates at 60-74% of the total; switching power on interconnect is "
    "the rest. Leakage is negligible at 25 &deg;C (0.5-21 nW) but rises about three orders of magnitude at 100 &deg;C (e.g. "
    "spi_master 4.65 nW at TT to 4.4 uW at SS 100 &deg;C), which is the expected subthreshold-leakage temperature dependence. "
    "sync_fifo draws the most power (5.75 mW at TT) because its storage is built from flip-flops clocked at 100 MHz. These are "
    "estimates: no simulation activity file (VCD/SAIF) was used, so real power depends on the workload."))

s.append(P("4.4 Resistance: interconnect and power grid", h2))
s.append(P(
    "A chip has no single \"resistance\". Two resistances matter for signoff: (i) the resistance of the signal wires and vias, "
    "which with their capacitance sets wire delay (RC) and is read back from the layout as SPEF parasitics, and (ii) the "
    "resistance of the power-delivery network (PDN), which causes a static IR (current x resistance) drop between the supply "
    "pins and each cell. Table 5 gives both."))
rows = [["Block", "Total wire+via R, min RC (ohm)", "Total R, nom RC (ohm)", "Total R, max RC (ohm)", "Total net C, nom (pF)",
         "Highest-R net, nom (ohm, net)", "R segments (nom)", "Worst IR drop VPWR (mV)", "Avg IR drop (mV)",
         "Worst ground bounce VGND (mV)", "IR limit (mV)"]]
for d in N:
    v = D[d]; sp = v["spef"]
    rows.append([d, f"{sp['min']['total_wire_res_ohm']:,.0f}", f"{sp['nom']['total_wire_res_ohm']:,.0f}",
                 f"{sp['max']['total_wire_res_ohm']:,.0f}", f"{sp['nom']['total_net_cap_f'] * 1e12:.2f}",
                 f"{sp['nom']['max_net_res_ohm']:.0f} ({sp['nom']['max_net_res_net']})", f"{sp['nom']['res_segments']:,}",
                 f"{v['ir_worst_v'] * 1e3:.3f}", f"{v['ir_avg_v'] * 1e3:.3f}", f"{v['vgnd_bounce_v'] * 1e3:.3f}",
                 f"{v['ir_limit_v'] * 1e3:.0f}"])
s.append(KeepTogether([table(rows, [16, 17, 16, 16, 14, 25, 14, 15, 13, 17, 12]),
P("Table 5. Interconnect resistance and capacitance summed over all routed nets from the signed SPEF files (OpenROAD "
           "extraction, three RC corners), and static PDN IR drop at TT (OpenROAD PSM).", cap)]))
s.append(P(
    "Total routed resistance scales with wire length (2.6-3.6 ohm per um of routed wire at nominal RC across the five blocks), "
    "and the max-RC corner is 2.2-2.3x nominal and 4.9-5.8x min-RC, which is why the slow-corner timing uses max RC. The "
    "highest-resistance single net is 232-561 ohm; in spi_master it is a leaf clock net (clknet_3_5__leaf_clk). The worst static "
    "IR drop is 0.05-1.37 mV, at most about 1.5% of the 90 mV budget, so the default SKY130 power grid is heavily over-provisioned for "
    "blocks of this size. Electromigration (current density in wires and vias) and dynamic (switching-transient) IR drop were "
    "<b>not analysed</b>; they are required before a production tape-out (Section 5)."))

rows = [["Block", "High", "Medium", "Low", "Top items"]]
for d in N:
    v = D[d]
    top = "; ".join(f"{i[0]} ({i[1]}): {i[2]}" for i in v["dfm_items"][:3])
    rows.append([d, v["dfm"]["high"], v["dfm"]["medium"], v["dfm"]["low"], top])
s.append(KeepTogether([P("4.5 Manufacturability (DFM)", h2), table(rows, [17, 10, 12, 10, 121]),
P("Table 6. DFM scorecard from KLayout geometry analysis of the final GDS (near-minimum spacing, line ends, via "
           "redundancy and density). No high-severity item in any block. All vias are single-cut.", cap)]))

s.append(P("4.6 Gate decision", h2))
rows = [["Block", "DRC", "LVS", "Antenna", "Timing (all corners)", "Equivalence", "Hard checks", "Derived score A / B"]]
for d in N:
    v = D[d]
    tim = "PASS (conditional)" if v["clock_rule_allowed"] else "PASS"
    rows.append([d, "PASS", "PASS", "PASS", tim, "PASS", v["hard"], f"{v['A']}% / {v['B']}%"])
s.append(KeepTogether([table(rows, [18, 12, 12, 14, 26, 18, 30, 26]),
P("Table 7. Phase 0 gate: hard checks pass/fail. The percentage is a derived figure (Baseline A = open-shuttle "
           "requirements, 90/97 points; Baseline B = commercial production, 68/106 points) with partial credit dft = 0 and "
           "ir_em = 0.5 (static IR only).", cap)]))
s.append(P(
    "The program-level gate was marked a <b>qualified pass</b> by the project lead: four blocks pass every hard check; spi_master "
    "passes only under the approved clock-net fanout limit of 20 and would fail a flat SDC limit of 10; EM, dynamic IR, DFT "
    "scan/ATPG and artifact-provenance checking are deferred to Phase 1. No check was waived, and no constraint was loosened to "
    "obtain these results."))

s.append(P("5. What a real-world tape-out checks", h1))
s.append(P(
    "Table 8 lists the checks a production tape-out on a commercial foundry process normally requires, and where this work "
    "stands on each. \"Done\" means a real tool ran and passed on these blocks; \"Partial\" means a reduced form ran; \"Not "
    "done\" means it is open work; \"n/a\" means it does not apply to these blocks. Typical pass criteria are industry practice; "
    "the exact limits come from the foundry PDK, the product specification and the qualification standard."))
C = [["Area", "Check", "Typical pass criterion", "This work (Phase 0)"],
     ["Function", "RTL simulation regression", "100% of tests pass, several seeds, two simulators", "Done"],
     ["Function", "Code + functional coverage", "Line >= 95%, toggle >= 90%, all functional bins hit (project targets)", "Done"],
     ["Function", "Formal property checking", "Properties proven (unbounded) or bounded depth documented; no vacuity", "Done"],
     ["Function", "Mutation / fault-injection of the testbench", "Injected-bug detection >= 85% (project target)", "Done for 4 blocks (counter8, sync_fifo 20/20; uart 19/20; spi_master 17/20); alu8 not in the M0.6 record"],
     ["Function", "Equivalence RTL vs. netlist (LEC)", "All compare points proven equivalent", "Done"],
     ["Function", "Gate-level simulation with timing", "Tests pass on final netlist; SDF-annotated GLS at corners", "Partial (functional GLS on final netlist, no SDF timing)"],
     ["Function", "CDC / RDC analysis", "All crossings synchronized and reviewed", "Not done as a separate check"],
     ["Layout", "DRC (foundry deck)", "0 violations on the foundry-certified deck", "Partial (open decks: 0)"],
     ["Layout", "LVS", "Full match, no unmatched devices/nets/pins", "Done (open deck)"],
     ["Layout", "ERC (shorts, floating gates, well taps)", "0 errors", "Partial (via LVS/DRC)"],
     ["Layout", "Antenna", "0 violating nets", "Done"],
     ["Layout", "Density / CMP fill", "Every layer within min/max density windows", "Done (PDK deck)"],
     ["Layout", "Litho / DFM hotspots", "No high-severity hotspot; recommended rules met", "Partial (scorecard)"],
     ["Layout", "Seal ring, pad ring, I/O cells", "Present and DRC/LVS clean at chip level", "n/a (blocks, not a chip)"],
     ["Timing", "Setup / hold at all corners", "WNS >= 0, TNS = 0 at every PVT/RC corner", "Done (9 corners)"],
     ["Timing", "On-chip variation (OCV/AOCV/POCV)", "Met with foundry derates", "Not done"],
     ["Timing", "Signal integrity / crosstalk delay and noise", "No glitch failures; SI-aware timing met", "Not done"],
     ["Timing", "Design-rule violations (slew, cap, fanout)", "0 violations", "Done (spi_master conditional)"],
     ["Timing", "Clock skew / latency / duty cycle", "Within clock budget", "Done (skew <= 0.062 ns)"],
     ["Power", "Power estimate vs. budget", "Below budget, vector-based (VCD/SAIF)", "Partial (vector-less estimate)"],
     ["Power", "Static IR drop", "Worst drop <= 5% (often 2-3%) of supply", "Done (<= 1.37 mV)"],
     ["Power", "Dynamic IR drop / voltage droop", "Droop within budget during worst switching", "Not done"],
     ["Power", "Electromigration (power + signal, DC/AC)", "Current density below foundry limits at max temperature", "Not done"],
     ["Power", "Power intent (UPF/CPF), level shifters", "Clean low-power checks", "n/a (single domain)"],
     ["Reliability", "ESD (HBM/CDM) and latch-up", "Meets JEDEC/ESDA classes, e.g. HBM 2 kV", "Not done (chip-level)"],
     ["Reliability", "Aging: HCI, NBTI, TDDB", "Timing met at end of life (e.g. 10 years)", "Not done"],
     ["Reliability", "Self-heating / thermal", "Junction temperature within limits", "Not done"],
     ["Test", "Scan insertion + ATPG", "Stuck-at coverage >= 95% (often >= 98%), transition faults", "Not done (deferred)"],
     ["Test", "Memory BIST, IDDQ, boundary scan", "As required by product", "n/a / not done"],
     ["Signoff", "Foundry-certified signoff (Calibre-class)", "Foundry tape-out checklist accepted", "Not done"],
     ["Signoff", "Reproducibility + data integrity", "Rebuild from sources matches; files hashed", "Done (clean container)"],
     ["Silicon", "Wafer sort, characterization (shmoo), yield", "Functional at spec V/F/T; yield target met", "Not applicable yet (no silicon)"],
     ["Silicon", "Qualification (e.g. JEDEC JESD47: HTOL, ESD, LU)", "Passes stress tests on sample lots", "Not applicable yet (no silicon)"]]
s.append(KeepTogether([table(C, [19, 50, 66, 41]),
P("Table 8. Production tape-out checks and the status of this work. Project targets (coverage, mutation) are S2S's "
           "own; other criteria are typical industry values.", cap)]))

s.append(P("6. Discussion and limitations", h1))
s.append(P(
    "<b>What is established.</b> For five blocks, the open-source flow driven by agents produced layouts that pass the hard "
    "signoff checks of an open SKY130 shuttle, with independent re-checks (two DRC engines, independent STA that must agree with "
    "the flow's own STA, and formal equivalence on the final netlist). Every number above is reproducible from the package. "
    "<b>What is estimated.</b> Power is vector-less at 20% input activity, so it is an order-of-magnitude figure, not a "
    "guarantee. IR drop is static only. "
    "<b>What is not established.</b> EM, dynamic IR, SI/crosstalk, OCV derates, reliability, DFT test coverage and foundry-"
    "certified decks were not run; no silicon exists, so nothing here proves working parts. "
    "<b>Margins worth noting.</b> sync_fifo's setup slack at the slow corner (+0.243 ns) and the 0.10-0.14 ns hold margins of four blocks at the "
    "fast corner are positive but small; they would be the first to fail under OCV derates. Input and output delays in the SDC "
    "are default assumptions (30% of the period) pending a real system specification, and the slack figures depend on them. "
    "spi_master's clock-tree fanout (11-17 per leaf buffer) is accepted only under an explicit clock-net rule; the installed "
    "TritonCTS builds this tree with an average of 13 sinks per leaf buffer, and no in-range parameter reduced it."))

s.append(P("7. Conclusion and next steps", h1))
s.append(P(
    "All five blocks reached a signed GDSII with 0 DRC violations (Magic and KLayout), full LVS match, 0 antenna violations and "
    "positive setup and hold slack at nine corners, at 146.6 uW-5.75 mW estimated power and at most 1.37 mV static IR drop. "
    "The Phase 0 gate is a qualified pass. Phase 1 adds: static and dynamic IR plus electromigration analysis (OpenROAD), scan "
    "insertion and ATPG with measured fault coverage (OpenROAD DFT + Fault), an artifact hash/provenance check, and a first "
    "processor-class design (RV32I core) taken to the same signoff."))

s.append(P("Appendix A. Data and reproducibility", h1))
rows = [["Block", "Run", "P&amp;R iteration", "GDS size (bytes)", "GDS SHA-256"]]
for d in N:
    v = D[d]
    rows.append([d, v["run"], v["iteration"], f"{v['gds_bytes']:,}", v["gds_sha256"]])
s.append(KeepTogether([table(rows, [17, 50, 15, 18, 76]),
P("Table A1. Signed layouts. Each package (docs/milestones/m0.7-evidence/&lt;block&gt;/&lt;run&gt;/tapeout/) holds "
           "MANIFEST.sha256 over every file and reproduce.sh, which re-runs DRC, LVS and the checks in a network-isolated "
           "container. Tool versions: OpenLane 2.3.10, OpenSTA 2.6.0; full versions in each package's versions.lock.", cap)]))
s.append(P(
    "<b>Source of each figure.</b> Implementation, routing, DRV and PDN counts: OpenLane final/metrics.json of the iteration "
    "whose GDS hash equals the packaged GDS. Timing: reports/sta_signoff.json (S2S OpenSTA, 9 corners). Power: "
    "reports/power_report.json. IR: reports/ir_report.json. Physical verification: reports/pv_signoff.json. Resistance and "
    "capacitance: sums over the packaged tapeout/spef/{min,nom,max}/*.spef. DFM: reports/dfm_scorecard.json. Gate: "
    "tapeout/reports/tapeout_readiness.json.", small))


def footer(c, doc):
    c.saveState(); c.setFont("Times-Roman", 8)
    c.drawString(18 * mm, 10 * mm, "S2S Phase 0 - signoff results on open SKY130 - pre-silicon")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}"); c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=16 * mm, bottomMargin=17 * mm,
                        title="Agent-Driven RTL-to-GDSII on Open SKY130: Phase 0 Signoff Results",
                        author="S2S project, Goutham Labs", subject="Phase 0 results: power, resistance, timing, signoff")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print("built", OUT)
