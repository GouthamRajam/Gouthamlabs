"""Builds docs/reports/S2S_status_report_2026-10-05.pdf (full status, success and failure report)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

OUT = Path(__file__).with_name("S2S_status_report_2026-10-05.pdf")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceBefore=10, spaceAfter=6,
                    textColor=colors.HexColor("#1F3A5F"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#1F3A5F"))
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=10.5, spaceBefore=6, spaceAfter=2)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.2, leading=12.2, alignment=TA_LEFT, spaceAfter=4)
SM = ParagraphStyle("SM", parent=B, fontSize=8.2, leading=10.4, spaceAfter=0)
BUL = ParagraphStyle("BUL", parent=B, leftIndent=12, bulletIndent=2, spaceAfter=2)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=22, textColor=colors.HexColor("#1F3A5F"))
BOX = ParagraphStyle("BOX", parent=B, backColor=colors.HexColor("#FFF4E5"), borderColor=colors.HexColor("#E0A040"),
                     borderWidth=0.6, borderPadding=5, spaceBefore=4, spaceAfter=8)
OKBOX = ParagraphStyle("OKBOX", parent=BOX, backColor=colors.HexColor("#EAF6EC"), borderColor=colors.HexColor("#5AA469"))

story = []


def h1(t): story.append(Paragraph(t, H1))
def h2(t): story.append(Paragraph(t, H2))
def h3(t): story.append(Paragraph(t, H3))
def p(t, st=B): story.append(Paragraph(t, st))
def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText="-"))
def box(t, ok=False): story.append(Paragraph(t, OKBOX if ok else BOX))


def table(rows, widths, head=True, zebra=True):
    data = [[Paragraph(str(c), SM) for c in r] for r in rows]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B7C3")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE4EF")))
    if zebra:
        for i in range(1 if head else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F5F7FA")))
    t.setStyle(TableStyle(st))
    story.append(t)
    story.append(Spacer(1, 6))


# ---------------------------------------------------------------- title
story.append(Spacer(1, 30 * mm))
story.append(Paragraph("S2S - Spec-to-Silicon", TITLE))
story.append(Paragraph("Full status report: successes, failures, where it is stuck and why", H2))
story.append(Spacer(1, 6))
p("Report date: 5 October 2026 (UTC, about 15:40). Branch: <b>claude/tender-davinci-2r4q38</b> "
  "(repository GouthamRajam/Gouthamlabs). Phase 0: open-source tools and the open SkyWater SKY130 PDK only.")
p("Goal of this round (CEO instruction): take all five designs - counter8, alu8, sync_fifo, uart, spi_master - "
  "through M0.6 (verification) and M0.7 (physical design to GDSII), in parallel within 4 CPU cores, with every "
  "pass/fail verdict decided by a real tool run, no weakened checks, no waivers, and a timed-out simulation never "
  "counted as a caught bug.")
story.append(Spacer(1, 8))
table([["Design", "Verification (M0.6)", "Physical (M0.7)", "GDSII", "Verdict"],
       ["counter8", "PASSED", "PASSED: DRC 0, LVS match, timing met", "PRODUCED", "SUCCESS"],
       ["alu8", "PASSED (mutation 20/20 = 100%)", "PASSED: DRC 0, LVS match, timing met, GLS 25/25", "PRODUCED", "SUCCESS"],
       ["sync_fifo", "PASSED", "BLOCKED at place and route after 9 iterations (3 clock-buffer max-fanout violations "
        "in the best run)", "not produced", "FAILED (blocked, needs decision)"],
       ["uart", "NOT PASSED: mutation stuck at 14/20 = 70% (target 85%) six runs in a row", "not started",
        "not produced", "FAILED so far (investigation running)"],
       ["spi_master", "NOT PASSED yet: regression 120/120 OK, formal proof could not close; new method running now",
        "not started", "not produced", "IN PROGRESS"]],
      [24, 45, 55, 20, 30])
box("<b>Bottom line.</b> 2 of 5 designs reached GDSII cleanly (counter8, alu8). The other three are stuck on three "
    "different, specific problems: (1) sync_fifo - the clock tree violates the SDC max-fanout limit and none of the "
    "allowed tuning knobs fixes it; (2) uart - the test suite catches 14 of 20 injected bugs and has not moved in six "
    "rounds, probably because several of the 6 'missed' bugs cannot be caught by any test; (3) spi_master - the "
    "formal proof method (k-induction) cannot close on its clock-timing properties. None of these was hidden or "
    "waived; each is described in detail in Part 3, with what was tried and what you could research.")
story.append(PageBreak())

# ---------------------------------------------------------------- contents
h1("Contents")
for line in ["Part 1 - What the system is and how it was run", "Part 2 - Success report (counter8, alu8)",
             "Part 3 - Failure report, design by design (sync_fifo, uart, spi_master)",
             "Part 4 - Infrastructure and process failures (restarts, my own mistakes, limits)",
             "Part 5 - Everything that was changed (code and decisions)",
             "Part 6 - What I am doing right now",
             "Part 7 - Where you can help: research questions and decisions",
             "Appendix - Key files, commands and identifiers"]:
    p(line)
story.append(PageBreak())

# ---------------------------------------------------------------- part 1
h1("Part 1 - What the system is and how it was run")
h2("1.1 The S2S pipeline")
p("S2S takes a written specification to a tape-out-ready GDSII layout using a team of AI 'engineer' agents "
  "(Atlas, Mason, Ada, Theo, Rex, Myra, Euclid, Dex, Sienna, Grid, Orion, Tick, Sentinel, Proof, ...) coordinated "
  "by a Postgres-backed orchestrator. Every check is decided by a real open-source tool, never by a model:")
table([["Stage", "What happens", "Real tools"],
       ["M0.5 spec / arch / RTL", "Spec, architecture and Verilog RTL written by agents", "Verilator lint, Yosys"],
       ["M0.6 verification", "cocotb regression on 2 simulators x 3 seeds, coverage, formal properties (SymbiYosys), "
        "mutation testing (20 injected bugs, target >= 85% caught), debug loop (Dex triages, owners fix)",
        "Verilator, Icarus, cocotb, SymbiYosys (yices, ABC), Yosys"],
       ["G2 gate", "Human/CEO gate: verification closed, RTL frozen", "-"],
       ["M0.7 physical", "Constraints (SDC), synthesis + equivalence, DFT plan, floorplan, placement, clock tree, "
        "routing (Orion iterates within config/pnr_ranges.yaml), signoff (DRC, LVS, STA all corners, IR drop), "
        "GDSII package", "OpenLane 2 (Yosys, OpenROAD), Magic, KLayout, Netgen, eqy"]],
      [33, 92, 45])
h2("1.2 How this round was run")
bullets([
    "<b>No API usage (CEO decision).</b> Every agent model call goes through the 'coding-agent bridge': the orchestrator "
    "writes a request file and a coding-agent subagent answers it; the answer is schema-checked. Model "
    "choice: Opus for RTL/test/formal/debug work, Sonnet for routine reviews.",
    "<b>Parallel within 4 cores.</b> A machine-wide pool of 4 tool slots (OpenLane takes 2). A tool's timeout only "
    "starts when it gets a slot, so waiting can never cause a timeout.",
    "<b>Honest verdicts.</b> A mutant whose simulation times out is retried at 2x the limit; if it times out again it "
    "counts as NOT caught. No check was weakened and no waiver was added at any point.",
    "<b>Environment.</b> A cloud container (4 cores, ~252 GB disk of which only ~4-8 GB was free), Docker for the EDA "
    "image, Postgres + Redis, the S2S API/web dashboard, and a live mirror to your local dashboard through ngrok.",
])
story.append(PageBreak())

# ---------------------------------------------------------------- part 2
h1("Part 2 - Success report")
h2("2.1 counter8 (8-bit counter) - GDSII produced")
table([["Check", "Result"],
       ["Verification (M0.6)", "Passed: regression, coverage, formal; mutation 20/20 (100%)"],
       ["Synthesis + equivalence", "Passed"],
       ["DRC (Magic / KLayout)", "0 / 0 violations"],
       ["LVS (Netgen)", "Match"],
       ["Static timing, worst corner", "Setup slack +2.013 ns, hold slack +0.114 ns"],
       ["DFM findings", "0 high, 2 medium, 5 low"],
       ["Readiness score", "95.3% (A) / 64.1% (B)"],
       ["Evidence", "docs/milestones/m0.7-evidence/counter8 (GDSII, reports, 3D layout), commit 71700ff"]],
      [55, 115])
h2("2.2 alu8 (8-bit ALU) - GDSII produced")
table([["Check", "Result"],
       ["Mutation testing", "20/20 injected bugs caught (100%), 0 timeouts"],
       ["DRC", "0 / 0"], ["LVS", "Match"],
       ["Static timing, worst corner", "Setup +3.276 ns, hold +0.420 ns"],
       ["Gate-level simulation", "25/25 passed"], ["Reproducibility re-run", "PASS"],
       ["Signoff checklist (B.9)", "16/16"], ["Readiness score", "95.3% (A) / 64.1% (B)"],
       ["Evidence", "docs/milestones/m0.7-evidence/alu8, commit f23364c"]],
      [55, 115])
p("A bug found and fixed on the way: the functional-coverage evaluator evaluated 'and/or' eagerly, which crashed on "
  "alu8 with 'negative shift count'; it now short-circuits like Python (commit 5b486fd).")
h2("2.3 Partial successes in the failing designs")
bullets([
    "<b>sync_fifo</b> passed verification (mutation 100%), passed synthesis with DELAY 4 (pre-layout slack +0.182 ns), "
    "passed equivalence (562/562 points, Yosys LEC fallback), DFT and floorplan. Its best route (iteration 8) had 0 "
    "routing DRC errors, 0 antenna violations, 0 disconnected pins, timing met at all 9 corners (worst setup +0.203 ns, "
    "hold +0.135 ns), clock skew 0.059 ns - everything except 3 max-fanout violations.",
    "<b>spi_master</b> passes its regression (120/120 runs, line coverage 98.2%, toggle 98.0%) and a bounded formal "
    "check to depth 160; 9 of its 12 formal properties have now been proven unbounded (scratch run, Part 3.3).",
    "<b>uart</b> passes its regression and formal (5 meaningful properties proven); only the mutation score is short.",
])
story.append(PageBreak())

# ---------------------------------------------------------------- part 3
h1("Part 3 - Failure report, design by design")

# ---- sync_fifo
h2("3.1 sync_fifo - BLOCKED at place and route")
h3("What the failure is")
p("The router never produced a fully clean layout. The last remaining violation is <b>max fanout on the clock tree</b>: "
  "the reviewed SDC sets <font face='Courier'>set_max_fanout 10</font>, and in the best run three top-level clock "
  "buffers drive 11-12 loads. Earlier iterations also had antenna violations (long metal-1 wires), which were finally "
  "cleared in iteration 8.")
h3("Timeline of all place-and-route iterations")
table([["It.", "Settings (only what changed)", "Result", "Note"],
       ["1", "util 45, density 55, max-fanout target 10, synth DELAY 4", "antenna 3, fanout 39 (later: placement failed GPL-0302)", "density below cell utilization"],
       ["2", "util 40, density 65", "antenna 2, fanout 34", ""],
       ["3", "max-fanout target 8", "antenna 3, fanout 35", "resizer target did not touch clock nets"],
       ["4", "CTS cluster 10, antenna repair iters 5 (new knobs, CEO option A)", "antenna 3, fanout 5", "cluster size cut fanout 35 -> 5"],
       ["5", "CTS cluster 8, antenna margin 20%", "antenna 4, fanout 0", "re-run hit a resume bug (GPL-0302), fixed later"],
       ["6", "util 35, antenna iters 10", "antenna 1, fanout 2", ""],
       ["7", "antenna margin 30%, max-fanout target 6", "antenna 3, fanout 2", ""],
       ["8 (first try)", "util 30, antenna iters 15", "INVALID", "my error: two runs at once on the same folder"],
       ["8 (clean re-run)", "util 30, antenna iters 15", "antenna 0, fanout 3 (clock buffers 12/11/11 vs 10)", "BEST RESULT"],
       ["9 (extra, CEO)", "CTS cluster 6 (only change)", "antenna 2, fanout 5 (clock buffers 16/16/12/12/12)", "worse; stopped"]],
      [16, 52, 60, 42])
h3("Root cause analysis")
bullets([
    "The violating cells are named <font face='Courier'>clkbuf_3_*__f_clk</font>: the 8 <b>level-3 buffers of the clock "
    "H-tree</b>, which drive the leaf (cluster) buffers. They are NOT leaf buffers. I misread this before iteration 9.",
    "CTS_SINK_CLUSTERING_SIZE controls how many flip-flops each LEAF buffer drives. Making it smaller creates MORE leaf "
    "buffers, which RAISES the fanout of the level-3 buffers (iteration 9: 12 -> 16). So the only clock knob in the "
    "approved set pushes the wrong way once the leaves are fixed.",
    "MAX_FANOUT_CONSTRAINT (the resizer's target) does not repair clock nets; OpenROAD's repair_design skips them. "
    "So no approved knob can fix fanout on the upper clock-tree levels.",
    "Antenna violations were driven by long metal-1 routes; lowering utilization to 30% (spreading cells) plus more "
    "repair passes cleared them, but the result is sensitive (it bounced 1 -> 3 -> 0 -> 2 between iterations).",
])
h3("What was tried")
bullets(["Synthesis strategy DELAY 4 (CEO) to meet timing; equivalence closed with a new Yosys LEC fallback.",
         "All 6 approved knobs: core utilization 45 -> 30, placement density 55 -> 65, resizer fanout target 10 -> 6, "
         "CTS cluster size 25 -> 6, antenna repair iterations 3 -> 15, antenna margin 10 -> 30%.",
         "Operator guidance to Orion (CEO option A), tool-run budget 16 -> 32 -> 40 -> 44, one extra iteration (9).",
         "Bug fixes on the way: OpenLane resume bug (re-running a stage resumed from the routed state, commit c4ad50f); "
         "fork kept state timestamps (aea81be); iteration start-stage recorded (04564a0)."])
h3("What I could not do (and why)")
bullets(["Change the SDC max-fanout limit or exclude clock nets from it - that would loosen a reviewed constraint "
         "(hard rule 2). Many real flows do not apply max_fanout to clock nets (the clock tree is checked by skew and "
         "slew instead), but that is a constraint-policy decision for you, not for me.",
         "Use OpenLane/OpenROAD CTS settings outside the approved list (for example the CTS buffer/branching "
         "controls) - they are not in config/pnr_ranges.yaml, so using them needs your approval.",
         "Waive the 3 violations - not allowed."])
h3("Options for you to research and decide")
bullets(["<b>A. Clock-tree structure knobs</b>: research OpenROAD clock_tree_synthesis options that bound the branching "
         "of non-leaf buffers (e.g. CTS distance between buffers, maximum wire length, buffer list / stronger buffers, "
         "'balance levels', cluster diameter, sink buffer max cap). Adding one to pnr_ranges.yaml is a decision.",
         "<b>B. Constraint policy</b>: decide whether set_max_fanout should apply to the clock network at all "
         "(standard practice varies; clock nets are often exempt and governed by CTS skew/slew/transition targets).",
         "<b>C. Larger cluster size + other leaf control</b>: iteration 5 (cluster 8) had fanout 0; the problem came back "
         "when antenna fixes added diodes/changed placement. A combination search (cluster 8-10 with util 30) was not run.",
         "<b>D. Accept as blocked</b> and report sync_fifo as not tape-out ready."])

# ---- uart
h2("3.2 uart - verification stuck at 70% mutation score")
h3("What the failure is")
p("Mutation testing injects 20 bugs into copies of the RTL and runs the full regression on each; at least 85% must be "
  "caught. uart catches <b>14/20 (70%)</b>, with 0 timeouts, and the number has been <b>identical six times</b>:")
table([["Run (UTC)", "Result", "Since the previous run"],
       ["4 Oct 15:16", "14/20 (70%)", "first measurement (CEO: reject at 70%, then fix)"],
       ["4 Oct 17:35", "14/20 (70%)", "Theo (test agent) round 1"],
       ["4 Oct 20:41", "14/20 (70%)", "Theo round 2"],
       ["4 Oct 23:31", "14/20 (70%)", "handover improved: module + per-bug-type test hints"],
       ["5 Oct 05:45", "14/20 (70%)", "Theo round 3"],
       ["5 Oct 15:09", "14/20 (70%)", "Theo round 4 (tests written 05:55, confirmed in the testbench)"]],
      [30, 30, 110])
p("Same 6 survivors every time. By type: wrong_operator 3/4, off_by_one 2/4, stuck_bit 4/4, <b>missing_reset 0/3</b>, "
  "swapped_condition 3/3, dropped_handshake 2/2.")
table([["Missed mutant", "Change", "Why it may be uncatchable"],
       ["uart_tx_L64_missing_reset_3", "reset of bit_idx_q removed (tx)", "bit index is probably reloaded at every frame start"],
       ["uart_rx_L67_missing_reset_3", "reset of bit_idx_q removed (rx)", "same, receiver side"],
       ["uart_rx_L65_missing_reset_3", "reset of tick_cnt_q removed (rx)", "tick counter probably restarted on start-bit detection"],
       ["uart_tx_L62_wrong_operator_1", "tick_cnt_q reset value 0 -> ~0 (tx)", "counter may be reloaded before it is used"],
       ["uart_tx_L34_off_by_one_1", "localparam PH_ONE 1 -> 2", "may only shift an internal phase that is not visible at the pins"],
       ["uart_rx_L69_off_by_one_2", "prev_q reset 1 -> 0", "edge detector start value; invisible while the line idles high"]],
      [52, 50, 68])
h3("Root cause hypothesis")
p("These are probably <b>equivalent mutants</b>: changes that alter internal state but can never change any output, "
  "so no test - however good - can catch them. Myra's screen should remove those, but it only searches 25 clock "
  "cycles from an all-zero state and labels all 6 'unknown' (undecided), so they stay in and count as 'missed'. "
  "A UART frame is ~160+ clock cycles at the smallest divisor, so a 25-step search cannot see a whole frame. "
  "If confirmed, the real catchable score would be 14/14 or 14/(20 - k).")
h3("What was tried")
bullets(["Four rounds of Theo test improvement (all applied, none moved the score).",
         "Richer handover to Theo: missed bug's module and test hints per bug type (e.g. reset in the middle of "
         "activity); Theo still never sees the RTL (independence rule).",
         "Regression timeout raised to 5400 s; mutant timeouts retried at 2x and never counted as catches.",
         "Mutation verdict cache (commit 10b2f67) so a container restart no longer throws away 2 hours of simulation "
         "(restarts did this 3 times).",
         "NOW RUNNING: an unbounded equivalence proof (miter + ABC PDR) for each of the 6 survivors, plus one caught "
         "mutant as a control that must come out 'not equivalent'. Result so far: the first two (tx bit_idx_q reset "
         "removed, tx tick_cnt_q reset inverted) TIMED OUT at the 30-minute limit with NO conclusion - neither "
         "'equivalent' nor 'different' was proven. The other 4 and the control are still running. The uart miter is "
         "too hard for PDR within 30 minutes; a smarter method (e.g. register-correspondence equivalence, or a "
         "long bounded search for a distinguishing input) is likely needed."])
h3("What I could not do")
bullets(["Lower the 85% target or drop mutants by hand - not allowed.",
         "Prove equivalence quickly: the uart miter is large (2 copies of a design with 16-bit baud divider "
         "counters); PDR is slow on it. Results pending."])
h3("Options for you to research and decide")
bullets(["<b>A. Equivalent-mutant handling</b>: standard mutation-testing practice excludes proven-equivalent mutants. "
         "Decide whether a stronger screen (unbounded PDR / k-induction with longer depth, or sequential equivalence "
         "with register correspondence) may replace undecided mutants.",
         "<b>B. Mutant generation</b>: should 'missing reset' mutants be generated for registers that are always "
         "re-initialised before use? Industrial tools (e.g. Certitude-style) classify such faults as non-activatable.",
         "<b>C. Reset-in-the-middle tests</b>: if any of the 6 is NOT equivalent, the PDR counterexample gives the exact "
         "input sequence; Theo can then target it."])

# ---- spi_master
h2("3.3 spi_master - formal proof could not close")
h3("What the failure is")
p("M0.6 requires at least 3 'meaningful' formal properties proven unbounded (proof passed, cover reached, fails on a "
  "free stub). spi_master has 12 port-level properties. With k-induction (the original method) <b>0</b> were proven:")
bullets(["At depth 30 (global default) induction could not close; one SPI transfer is 73 cycles.",
         "CEO option A raised spi_master's depth to 160. The base case then needs ~1 minute per step "
         "(40-minute limit reached at step 110 the first time). Bounded check to 160 now passes for all 12.",
         "Induction still fails: a counterexample from an arbitrary (possibly unreachable) start state. The formal agent "
         "(Euclid) showed why for the 3 SCK-timing properties: they can only see pins, the clock divider can be up to "
         "65535, so a 160-cycle window may contain fewer than 2 SCK edges and nothing ties the property to the hidden "
         "divider counter. Making them inductive would need internal signals (forbidden: port-level only) or a "
         "spec-less assumption (forbidden)."])
h3("A harness bug found")
p("The formal harness counted an induction-step counterexample (and the summary line repeating it) as a real design "
  "failure. That sent the debug loop after non-bugs twice (mosi_zero_when_idle, sck_edges_max). Fixed in 26ded26: only "
  "base-case / bounded / PDR engine lines count as failures (tests use real logs).")
h3("What was tried")
bullets(["Depth 30 -> 160; formal timeout scaled with depth.",
         "Property fixes by Euclid (one real property fix: mosi_zero_when_idle).",
         "Joint PDR (ABC IC3) on all 12 properties: 30 min and 2 h runs - did not finish (stuck on the SCK properties).",
         "<b>Per-property PDR</b> (CEO-approved): 9 of 12 properties proven alone in about 1 second each; negative "
         "controls with RTL broken on purpose FAIL (reset_values at frame 2, done_implies_busy at frame 88), so the "
         "assumptions are not vacuous. Adopted into the flow (26ded26, b18ad24); pass rule unchanged.",
         "NOW RUNNING: spi_master verification with the new method (regression passed 120/120 at 13:53; joint proof at "
         "depth 160 then per-property PDR)."])
h3("Not done")
bullets(["The spec's REQ-025 asks for a bounded check from reset to depth >= 400 for the SCK properties. Not run: the "
         "depth-160 bounded run already takes ~40 minutes. Those 3 properties stay 'bounded to 160', not counted."])
h3("Options for you to research")
bullets(["Whether a depth-400 bounded check is worth hours of CPU, or whether a smaller clk_div range in a separate "
         "formal configuration (spec-justified) is acceptable for the SCK properties.",
         "Whether port-level-only formal is the right rule for timing properties (white-box helper invariants are "
         "standard in industry but break the test/RTL independence rule S2S uses)."])
story.append(PageBreak())

# ---------------------------------------------------------------- part 4
h1("Part 4 - Infrastructure and process failures")
table([["Problem", "Impact", "What was done"],
       ["Container restarts (at least 6 in this round; Docker, DB and all services down each time)",
        "Lost in-progress work each time: uart's 2-hour mutation step lost 3 times; spi_master formal, sync_fifo runs "
        "interrupted", "Recovery script (start_all.py); stale containerd pid fix; mutation verdict cache; tasks resume "
        "from checkpoints"],
       ["Disk nearly full (4-8 GB free; one 'No space left' crash)", "A uart mutation run crashed", "Compressed large "
        "waveforms, deleted scratch runs; currently ~4.3 GB free"],
       ["API key leaked into the transcript (my error, early in the project)", "Security", "Log deleted; processes "
        "started without the key; you were asked to revoke it (please confirm)"],
       ["Two copies of sync_fifo iteration 8 ran at once (my error: I marked an outside-run task 'running' to clear a "
        "dashboard flag; the stall watchdog reassigned it)", "Iteration 8 result invalid; ~30 min lost", "Recorded as "
        "invalid; clean re-run; rule: outside-run tasks stay 'paused'"],
       ["OpenLane resume bug (re-running placement resumed from the routed state)", "GPL-0302 failure, wasted iteration",
        "Fixed: clear a stage's and later steps before re-running (c4ad50f)"],
       ["Budget stops: tool-run budget (sync_fifo 16/32/40), token budgets (spi_master 400k, uart 1M), spend cap $8 "
        "(uart, mostly old API spend)", "Tasks paused for approval several times", "Raised per CEO decisions; token "
        "limits removed for bridge use; cap $20 compute backstop"],
       ["Stall watchdog fires every 15 min during long simulations", "Noise: 'needs a human' on healthy runs",
        "Explained; not changed"],
       ["Bridge requests orphaned by restarts", "Some model calls lost", "Ignored safely; tasks re-ask after resume"],
       ["My own misreading (sync_fifo it. 9): level-3 clock buffers taken for leaf buffers", "One wasted iteration",
        "Analysis corrected in this report"]],
      [55, 50, 65])
story.append(PageBreak())

# ---------------------------------------------------------------- part 5
h1("Part 5 - Everything that was changed")
table([["Commit", "Change"],
       ["7bf7dbb", "Model calls go to the coding-agent bridge by default; no API usage"],
       ["4ad31d0", "Machine-wide tool slots; mutation timeouts never count as catches; synth_strategy input; clearer missed-mutant handover"],
       ["fe35a64", "Equivalence: Yosys LEC fallback when eqy cannot prove (must prove every point)"],
       ["aea81be", "OpenLane fork keeps state-file timestamps"],
       ["5b486fd", "Functional coverage: and/or short-circuit (alu8 crash)"],
       ["b5ba04f", "Orion repair knobs: CTS cluster size, antenna repair iterations and margin (in pnr_ranges.yaml)"],
       ["f4985a1", "Per-design formal depth minimum (spi_master 160), depth-scaled formal timeout"],
       ["a8dcaf7", "No line-ending conversion for tape-out evidence and snapshots"],
       ["581184d", "Live mirror: POST /mirror + relay, so your local dashboard shows the cloud run in real time"],
       ["95f9101", "Orion reads recorded operator guidance"],
       ["c4ad50f", "OpenLane resume fix"],
       ["04564a0", "Place-and-route loop resumes an iteration from its recorded start stage"],
       ["305f7f3", "Spend cap per design $8 -> $20 (compute backstop)"],
       ["10b2f67", "Mutation verdict cache (restart-safe)"],
       ["26ded26, b18ad24", "Formal: per-property PDR when induction does not close; induction-step counterexamples are not failures; proof-line guard"],
       ["71700ff, f23364c", "counter8 and alu8 tape-out packages"],
       ["docs/DECISIONS.md", "Every CEO decision and every rule change recorded"]],
      [32, 138])
p("Unit tests: 227 passed, 1 skipped on the full suite (run after the resume fix); new tests for each change above.")

# ---------------------------------------------------------------- part 6
h1("Part 6 - What I am doing right now")
bullets(["<b>spi_master</b>: verification running with the new formal method (joint proof at depth 160, then per-property "
         "PDR). If >= 3 meaningful properties are proven it goes to G2 and then automatically to M0.7.",
         "<b>uart</b>: (1) its verification task is re-running mutation with Theo's latest tests (token limit removed per "
         "your no-limits rule); (2) a scratch unbounded equivalence proof of the 6 missed mutants (+1 control) is "
         "running - this decides whether the 70% is a test problem or an equivalent-mutant problem.",
         "<b>sync_fifo</b>: stopped, waiting for your decision (Part 3.1 options).",
         "Answering every bridge model call, re-arming monitors, recovering after container restarts."])

# ---------------------------------------------------------------- part 7
h1("Part 7 - Where you can help")
h2("Decisions only you can make")
table([["#", "Decision", "Why it matters"],
       ["1", "sync_fifo: allow a new clock-tree knob, or exempt the clock network from set_max_fanout, or accept blocked",
        "No approved knob can fix the 3 violations"],
       ["2", "uart: may mutants proven equivalent by an unbounded check be replaced (and undecided ones too, with a "
        "longer bounded search)?", "Decides whether 70% is real"],
       ["3", "spi_master: run the REQ-025 depth-400 bounded check (hours), or drop it?", "Spec compliance of the SCK properties"],
       ["4", "Revoke the leaked API key (if not done)", "Security"],
       ["5", "Container stability: the cloud container restarted ~6 times; a more stable/larger environment (more "
        "disk, more cores) would cut lost work", "Every restart costs 0.5-2 h"]],
      [8, 92, 70])
h2("Research questions")
bullets(["OpenROAD CTS: which clock_tree_synthesis options limit the fanout of non-leaf (trunk / H-tree) buffers in "
         "OpenLane 2 for sky130_fd_sc_hd? Is set_max_fanout normally applied to clock nets in sky130 flows?",
         "Mutation testing on RTL: how do industrial and academic flows treat equivalent / non-activatable mutants "
         "(e.g. removed resets of registers always reloaded before use)? Is excluding proven-equivalent mutants and "
         "counting only 'killable' ones the accepted metric?",
         "Formal on counters with large divisors: accepted practice for proving SCK-timing properties of an SPI master "
         "(helper invariants, white-box properties, abstraction of the divider, or bounded proofs only).",
         "Is the S2S rule 'port-level properties only' (for test/RTL independence) too strict for timing properties?"])

# ---------------------------------------------------------------- appendix
h1("Appendix - Key files, commands and identifiers")
table([["Item", "Where"],
       ["Decisions log", "docs/DECISIONS.md"],
       ["Rules for this project", "PROJECT_RULES.md, CONTEXT.md, PHASE_GATES.md"],
       ["Approved P&amp;R knobs and ranges", "config/pnr_ranges.yaml"],
       ["Coverage / formal targets", "config/coverage_targets.yaml (formal_min_depth_by_design)"],
       ["Spend caps / model provider", "config/finance.yaml"],
       ["Mutation harness", "backend/s2s/verify/mutation_run.py"],
       ["Formal harness", "backend/s2s/verify/formal.py"],
       ["P&amp;R flow and Orion loop", "backend/s2s/physical/flow.py, backend/s2s/agents/m07.py"],
       ["sync_fifo M0.7 run", "run_01M43MDNVKWCHEQ0GGHPJFT602 (reports/pnr_iterations.json, pnr/runs/it1..it9)"],
       ["uart M0.6 run", "run_01M42GYPBFRPKEC4BCQQVVD6A3 (reports/mutation_1.json)"],
       ["spi_master M0.6 run", "run_01M443MCHKW7P4HJ8RSESA9S2W (reports/formal_report.json)"],
       ["alu8 / counter8 evidence", "docs/milestones/m0.7-evidence/alu8, .../counter8"],
       ["Branch", "claude/tender-davinci-2r4q38"]],
      [55, 115])


def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.grey)
    c.drawString(15 * mm, 10 * mm, "S2S status report - 5 Oct 2026 - every result above comes from a real tool run")
    c.drawRightString(195 * mm, 10 * mm, f"Page {d.page}")
    c.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm,
                        bottomMargin=17 * mm, title="S2S status report", author="S2S")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
