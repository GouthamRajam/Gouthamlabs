# Engineering Knowledge Store

Machine-readable knowledge base for S2S agent cold-start and continuity.
Derived from trajectory logs, DECISIONS.md, and experiment results.

## Structure

```
knowledge/
  README.md          — this file
  index.yaml         — master index of all entries (topic, file, tags, status)
  experiments/       — experiment results and failure analyses
  methods/           — known-good methods (synthesis, P&R, verification recipes)
  decisions/         — structured decision records (from DECISIONS.md)
  failures/          — root-cause analyses of significant failures
```

## Entry Format

Each entry is a YAML file with:
```yaml
topic: short-title
summary: one-paragraph description
evidence:
  - path: relative/path/to/file
    commit: abc1234
tags: [synthesis, sky130, phase-0]
status: confirmed | provisional | superseded
date: 2026-10-08
related: [other-entry-id]
```

## Populated by

- Phase 0/1 experiment results (backfilled from DECISIONS.md and trajectory logs)
- Ongoing Phase 1 work (each significant decision or failure gets an entry)
- Phase 1.5 Pillar D requires this store to be complete enough for cold-start 5/5

## NOT stored here

- Raw tool logs (stay in var/artifacts/)
- The full MASTER_SPEC (stays in docs/)
- Secrets, API keys, credentials
