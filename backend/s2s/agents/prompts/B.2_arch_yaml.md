<!-- Copied verbatim from docs/MASTER_SPEC.md: Appendix B.2 `arch.yaml` -->
design: uart
top: uart_top
modules:
  - name: uart_top
    ports_from_spec: true
    instances: [baud_gen, uart_tx, uart_rx, sync2]
  - name: baud_gen
    params: {DIV_W: 16}
    ports:
      - {name: clk, dir: in, width: 1}
      - {name: rst_n, dir: in, width: 1}
      - {name: baud_div, dir: in, width: DIV_W}
      - {name: tick16, dir: out, width: 1}
    implements: [REQ-002]
  # ...
connections:
  - {from: baud_gen.tick16, to: [uart_tx.tick16, uart_rx.tick16]}
cdc:
  - {signal: rx, from: async, to: clk, synchronizer: sync2}
state_machines:
  - module: uart_tx
    states: [IDLE, START, DATA, PARITY, STOP]
ppa_estimate:
  cells: 420
  critical_path_levels: 9
  slack_margin_pct: 35
rationale:
  - "Shared 16x tick for TX and RX keeps one divider; TX uses every 16th tick."
