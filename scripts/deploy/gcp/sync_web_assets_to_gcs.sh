#!/usr/bin/env bash
#
# Mirror the deploy-critical binary assets to GCS so the prod web build can
# hydrate them WITHOUT a `git lfs fetch` (which exhausts the GitHub LFS
# bandwidth budget and blocked every deploy — "exceeded its LFS budget").
#
# These assets are still tracked in Git LFS for local dev; GCS is the source
# the Cloud Build `hydrate-web-assets` step reads (see cloudbuild.yaml).
#
# RUN THIS whenever data/processed, data/artifacts or the favicons change,
# BEFORE triggering a prod deploy. Requires gcloud/gsutil authenticated with
# write access to the project.
#
# Usage:
#   ./scripts/deploy/gcp/sync_web_assets_to_gcs.sh            # default bucket
#   ./scripts/deploy/gcp/sync_web_assets_to_gcs.sh my-bucket  # custom bucket
#
set -euo pipefail

BUCKET="${1:-animetix-deploy-assets}"
PROJECT="${GCP_PROJECT:-animetix}"
REGION="${GCP_REGION:-europe-west9}"

# Run from repo root regardless of where it's invoked from.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

# Guard: refuse to upload Git LFS pointer stubs (would ship a broken image).
# A pointer file starts with "version https://git-lfs.github.com/spec/v1".
guard_hydrated() {
  local f="$1"
  if head -c 64 "$f" 2>/dev/null | grep -q 'git-lfs.github.com/spec'; then
    echo "ERROR: $f is a Git LFS pointer, not real data."
    echo "       Run 'git lfs pull' first (needs LFS bandwidth) so real files are uploaded."
    exit 1
  fi
}
guard_hydrated data/processed/combat_data.json
guard_hydrated frontend/public/favicon-32x32.png

# Create the bucket if it doesn't exist yet (idempotent).
if ! gsutil ls -b "gs://${BUCKET}" >/dev/null 2>&1; then
  echo "Creating bucket gs://${BUCKET} (${REGION}) ..."
  gsutil mb -p "$PROJECT" -l "$REGION" -b on "gs://${BUCKET}"
fi

echo "[1/3] Uploading data/processed ..."
gsutil -m rsync -r -d data/processed "gs://${BUCKET}/data/processed"

echo "[2/3] Uploading data/artifacts (json + npy) ..."
gsutil -m rsync -r -d data/artifacts "gs://${BUCKET}/data/artifacts"

echo "[3/3] Uploading favicons (frontend/public/*.png) ..."
gsutil -m cp frontend/public/*.png "gs://${BUCKET}/frontend/public/"

echo ""
echo "Done. gs://${BUCKET} is now the deploy source for the web build."
echo "Next: trigger a deploy — gh workflow run ci.yml -f deploy_to_prod=true --ref main"
