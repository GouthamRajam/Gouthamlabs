# S2S database snapshot (from the Claude Code cloud session)

`s2s_db.dump` is a `pg_dump -Fc` of the cloud session's S2S database: runs, tasks, agent events, checks,
gates, findings and metered spend for counter8, sync_fifo and uart (M0.5, M0.6, and M0.7 once it runs).
Restore it locally to see that history in the Live Office. It is a **snapshot**: refreshed and re-pushed at
milestones, never a live link.

Not included: the API key (it lives in an encrypted file, not the database; the dump was checked for it),
and the large run files under `var/artifacts/` (waveforms, logs). Pages that open those files will
show them as missing. The tape-out outputs (GDSII, reports) are committed separately, see below.

## Restore (local machine)

```bash
# 1. stop the local API and, IMPORTANT, the orchestrator (see the warning below)
docker compose up -d postgres
# 2. replace the local s2s database with the snapshot
docker compose exec -T postgres pg_restore -U s2s -d s2s --clean --if-exists --no-owner < snapshots/s2s_db.dump
# 3. start only the API and the web app
cd backend && uvicorn s2s.api.app:app --port 8000     # in one terminal
cd web && npm run dev                                 # in another: http://localhost:3000
```

Open http://localhost:3000, then use **Replay** or pick a run.

## GDSII and reports

The M0.7 tape-out packages are committed separately from the dump, under
`docs/milestones/m0.7-evidence/<design>/<run_id>/`: the whole `tapeout/` package (GDS, netlists, SPEF,
constraints, flow, RTL, reports, evidence, checklist, `reproduce.sh`, `MANIFEST.sha256`, ...), plus the run's
`reports/*.md|json`, `signoff/layout3d.json` (the 3D viewer's geometry), `arch/arch.yaml` (the API reads the
top name from it) and `spec/spec.yaml`. The cloud session writes them with

```bash
cd backend && python scripts/export_evidence.py     # re-hashes every file against MANIFEST.sha256
```

`snapshots/restore.sh` copies them back to `var/artifacts/runs/<run_id>/` and re-checks each manifest, so the
local API's Outputs downloads (`GET /runs/{id}/files/...`) and 3D layout (`GET /runs/{id}/layout3d`) work.
Start the API with `S2S_ARTIFACT_DIR` pointing at that folder (restore.sh prints the command). The GDS is
also a plain file you can open directly in KLayout.

## Warning: do not start the orchestrator on this snapshot

The snapshot was taken while uart's verification was running, so some tasks are marked `running`.
A local orchestrator would "recover" them and continue the work on your machine, making real model
calls with your local key. View it with the API and web app only.
