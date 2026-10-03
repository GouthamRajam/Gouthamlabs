# Golden logs (M0.2)

Real tool output, recorded by running each adapter in the `s2s-eda` image. None of these
files is hand-written or edited. Unit tests (`tests/test_golden.py`, `test_parsers.py`,
`test_safety_net.py`) parse them with exactly the same code path the live adapters use.

Layout: `<tool>/<case>/`
- `log.txt` — the tool's raw combined stdout/stderr
- `reports/<name>` — report files the parser also reads (e.g. sby JUnit, KLayout lyrdb,
  Netgen report + JSON, cocotb results.xml, OpenLane flow.log + metrics)
- `meta.json` — exact command, exit code, tool version, environment hash, capture time,
  and the live result (status, reasons, metrics) the adapter returned

Every tool has at least one `pass` case and one `fail_*` case. A golden is written only if
the real run's verdict matches the case's expectation.

Regenerate (needs docker + the `s2s-eda` image):

    cd backend
    python -m tests.capture_golden              # all cases (OpenLane cases take a few minutes)
    python -m tests.capture_golden opensta      # only cases whose id contains "opensta"

Cases and their inputs are defined in `tests/cases.py`; inputs live in `tests/fixtures/`.
