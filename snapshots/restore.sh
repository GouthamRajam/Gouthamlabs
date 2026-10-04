#!/usr/bin/env bash
# Restore the cloud session's S2S database snapshot into the local Postgres and start the API + Live Office.
# Run from the repo root on YOUR machine:   bash snapshots/restore.sh
# It never starts the orchestrator (the snapshot has tasks marked running; see snapshots/README.md).
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only origin claude/tender-davinci-2r4q38 || true
docker compose up -d postgres
echo "waiting for postgres..."
until docker compose exec -T postgres pg_isready -U s2s >/dev/null 2>&1; do sleep 1; done
docker compose exec -T postgres pg_restore -U s2s -d s2s --clean --if-exists --no-owner < snapshots/s2s_db.dump || true
echo "restored: $(docker compose exec -T postgres psql -U s2s -d s2s -Atc 'select count(*) from runs') runs, \
$(docker compose exec -T postgres psql -U s2s -d s2s -Atc 'select count(*) from events') events"
echo
echo "Now start, in two terminals (NOT the orchestrator):"
echo "  cd backend && uvicorn s2s.api.app:app --port 8000"
echo "  cd web && npm run dev        # then open http://localhost:3000"
