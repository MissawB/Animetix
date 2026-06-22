# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [x] **Coût/Infra — bornes de scaling du brain GPU non explicites** _(analyse financière 2026-06-22 ; résolu le 2026-06-22)_
  - Constat initial (« aucune IaC ») **partiellement faux** : le déploiement est bien codifié dans [scripts/deploy/deploy_brain.py](scripts/deploy/deploy_brain.py) (Cloud Run, L4, secrets, VPC, volume GCS-FUSE). Le vrai défaut : `--min-instances`/`--max-instances` n'étaient **pas fixés** → défauts Cloud Run (min=0 implicite — le brain scalait déjà à zéro ; max=100 non plafonné). Le « GPU fixe 24/7 » du [COST_AUDIT.md](docs/COST_AUDIT.md) était donc inexact.
  - **Fait :** ajout de `--min-instances=0` (scale-to-zero explicite/auditable) et `--max-instances=3` (plafond coût, aligné sur le défaut de `restore_brain_service`) dans le script de déploiement. COST_AUDIT corrigé.

## 🟡 Moyens

- [ ] **Backend — `UnifiedInferenceAdapter` god object**
  - 8 mixins, ~476 lignes ([unified_inference_adapter.py:30](backend/adapters/inference/unified_inference_adapter.py#L30)) ; MRO fragile, dur à tester → composition plutôt qu'héritage multiple.

## 🟢 Faibles

- [ ] **Couverture frontend — élargir** _(ongoing optionnel ; 520 tests, seuils 29/22/28/29)_
  - Reste (ROI décroissant) : flows complexes 3D/canvas/WebSocket (`useTachideskExplorer`, `useSocket`, `useMultiverseCatalog`) ; continuer à remonter le plancher au fil de l'eau.
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. À purger lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).
