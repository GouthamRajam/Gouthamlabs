# Phase 0 signoff results paper

`../S2S_Phase0_Signoff_Results.pdf` is generated from the committed tool reports; nothing is typed in by hand.

    python collect.py data.json          # read reports, metrics.json and SPEF of the five runs (S2S artifact store)
    python figs.py .                     # Figure 1 (layouts from the signed GDS), Figure 2 (power, IR drop)
    python build.py . ../S2S_Phase0_Signoff_Results.pdf

Needs reportlab, matplotlib and gdstk. collect.py reads var/artifacts/runs (the runs' working folders); the same
GDS, SPEF and reports are in docs/milestones/m0.7-evidence/<design>/<run>/.
