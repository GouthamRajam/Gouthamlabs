<!-- Copied verbatim from docs/MASTER_SPEC.md: Appendix B.1 `spec.yaml` -->
design: uart
version: 1
summary: "UART transmitter and receiver with configurable parity."
pdk: sky130A
std_cell_library: sky130_fd_sc_hd
target_clock_mhz: 50
target_clock_note: "DEFAULT — needs G1 review"
clocks:
  - {name: clk, freq_mhz: 50}
resets:
  - {name: rst_n, active: low, type: synchronous}
interfaces:
  - {name: clk, dir: in, width: 1}
  - {name: rst_n, dir: in, width: 1}
  - {name: tx, dir: out, width: 1, protocol: "UART 8N1/8E1/8O1"}
  - {name: rx, dir: in, width: 1, protocol: "UART", async: true}
  - {name: tx_data, dir: in, width: 8}
  - {name: tx_valid, dir: in, width: 1}
  - {name: tx_ready, dir: out, width: 1}
  - {name: rx_data, dir: out, width: 8}
  - {name: rx_valid, dir: out, width: 1}
  - {name: baud_div, dir: in, width: 16}
  - {name: parity_mode, dir: in, width: 2, values: {0: none, 1: even, 2: odd}}
  - {name: frame_err, dir: out, width: 1}
  - {name: parity_err, dir: out, width: 1}
requirements:
  - id: REQ-001
    type: functional
    text: "Transmit one 8-bit word per tx_valid & tx_ready handshake, LSB first, 1 start bit, 1 stop bit."
    acceptance: "Serialized waveform matches reference model for 10,000 random words."
  - id: REQ-002
    type: functional
    text: "Receiver samples rx at 16x oversampling and takes the majority of 3 center samples."
    acceptance: "Correct reception with ±2% baud mismatch between sender and receiver."
  - id: REQ-003
    type: reset
    text: "After reset, tx is high (idle), tx_ready is 1, rx_valid and error flags are 0."
    acceptance: "Checked by directed test and formal property."
  # ...
out_of_scope: ["flow control (RTS/CTS)", "FIFOs larger than 1 entry"]
open_questions: []
