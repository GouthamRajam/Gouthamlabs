# S2S database snapshot (from the Claude Code cloud session)

`s2s_db.dump` is a `pg_dump -Fc` of the cloud session's S2S database: runs, tasks, agent events, checks,
gates, findings and metered spend for counter8, sync_fifo and uart (M0.5, M0.6, and M0.7 once it runs).
Restore it locally to see that history in the Live Office. It is a **snapshot**: refreshed and re-pushed at
milestones, never a live link.

Not included: the API key (it lives in an encrypted file, not the database; the dump was checked for it),
and the large run files under `var/artifacts/` (waveforms, GDS, logs). Pages that open those files will
show them as missing.

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

## Warning: do not start the orchestrator on this snapshot

The snapshot was taken while uart's verification was running, so some tasks are marked `running`.
A local orchestrator would "recover" them and continue the work on your machine, making real model
calls with your local key. View it with the API and web app only.
