# TODO — Améliorations du projet Animetix

> Audit du 2026-06-20. Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [ ] **Renforcer le typage**
  - Backend : ~105 modules en `ignore_errors=true` (mypy), baseline ~445 erreurs. Burn-down progressif (105 → 50 → 10).
  - ⚠️ Burn-down bloqué localement (dbt épingle `pathspec<0.13`, incompatible avec le mypy courant ; le seul mypy qui tourne localement est non-standard et **diverge de la CI**). → **À faire dans un venv propre type-CI** (`pip install mypy`, sans dbt) : désactiver l'override `ignore_errors`, `cd backend && mypy .`, retirer de la liste tout module à 0 erreur, vérifier vert.
  - 🔎 Piste : contrat de streaming incohérent — `StateProcessor.process` annonce `Generator[StreamStep,…]` mais des processors (`judge/graph_explore/fallback/acquire_knowledge`) annotent `Generator[dict,…]` et yieldent des `StreamStep(...).model_dump()` (dicts). Harmoniser.
  - Frontend : durcir progressivement les interfaces les plus laxistes (les `any` bloquants sont déjà résorbés).

- [ ] **CI couverture — job d'intégration optionnel** _(le gate `--cov-fail-under=75` + upload Codecov sont posés)_
  - Hook `conftest` qui ping ollama et **skip gracieusement** les tests `@pytest.mark.integration` s'il est injoignable, + job CI dédié non-bloquant.

- [x] **Consolidation de la couverture backend → 75 % — ✅ ATTEINT : 75,33 %** _(branche `worktree-coverage-consolidation`, 2285 tests verts)_
  - **Mesure finale 2026-06-21 : 75,33 % global** (`--cov=backend`, le flag exact du gate CI ; 19 831 / 26 325 lignes). Point de départ 55,05 %.
  - ⚠️ **Méthodologie** : mesurer **par chemin** (`--cov=backend`), PAS par nom de package (`--cov=pipeline` sous-compte les modules importés `backend.pipeline.*` à 0 % à cause du dual-namespace ; CI utilise déjà `--cov=backend`, donc le gate n'est pas affecté).
  - Modules portés à 100 %/quasi cette campagne : `auth` (0→100), games `vision`/`akinetix`/`blindtest` (100), `librarian`, `akinetix_rl_service`, `tasks_views`, `creative_tasks` (100), `dpo_dataset_compiler` (81→95), `api/core` (79→100), `video_analysis` (44→100), `index_otaku_knowledge` (51→96).
  - ⚠️ Seul rouge restant : `tests/backend/test_speech_to_speech_live.py::test_speech_to_speech_live_consumer` — flaky e2e connu (timeout), sans rapport avec la couverture.
  - **Lot 🟢 — fortement testable (mock-based, méthode P1-P3 prouvée) — ✅ FAIT (commit `245e92f3`) :**
    - [x] Adaptateurs inférence : `google_genai_adapter`, `brain_api.py`, `fallback_adapter`, `unified_inference_adapter`.
    - [x] Agents RAG : `rag/agents/debate_manager`, `rag/agents/planner`, `rag/hybrid_index`.
    - [x] Scrapers/extracteurs : `pipeline/mlops/fandom_lore_scraper`, `pipeline/characters/extract_akinetix_attributes`, `pipeline/characters/vectorize_characters`.
  - **Lot 🟡 — gros volume, vues DRF (APIClient + `@django_db` + mock conteneur) — ✅ FAIT (commits `903001b9`, `b614dcb1`, `9dcb953d`, `e488853a`, `06aef310`) :**
    - [x] `api/labs.py`, `api/core.py`, `api/social.py`, `api/multiverse.py`, `api/developer.py`, `api/mlops.py`, `api/cognition.py`, `views.api`.
    - [x] `api/games/*` : classic, archetypist, emoji, paradox, covertest (conftest partagé de re-wiring DI).
    - [x] Tasks Celery `tasks/pipeline_tasks.py` ; persistence `neo4j_client`, `chroma_client`, `pgvector_repository_adapter` (99 % combiné `tests/adapters/` + `tests/core/`).
  - **Lot 🔴 — difficile (torch/GPU, faux-vert risqué) :**
    - [x] `pipeline/mlops/train_expert_model` (0 → 88 %, commit `82c463e5`, tout I/O torch mocké).
    - [ ] Orchestrateur `finetuning_dataset.run_generate_instruction_dataset` (433, 14 %). _À traiter au cas par cas, sans gonfler la couverture._
  - _Méthode : mesurer par module ciblé (`--cov=<module>`), pas de full-run (17 min). Mêmes garde-fous : vrais tests de comportement, tout I/O mocké, pas de faux-vert._

## 🟡 Moyens

- [ ] **MLOps — versioning data/modèles (DVC/MLflow)** _(optionnel, lourd)_ — la provenance des checkpoints (commit/timestamp) est faite ; reste le versioning data/modèles avec remotes (infra à configurer, non vérifiable en local).
- [ ] **État frontend — convention de state** — harmoniser 9 stores Zustand vs React Query vs useState (décision de design à cadrer, pas un sweep mécanique). _Les `window.location.reload()` ont déjà été éliminés._
- [ ] **Performance frontend — fignolages** _(ROI moindre)_ — `loading="lazy"` sur les `<img>`, `React.memo`/`useMemo` ciblés. _Le gros levier (précache PWA −60 %) est fait._

## 🟢 Faibles

- [ ] **Accessibilité — labels restants** — quelques `control-has-associated-label` en `warn` (contrôles icône / lignes de tableau / div draggable `AudioLabPage`) à étiqueter, puis passer la règle en `error`.
- [ ] **Couverture de tests frontend** — ajouter `vitest --coverage` et élargir (la campagne P4 a déjà ajouté stores/ErrorBoundary/offline ; vitest 69 → 191).
- [ ] **Organisation des tests backend** — `tests/backend/` vs `tests/core/` se recouvrent.
- [ ] **Logging MLOps** — `logging.basicConfig` répété par script ; centraliser.
- [ ] **E2E Playwright** — Chromium seul, pas de screenshots on failure ni d'artefacts CI.
- [ ] **K6 load test** présent mais hors CI, sans baseline.
- [ ] **`Dockerfile.dataflow`** — pas de HEALTHCHECK, fichier pipeline figé.
