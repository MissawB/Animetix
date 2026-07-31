# Deploy assets: Git LFS → GCS migration

## Why

`deploy-to-prod` checked out the repo with `lfs: true` to get the runtime data
(`data/processed/*.json`, `data/artifacts/*` incl. `*.npy`) and the favicons.
That `git lfs fetch` consumes the account's **GitHub LFS bandwidth budget**
(free tier: 1 GiB/month). Once exhausted, every deploy fails at the very first
step with:

```
batch response: This repository exceeded its LFS budget.
error: failed to fetch some objects from '.../info/lfs'
```

The deploy never reaches GCP — auth/build/deploy steps are all skipped.

## What changed

The deploy no longer touches Git LFS. Instead:

1. The deploy-critical assets live in a GCS bucket **`gs://animetix-deploy-assets`**
   (mirrors the repo paths: `data/processed/`, `data/artifacts/`, `frontend/public/`).
2. `cloudbuild.yaml` gained a first step **`hydrate-web-assets`** that
   `gsutil rsync`s those into the build context (overwriting the LFS pointer
   stubs) **before** `build-web` runs `COPY . .`.
3. Both deploy jobs in `.github/workflows/ci.yml` dropped `lfs: true`.
   - web: assets come from GCS (above).
   - brain: inference-only, never needed the LFS data.

App code and `sync_catalog` are unchanged — the image still ships the same
`/app/data/...` files, just sourced from GCS instead of LFS.

The files remain in Git LFS for **local dev** (unchanged clone/pull workflow);
GCS is only the *deploy* source. Nothing was removed from git history.

## One-time setup (before the next deploy)

Requires `gcloud`/`gsutil` authenticated with write access to project `animetix`,
and the LFS files hydrated locally (`git lfs pull` if you only have pointers).

```bash
./scripts/deploy/gcp/sync_web_assets_to_gcs.sh
```

This creates the bucket if missing and uploads `data/processed`,
`data/artifacts` and the favicons.

## Ongoing

Re-run the same script **whenever `data/processed`, `data/artifacts` or the
favicons change**, then deploy:

```bash
./scripts/deploy/gcp/sync_web_assets_to_gcs.sh
gh workflow run ci.yml -f deploy_to_prod=true --ref main
```

## Rollback

Re-add `with: { lfs: true }` to the deploy checkout in `ci.yml` and remove the
`hydrate-web-assets` step from `cloudbuild.yaml`. (Only viable once the LFS
bandwidth budget is restored.)

## Optional phase 2 (not done)

To also stop LFS *storage* growth and dev-clone bandwidth, untrack the large
data from LFS entirely (`.gitattributes` + `git rm --cached` + `.gitignore`)
and have devs fetch from GCS too. Deferred — the bandwidth drain (deploy) is
already fixed by the above.
