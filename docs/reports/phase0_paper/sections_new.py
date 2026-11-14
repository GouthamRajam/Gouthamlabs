# Extra sections for build.py (exec'd inside build.py's namespace). Numbers come from data.json, exec.json
# (orchestrator database), versions.lock and docs/DECISIONS.md; see README.
EX = json.load(open(f"{S}/exec.json"))


def sec_tools():
    out = []
    rows = [["Stage", "Tool", "Version", "What it did in this work"],
            ["Container", "s2s-eda image (OpenLane 2 base, pinned by digest)", "openlane2 2.3.10", "Every EDA tool below runs in this one pinned image; reproduce.sh re-runs checks in it with no network"],
            ["PDK", "SkyWater SKY130A via open_pdks / volare", "commit 0fe599b2", "Process rules, device models, sky130_fd_sc_hd cells, DRC/LVS decks"],
            ["Lint / elaboration", "Verilator, Yosys", "5.018, 0.46", "Lint, elaboration, latch and logic-loop checks on RTL"],
            ["Simulation", "Verilator, Icarus Verilog, cocotb", "5.018, 12.0, 1.9.2", "Regression on several seeds, cross-check simulator, gate-level simulation"],
            ["Formal", "SymbiYosys (sby), Yices, Z3, ABC PDR", "yosys-0.47, 2.6.4, 4.8.17", "Property proofs, cover traces, vacuity checks, equivalent-mutant proofs"],
            ["Equivalence", "eqy; Yosys equiv_* (LEC fallback)", "yosys-0.46", "RTL vs synthesized and RTL vs final routed netlist"],
            ["Synthesis", "Yosys + ABC (in OpenLane)", "0.46", "Gate-level netlist, synthesis strategy AREA/DELAY"],
            ["Floorplan, place, CTS, route", "OpenROAD (RePlAce, TritonCTS, TritonRoute)", "edf00dff", "Die/core, placement, clock tree, global and detailed routing, antenna repair"],
            ["Parasitics", "OpenROAD OpenRCX", "edf00dff", "SPEF extraction at min/nom/max RC"],
            ["Timing, power", "OpenSTA", "2.6.0", "9-corner setup/hold/DRV; report_power"],
            ["IR drop", "OpenROAD PSM", "edf00dff", "Static IR drop on VPWR/VGND"],
            ["DRC", "Magic; KLayout", "8.3.489; 0.29.4", "Two independent DRC runs on the streamed GDS; density deck"],
            ["LVS", "Magic extraction + Netgen", "8.3.489 + 1.5.278", "Layout vs schematic on the streamed GDS"],
            ["DFM", "KLayout scripts (S2S)", "0.29.4", "Near-minimum spacing, line ends, via redundancy, density windows"],
            ["Orchestration", "S2S orchestrator (Python), PostgreSQL 16, Redis 7", "this repo", "Tasks, checkpoints, checks, events, budgets, gates"],
            ["Agent reasoning", "Claude models via Claude Code bridge / API", "-", "Spec, architecture, RTL, tests, constraints, P&amp;R decisions, reports; never pass/fail"]]
    out.append(KeepTogether([P("3.1 Tools used", h2), table(rows, [24, 52, 28, 72]),
                             P("Table 3. Tools and versions (from each package's versions.lock). All are open source except the "
                               "language models, which write and decide but never mark a check passed.", cap)]))
    return out


def sec_teams():
    out = [P("3.2 How the work was executed: teams and agents", h2)]
    out.append(P(
        "The system is organised like a chip company. A human CEO and two human VPs own approval gates; 37 agent roles are "
        "grouped into divisions and teams, each with a lead agent, a manager or director that checks its work, and a fixed "
        "list of files it may read and write (a test writer, for example, may never read the RTL it tests). Work is broken "
        "into tasks run by a durable orchestrator; each task records checkpoints, heartbeats, budgets and every tool result "
        "as a check. A red-team reviewer (Sentinel) must approve constraints, specs and any change to tests; a trust agent "
        "(Proof) re-hashes and signs packages. Every agent action emits an event."))
    rows = [["Division / zone", "Teams (lead agent)", "Role in these five designs"],
            ["1 Architecture &amp; Specification (Juno)", "Spec (Iris), Micro-architecture (Kepler), Perf/Power modelling (Pascal), IP library (Ivy)", "Written spec with numbered requirements; block architecture and interfaces"],
            ["2A RTL Design (Reid)", "Datapath (Ada), Control/FSM (Ada-C), Interfaces (Ada-I), Low-power (Watt), Lint/CDC (Lumen)", "Verilog RTL per module; lint and elaboration"],
            ["2B Verification Build (Nadia)", "Test planning (Vera), Testbench (Theo), Reference models (Mira), Protocol checkers (Proto), Formal (Euclid)", "Test plan, cocotb testbenches, golden models, assertions and proofs"],
            ["2C Verification Closure (Rhea)", "Regression (Rex), Debug (Dex), Coverage (Cora), Mutation (Myra)", "Multi-seed regression, debug loops, coverage closure, injected-bug scoring"],
            ["3 Physical Implementation (Mason)", "Synthesis &amp; constraints (Sienna), DFT (Tess), Floorplan/PDN (Grid), Place &amp; route (Orion), Clock tree (Tick)", "SDC, netlist, floorplan, P&amp;R iterations with diagnosis, CTS reports, DFT plan"],
            ["4 Signoff &amp; Manufacturing (Sloane)", "Timing (Chronos), Physical verification (Calla), Power/IR (Volta), DFM (Fabian), Tape-out (Gideon), Trust (Proof)", "9-corner STA, DRC/LVS/antenna/density, power and IR, DFM, package, checklist, signing"],
            ["Cross-cutting", "Sentinel (critic), Sage (knowledge base)", "Reviews of specs, SDC and test changes; lessons from past failures"],
            ["Humans", "CEO; VP Front-End (G1, G2); VP Physical (G3, G4)", f"{EX['ceo_decisions']} recorded CEO decisions; G3/G4 auto-approved by policy when all checks passed (G4 stays a human decision before any real fabrication)"]]
    out.append(KeepTogether([table(rows, [40, 72, 64]),
                             P("Table 4. Organisation used (config/management.yaml). Agent names are role names, not people.", cap)]))
    rows = [["Block", "Runs", "Tasks", "Checks run", "Checks failed", "Events", "Agents active", "Model calls", "Model tokens (M)", "Tool CPU h", "Spend USD"]]
    for d in N:
        e = EX["designs"][d]
        rows.append([d, e["runs"], e["tasks"], e["checks"], e["failed"], f"{e['events']:,}", e["agents"], e["llm_calls"],
                     e["mtok"], e["cpu_h"], e["usd"]])
    out.append(KeepTogether([table(rows, [18, 10, 11, 14, 14, 14, 14, 14, 16, 13, 14]),
                             P("Table 5. Execution record per block over all its runs (spec through GDSII), from the orchestrator "
                               "database, queried on 2026-10-06, before the derated check and the sync_fifo design-change runs "
                               "of 2026-10-07 (not included). Spend includes early paid model calls; model calls through the Claude Code bridge are "
                               "metered at $0 and EDA compute at a nominal rate.", cap)]))
    out.append(P(
        "<b>Stage sequence per block.</b> spec -> architecture (G1) -> RTL -> test build -> verification: regression, coverage, "
        "formal, mutation (G2) -> synthesis + SDC (Sentinel review) -> DFT plan -> floorplan -> place &amp; route iterations -> "
        "signoff (G3) -> GDSII package, clean-container reproduction, checklist, signing (G4). A failed check stops the stage; "
        "the owning agent must diagnose the cause from tool facts before changing anything, a manager spot-checks 10% of work "
        "and 100% of anything touching tests, constraints or waivers, and three identical failures escalate."))
    return out


def sec_failures():
    out = [P("5.7 Failures encountered and how they were resolved", h2)]
    fc = EX["failed_by_stage"]
    out.append(P(
        f"Across the five blocks the orchestrator recorded {sum(EX['designs'][d]['checks'] for d in N):,} tool check results; "
        f"{sum(EX['designs'][d]['failed'] for d in N)} were failures, covering {sum(fc.values())} distinct checks (by stage: "
        f"{', '.join(f'{k.replace(chr(95), chr(32))} {v}' for k, v in fc.items())}; same 2026-10-06 query as Table 5). No failure "
        "was waived; the one relaxed rule is spi_master's clock-net fanout limit of 20, recorded as a CEO decision and printed as a "
        "condition on its result. Each failure was fixed at its cause and the check re-run, except sync_fifo's derated timing "
        "failure, which is still open at the physical-cleanup stage. Table 13 lists the significant ones with their numbers."))
    F = [["Block", "Stage", "What failed (numbers)", "Root cause found", "Fix", "Result after fix"],
         ["alu8", "synthesis", "SDC guard: clock 13.3333 ns vs spec 13.333333 ns (75 MHz)", "Constraint rounded the clock period", "SDC re-issued with the spec period; guard re-run", "Guard passed; setup +3.276 ns signed off"],
         ["counter8", "floorplan", "OpenROAD syntax error in the pin script; pins not placed on planned sides", "S2S regex accepted pin patterns (e.g. ^clk$) that OpenLane rejects", "Pin file now checked by OpenLane's own parser before floorplan", "All 21 pins on planned sides"],
         ["sync_fifo", "synthesis", "Pre-layout setup -1.545 ns at SS 100C", "Default AREA 0 strategy too slow for the read path", "Synthesis strategy DELAY 4 (+19% area), no constraint change", "+0.182 ns pre-layout; +0.243 ns signed off"],
         ["sync_fifo", "synthesis", "eqy partition errors (count/memory partitions)", "Tool limitation on this structure", "Independent Yosys sequential LEC fallback; must prove every point", "All points proven; changed RTL is rejected"],
         ["sync_fifo", "verification", "Functional bin cov_full_and_empty_never never hit; mutation: 1 distinct non-equivalent mutant", "Bin described an impossible state; mutation engine produced too few distinct mutants", "Bin moved to illegal-states list (proven by assertion); deterministic type-balanced mutation engine with equivalence screening", "Functional coverage 35/35; 20/20 injected bugs caught"],
         ["sync_fifo", "place &amp; route", "10 iterations; leaf clock buffers fanout 12/11/11 vs limit 10; antenna nets; detailed placement DPL-0036", "Clock flops spread too far per leaf; cluster size chosen by guess", "Recorded CTS experiments; cluster size 9 predicted by tree-level diagnosis", "0 fanout, 0 antenna, 0 DRC; setup +0.243 ns"],
         ["sync_fifo", "process", "Iteration 8 ran twice at once (invalid)", "Operator marked an outside-run task 'running'; watchdog re-assigned it", "Rule: outside runs stay 'paused'; iteration re-run once", "Invalid result kept on record; clean re-run used"],
         ["uart", "verification", "Mutation detection 14/20 = 70% (target 85%)", "Equivalent mutants counted as misses", "Prove-then-exclude: only an unbounded proof removes a mutant", "19/20 = 95%; 8 proven-equivalent mutants screened"],
         ["uart", "verification", "Anti-cheat: 3 flags (test loop shortened, 2 tests deleted)", "Testbench edit weakened tests", "Sentinel rejected; tests restored, flag sent to review", "anti_cheat_final passed"],
         ["uart", "synthesis", "Pre-layout setup -0.107 ns at SS (AREA 0)", "Area strategy too slow", "Sweep of 6 strategies; DELAY 0 chosen (+15% area)", "+3.54 ns pre-layout; +5.67 ns signed off"],
         ["uart", "synthesis", "LEC 105 proven / 19 unproven (TX FSM)", "Synthesis re-encoded the FSM to one-hot", "LEC reads synthesis FSM map (encfile), as industrial LEC tools do", "125/125 proven; 3 known-bad mutants still rejected"],
         ["uart", "signoff", "Max fanout 16 vs 10 on clock buffers; OpenLane reported 0", "OpenLane timing ran on an ideal clock", "Independent S2S OpenSTA DRV check every iteration", "Hidden violation found, then fixed"],
         ["uart", "signoff", "OpenLane vs S2S STA mismatch (capture clock 0 vs 0.94 ns)", "SDC comment contained the word propagated_clock, which disables OpenLane's clock propagation", "Guard forbids the word; comment-only SDC rewrite; re-run from synthesis", "0 mismatches; clock propagated"],
         ["uart", "place &amp; route", "Leaf clock fanout 11 after 6 CTS-knob experiments", "Flop spread, not clustering (125 sinks, H-tree stop at 15)", "Placement density 60% (in range)", "0 violators; DRC 0; hold +0.104 ns"],
         ["spi_master", "spec", "Sentinel: worked example (80 cycles) contradicts formula", "Spec arithmetic error", "Spec corrected before RTL", "Review passed"],
         ["spi_master", "verification", "$past outside clocked block; 2 assertion names missing; SCK properties not closing", "Formal harness and test-plan naming errors; hard proofs", "Fixed harness; plan names corrected via change request; per-property PDR", "9 properties proven unbounded; 3 bounded at depth 160 (not counted)"],
         ["spi_master", "synthesis", "LEC 95 proven / 8 unproven (rx_data[15:8])", "Synthesis merged two identical registers", "RTL side runs Yosys opt (same merge)", "103/103 proven; 4 known-bad mutants rejected"],
         ["spi_master", "place &amp; route", "8 leaf clock buffers at 11-17 loads vs 10", "TritonCTS stops the H-tree at &lt;=15 sinks; 104 sinks -> 8 leaves", "CEO decision: clock-net fanout rule 20 (data nets keep 10)", "Conditional pass (Section 5.6)"],
         ["all", "signoff", "Safety net flagged allowed clock-rule lines as failures", "Checker bug", "Narrow fix: only rule-allowed pins accepted", "9/9 corners pass on real data"],
         ["sync_fifo", "signoff (derated, what-if)", f"Setup {sg(WI_ORIG['setup']['5'])} ns at +/-5%, {sg(WI_ORIG['setup']['10'])} ns at +/-10% on the signed netlist", "Combinational read path to the rd_data port", "Design change #1: registered rd_data (full re-verification)", f"{sg(WI_C1['setup']['10'])} ns at +/-10%: worse, path now fully on-chip"],
         ["sync_fifo", "signoff (derated, what-if)", f"Change #1 still fails ({sg(WI_C1['setup']['10'])} ns)", "Path now fully on-chip: its cell and wire delay scales with the derate", "Design change #2: every read-mux select straight from flip-flops", f"{sg(WI_C2['setup']['10'])} / {sg(WI_C2['hold']['10'])} ns setup / hold at +/-10%"],
         ["sync_fifo", "place &amp; route (change #2)", f"it3: {C2['it3']['antenna_nets']} antenna net; it4 (heuristic diodes): instances {C2['it3']['instances']:,} -> {C2['it4']['instances']:,}, clock-buffer fanout up to {C2['it4']['max_clkbuf_fanout']:.0f}, {C2['it4']['slew_viol']} slew, {C2['it4']['cap_viol']} cap violations", "Global-route repair sees the gate tied to driver diffusion on met1 (allowed 2,736); the detailed route splits the net across layers (allowed 400); heuristic diodes land on clock nets", f"it5: diodes off, density 60%, margin 30% -> {C2['it5']['antenna_nets']} antenna nets on other input-buffer nets; stopped at 18/20 tool runs", "Not resolved: block FAIL; needs post-detailed-route antenna repair (Phase 1)"]]
    out.append(table(F, [15, 15, 40, 36, 38, 32]))
    out.append(P("Table 13. Significant failures, root causes and fixes (orchestrator check records and docs/DECISIONS.md; the "
                 "last three rows from the what-if logs and change #2's P&amp;R reports, see Appendix A). Every fix is covered by "
                 "a regression test in the repository.", cap))
    return out


FLOPS = {"counter8": 8, "alu8": 12, "sync_fifo": 531, "uart": 125, "spi_master": 104}  # sequential cells in final netlist
NAND2 = 3.7536  # um2, sky130_fd_sc_hd__nand2_1 (PDK liberty)


def sec_compare():
    out = [P("6. Comparison with published designs, products and process data", h1)]
    out.append(P(
        "No public chip is identical to these blocks, so we compare in three ways: (a) against the SKY130 process data our "
        "numbers must agree with physically, (b) against published designs of the same function on SKY130 or comparable "
        "nodes, and (c) against industry signoff thresholds. Each reference is cited and its comparability stated; numbers "
        "marked <i>derived</i> are our arithmetic from cited values. References we could not trace to a primary source were "
        "left out."))
    out.append(P("6.1 Normalised results", h2))
    rows = [["Block", "Synth area (NAND2-eq)", "Gate density on die (kGE/mm<super>2</super>)", "Flip-flops", "Power per flop per MHz, TT (uW)",
             "Tiny Tapeout tiles (~16,000 um<super>2</super>)", "Leakage per placed instance, TT (pW)"]]
    for d in N:
        v = D[d]; t = v["power"]["tt_025C_1v80"]; ge = v["synth_area_um2"] / NAND2
        rows.append([d, f"{ge:,.0f}", f"{ge / (v['die_area_um2'] * 1e-6) / 1e3:.0f}", FLOPS[d],
                     f"{t['total_w'] * 1e6 / FLOPS[d] / (1e3 / v['period_ns']):.3f}", f"{v['die_area_um2'] / 16000:.2f}",
                     f"{t['leakage_w'] * 1e12 / v['instances']:.1f}"])
    out.append(KeepTogether([table(rows, [20, 24, 30, 16, 28, 30, 28]),
                             P("Table 14. Derived, normalised figures. NAND2-eq = synthesis area / 3.7536 um<super>2</super> "
                               "(sky130_fd_sc_hd__nand2_1). Flip-flops counted in the final netlists.", cap)]))
    out.append(P(
        "The register-dominated blocks (sync_fifo, uart, spi_master) land within 0.108-0.126 uW per flip-flop per MHz, a tight "
        "spread that indicates the power estimates are internally consistent; counter8 and alu8 are higher per flop because "
        "their logic, not their few registers, dominates."))
    R = [["Quantity", "Our result", "Published reference", "Source", "Agreement"],
         ["D flip-flop area", "sync_fifo 531 flops = ~10,600 um<super>2</super> of 26,050 um<super>2</super> synth area (41%)", "dfxtp_1 20.02 um<super>2</super>; dfrtp_1 25.02 um<super>2</super>", "SKY130 hd liberty tt_025C_1v80 (checked locally)", "Consistent: flop storage is the expected dominant area of a flop-based FIFO"],
         ["Gate density", "61-96 kGE/mm<super>2</super> of die (Table 14)", "&gt;=160 kGE/mm<super>2</super> routed; 266 kGE/mm<super>2</super> raw", "SkyWater PDK docs, foundry-provided libraries", "Below the routed figure because our cores run at 38-56% utilisation and the die includes I/O margin; no density problem"],
         ["Leakage", "4.8-5.5 pW per placed instance at TT, 25 C", "dfxtp_1 8.4 pW; nand2_1 2.1 pW; inv_1 5.3 pW", "SKY130 hd liberty (leakage unit nW)", "Consistent: within the 2.1-8.4 pW range of the individual cells"],
         ["Wire resistance", "2.6-3.6 ohm per um of routed net (includes via and li1 segments)", "met1/met2 0.125 ohm/sq at 0.14 um min width = 0.89 ohm/um (derived); met3/met4 0.047 ohm/sq; li1 12.8 ohm/sq", "SkyWater PDK device details; periphery rules", "Plausible: about 3-4x a bare min-width met1 wire; the difference is vias (via1 4.5 ohm each; 606-16,542 vias per block) and high-resistance li1 pin stubs"],
         ["Via resistance", "4,412 vias in spi_master, all single-cut", "via 4.5 ohm, via2/via3 3.41 ohm, via4 0.38 ohm", "SKY130 PDK resistance-values table", "Single-cut vias are a DFM yield item (Table 11), not a resistance problem at these currents"],
         ["Static IR drop", "0.05-1.37 mV (&lt;=0.08% of 1.8 V)", "Design rule of thumb 5-10% of VDD; 10% drop gives up to 8% gate delay increase (0.18 um)", "Ajami, Banerjee et al., ISQED 2003", "Far inside the budget (about 65x margin at worst)"]]
    out.append(KeepTogether([P("6.2 Against the SKY130 process data", h2), table(R, [22, 40, 42, 34, 38]),
                             P("Table 15. Our physical numbers against SKY130 process data.", cap)]))
    R = [["Block", "Our result", "Comparable design / product", "Its published numbers", "Source", "How comparable"],
         ["uart", "736 cells, 8,363 um<super>2</super> (~2,230 NAND2-eq), 50 MHz, 788 uW (est.)", "CAST H16550S UART IP (16550-compatible, FIFOs excluded)", "~2,769-3,355 gates (28/40/16 nm), 300 MHz", "cast-inc.com H16550S brief", "Same order of logic size; 16550 has more registers/features. Ours is in the expected range"],
         ["uart", "as above", "SKY130 hobby UART, Yosys + OpenROAD, hd library", "231 cells (56 flops), ~4,771 um<super>2</super> core, 50 MHz, fixed 8N1 19,200 baud", "github.com/raghunandanr487-collab/uart_on_openroad", "Same process and library; simpler (fixed baud, no programmable divider), so smaller"],
         ["uart", "788 uW core estimate", "TI TL16C550D discrete UART chip", "ICC max 8 mA at 3.3 V (~26 mW), includes I/O and package", "ti.com TL16C550D datasheet", "Ceiling only: a packaged chip with pads; our core figure is ~30x lower, as expected"],
         ["spi_master", "486 cells (~1,485 NAND2-eq), 5,574 um<super>2</super>, 50 MHz, 581 uW (est.) = 11.6 uW/MHz", "Academic SPI core with APB, Silterra 0.18 um, Synopsys DC", "27,750 um<super>2</super>, 47.12 uW, 16 MHz max (= 2.9 uW/MHz)", "ir.uitm.edu.my/id/eprint/52072", "Closest node. Our area is 5x smaller at a smaller node; our power per MHz is 4x higher, likely because ours is a vector-less 20%-activity estimate including the clock tree. Needs a vector-based run"],
         ["spi_master", "~1,485 NAND2-eq", "CAST SPI-MS quad SPI master IP (16 nm)", "4,259 gates (master), 500 MHz APB", "cast-inc.com SPI-MS", "Vendor IP has more features (quad mode, FIFOs, bus interface); ours is a single-lane master"],
         ["all", "Die 3,119-98,116 um<super>2</super>; 50-100 MHz", "Tiny Tapeout (SKY130 shuttle) tile", "~160 x 100 um per tile (~1,000 gates); design clock up to ~50-66 MHz through the pads", "tinytapeout.com FAQ and clock spec", "counter8 and alu8 fit in one tile; spi_master has about one tile of area but its 122 x 133 um shape needs two; uart two; sync_fifo about six (Table 14)"],
         ["all", "Core area needed", "Efabless Caravel user area (SKY130 MPW shuttle)", "2.92 x 3.52 mm (10.3 mm<super>2</super>)", "caravel-harness docs", "All five blocks together use 0.15 mm<super>2</super>, about 1.4% of one Caravel user area"]]
    out.append(KeepTogether([P("6.3 Against same-function designs and products", h2), table(R, [16, 34, 32, 34, 30, 30]),
                             P("Table 16. Same-function and same-process comparisons. Gate counts of vendor IP are vendor "
                               "figures at their own nodes; they indicate logic size, not area on SKY130.", cap)]))
    R = [["Criterion", "Typical threshold", "Source", "Our result", "Status"],
         ["Static IR drop", "&lt;=5-10% of VDD (we use 5% = 90 mV)", "Ajami et al., ISQED 2003 (10% rule)", "&lt;=1.37 mV", "Pass with large margin"],
         ["Setup/hold with OCV", "Real SKY130 tapeout: set_timing_derate early 0.95 / late 1.05, 0.25 ns uncertainty at 10 ns", "Efabless MPW-6 ExperiarCore SDC", "Flat +/-5% and +/-10% derates, 9 corners, 0.25 ns uncertainty kept (Table 1)", f"4 of 5 blocks meet +/-10% (spi_master conditional); sync_fifo fails already at +/-5% ({sg(WI_ORIG['setup']['5'])} ns, what-if); flat derate is an estimate"],
         ["Stuck-at fault coverage", "Typically 99% or higher (automotive, data-centre, HPC)", "Siemens EDA, DVCon India 2025", "Not measured (DFT deferred)", "Open (Phase 1)"],
         ["DRC / LVS", "0 violations; full match on the foundry deck", "Foundry tape-out practice", "0 / match on open decks", "Pass for an open shuttle; foundry deck not run"],
         ["Electromigration", "Foundry current-density limits", "Not public for SKY130", "Not analysed", "Open (Phase 1)"]]
    out.append(KeepTogether([P("6.4 Against industry signoff thresholds", h2), table(R, [24, 46, 38, 30, 38]),
                             P("Table 17. Industry thresholds versus our results.", cap)]))
    out.append(P(
        "<b>Reading.</b> Where a like-for-like comparison exists, our areas, cell counts, leakage and IR drop sit where the "
        "process data and published designs say they should. Two results do not hold up against real designs: power (our "
        "estimate is vector-less; one comparable SPI core reports about 4x lower power per MHz), and timing with "
        "on-chip-variation derates, where a real SKY130 shuttle design applied a 5% derate and our sync_fifo fails at that "
        "level (Table 1)."))
    return out
