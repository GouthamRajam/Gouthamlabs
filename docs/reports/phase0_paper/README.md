# Phase 0 signoff results paper

`../S2S_Phase0_Signoff_Results.pdf` is generated from the committed tool reports; nothing is typed in by hand.

    python collect.py data.json          # read reports, metrics.json and SPEF of the five runs (S2S artifact store)
    python figs.py .                     # Figure 1 (layouts from the signed GDS), Figure 2 (power, IR drop)
    python build.py . ../S2S_Phase0_Signoff_Results.pdf   # also runs sections_new.py (tools, teams, failures, comparison)

Needs reportlab, matplotlib and gdstk. collect.py reads var/artifacts/runs (the runs' working folders); the same
GDS, SPEF and reports are in docs/milestones/m0.7-evidence/<design>/<run>/.

Derated (flat OCV) timing: collect.py also reads each run's reports/sta_tool.json key "derated" and the current hard-check
verdict from reports/tapeout_readiness.json. sync_fifo has no recorded derated signoff; its three what-if rows (signed original,
design change #1, design change #2) are read from the OpenSTA logs in var/artifacts/scratch_ocv/{sync_fifo,sync_fifo_fix_it3,
sync_fifo_fix2_it3} and are labelled "what-if, not a recorded signoff" in the paper.

exec.json and failed_stage.txt are queries of the orchestrator database (runs, tasks, checks, events, usage) for the five
designs; external comparison figures are cited in the paper's References and were checked against the PDK liberty file
where possible.
