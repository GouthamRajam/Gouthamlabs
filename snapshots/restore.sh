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

# Tape-out outputs (GDSII, reports) committed by backend/scripts/export_evidence.py: copy them back into the
# run folders the API reads (var/artifacts/runs/<run_id>/), and re-check each package's MANIFEST.sha256.
EVID=docs/milestones/m0.7-evidence
if command -v sha256sum >/dev/null 2>&1; then SHA="sha256sum"; else SHA="shasum -a 256"; fi   # macOS: shasum
n=0
for pkg in "$EVID"/*/*/tapeout; do
  [ -d "$pkg" ] || continue
  src=$(dirname "$pkg"); run_id=$(basename "$src"); dst=var/artifacts/runs/$run_id
  mkdir -p "$dst"
  rm -rf "$dst/tapeout" && cp -R "$pkg" "$dst/tapeout"
  for rel in spec/spec.yaml arch/arch.yaml signoff/layout3d.json; do
    if [ -f "$src/$rel" ]; then mkdir -p "$dst/$(dirname "$rel")" && cp "$src/$rel" "$dst/$rel"; fi
  done
  if [ -d "$src/reports" ]; then mkdir -p "$dst/reports" && cp "$src"/reports/* "$dst/reports/"; fi
  # the API rebuilds layout3d.json (needs KLayout + PDK) when it is older than the GDS: keep the copy newer
  if [ -f "$dst/signoff/layout3d.json" ]; then touch "$dst/signoff/layout3d.json"; fi
  if (cd "$dst/tapeout" && $SHA -c MANIFEST.sha256 >/dev/null 2>&1); then chk=ok; else chk="MISMATCH (run: $SHA -c MANIFEST.sha256 in $dst/tapeout)"; fi
  echo "tape-out package: $(basename "$(dirname "$src")") $run_id -> $dst (manifest $chk)"
  n=$((n + 1))
done
echo "restored $n tape-out package(s) from $EVID"

echo
echo "Now start, in two terminals (NOT the orchestrator):"
echo "  cd backend && S2S_ARTIFACT_DIR=\"\$PWD/../var/artifacts\" uvicorn s2s.api.app:app --port 8000"
echo "  cd web && npm run dev        # then open http://localhost:3000"
