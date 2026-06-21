# TODO — Améliorations du projet Animetix

> Audit du 2026-06-20. Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [~] **Renforcer le typage** _(backend : gros burn-down fait — branche `typing-burndown`)_
  - ✅ Burn-down backend : **105 → 51 modules** en `ignore_errors` (54 brûlés). Fait dans un venv propre type-CI (`pip install mypy` → mypy 2.1.0 + pathspec 1.1.1, sans dbt) ; le conflit dbt/pathspec n'existe que dans le venv projet. CI `cd backend && mypy .` **verte**.
  - ✅ Contrat de streaming harmonisé sur `dict` (le runtime réel : les processors yieldent `StreamStep(...).model_dump()`, l'orchestrateur fait `yield from`, `streams.py` `json.dumps`). `StateProcessor.process` annonce désormais `Generator[dict, None, RAGState]` ; orchestrateur simplifié (tous les processors sont des générateurs). **Ces 11 erreurs bloquaient mypy en CI.**
  - 🐞 **Bug réel surfacé (non corrigé — décision produit)** : `SimilarityService` n'a pas de méthode `find_similar_items`, pourtant `game_service.find_similar_items` et `undercover_service` l'appellent → `AttributeError` au runtime. Aucune implémentation nulle part. `game_service`/`undercover_service` laissés dans la baseline. À implémenter (requête vectorielle format `{"metadatas": [[...]]}`).
  - 🐞 Vue morte supprimée : `urls/api.py` référençait `api_views.SampleView` (inexistante) en fallback de `LatentSpaceDataView` (toujours présente) → simplifié.
  - ⏭️ Reste 51 modules en baseline (~213 erreurs) pour atteindre la cible → 10. `emoji_service` reporté (le fix correct = parser la str LLM en liste, mais ça change le comportement et casse un test qui encode l'ancien comportement → décision produit).
  - Frontend : durcir progressivement les interfaces les plus laxistes (les `any` bloquants sont déjà résorbés). _(non traité ici)_

- [ ] **CI couverture — job d'intégration optionnel** _(le gate `--cov-fail-under=75` + upload Codecov sont posés)_
  - Hook `conftest` qui ping ollama et **skip gracieusement** les tests `@pytest.mark.integration` s'il est injoignable, + job CI dédié non-bloquant.

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
