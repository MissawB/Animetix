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

- [ ] **Consolidation de la couverture backend → 75 %** _(branche `worktree-coverage-consolidation`)_
  - **Mesure 2026-06-21 : 55,05 % global** (14 467 / 26 282 lignes ; plancher local, 114 échecs infra redis/neo4j → CI un peu plus haut). **~5 200 lignes à couvrir** pour atteindre le gate 75 %.
  - **Lot 🟢 — fortement testable (mock-based, méthode P1-P3 prouvée) :**
    - [ ] Adaptateurs inférence : `google_genai_adapter` (215 manq., 44 %), `brain_api.py` (169, 52 %), `fallback_adapter` (140, 59 %), `unified_inference_adapter` (138, 31 %).
    - [ ] Agents RAG : `rag/agents/debate_manager` (103, 13 %), `rag/agents/planner` (93, 10 %), `rag/hybrid_index` (103, 13 %).
    - [ ] Scrapers/extracteurs 0 % : `pipeline/mlops/fandom_lore_scraper` (143), `pipeline/characters/extract_akinetix_attributes` (89), `pipeline/characters/vectorize_characters` (86).
  - **Lot 🟡 — gros volume, plus lourd (vues DRF : APIClient + `@django_db` + mock conteneur) — ~1 800 lignes :**
    - [ ] `api/labs.py` (416, 22 %), `api/core.py` (349, 30 %), `api/social.py` (192, 33 %), `api/multiverse.py` (161, 17 %), `api/developer.py` (120, 24 %), `api/mlops.py` (105, 42 %), `api/games/*` (classic 102, archetypist 100…), `api/cognition.py` (97).
    - [ ] Tasks Celery `tasks/pipeline_tasks.py` (232, 8 %) ; persistence `pgvector_repository_adapter` (128, 31 %), `neo4j_client` (160, 37 %), `chroma_client` (109, 63 %).
  - **Lot 🔴 — difficile (torch/GPU, faux-vert risqué) :** `pipeline/mlops/train_expert_model` (175, 0 %), orchestrateur `finetuning_dataset.run_generate_instruction_dataset` (433, 14 %). _À traiter au cas par cas, sans gonfler la couverture._
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
