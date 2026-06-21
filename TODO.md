# TODO — Améliorations du projet Animetix

> Audit du 2026-06-20. Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [~] **Renforcer le typage** _(backend : burn-down quasi terminé — branche `typing-burndown`)_
  - ✅ Burn-down backend : **105 → 3 modules** en `ignore_errors` (102 brûlés). Fait dans un venv propre type-CI (`pip install mypy` → mypy 2.1.0 + pathspec 1.1.1, sans dbt) ; le conflit dbt/pathspec n'existe que dans le venv projet. CI `cd backend && mypy .` **verte**. Les 6 adapters d'inférence ML lazy-`None` ont été typés (`self._model: Any = None`, accumulateurs `_last_*` typés, override `generate_3d_scene` aligné sur le port) ; `admin.py` modernisé via `@admin.display`/`@admin.action` (au lieu de `method.short_description = …`).
  - ✅ Contrat de streaming harmonisé sur `dict` (le runtime réel : les processors yieldent `StreamStep(...).model_dump()`, l'orchestrateur fait `yield from`, `streams.py` `json.dumps`). `StateProcessor.process` annonce désormais `Generator[dict, None, RAGState]` ; orchestrateur simplifié (tous les processors sont des générateurs). **Ces 11 erreurs bloquaient mypy en CI.**
  - 🐞✅ **Bugs runtime corrigés (révélés par le typage strict)** :
    - `SimilarityService.find_similar_items` **manquait** alors que `game_service`/`undercover_service` l'appelaient (`AttributeError`) → implémentée par délégation à `repository.get_nearest_neighbors` (format chroma `{"metadatas": [[...]]}`), + garde `None` dans `undercover` (n'indexait plus à l'aveugle).
    - `fallback_adapter` : `raise e` après un `except … as e` interne qui **supprimait** `e` → `NameError` si le décrément de cache échouait. Exception interne renommée (`cache_err`).
    - `trl_ops.trl_ready_dataset` appelait `loop.export_preference_dataset()` **inexistante** sur le `DPOFeedbackLoop` du pipeline (le test la masquait en mockant la classe) → corrigé en `process_and_export(raw_data_path, output_path)` (convention `ai_feedback.jsonl`) + test mis à jour.
    - Vue morte : `urls/api.py` référençait `api_views.SampleView` (inexistante) en fallback de `LatentSpaceDataView` (toujours présente) → simplifié.
    - `advanced_vision_service.vlm_rerank` traitait le retour de `visual_rerank` (liste de **dicts** `{"index", "score"}`) comme des **index entiers** (`0 <= idx < len`, `candidate_items[idx]`) → `TypeError` au runtime. Corrigé en extrayant `ranked.get("index")` (comme `VlmRerankProcessor`).
    - `tree_of_thoughts_service:144` : `InferenceResponse` réassignée puis utilisée comme `str` dans la branche `except` → `.text` ajouté.
    - `validation_gate._run_ai_critique` annoté `-> (str, float)` (un tuple-valeur, pas un type) → `tuple[str, float]`. `django_repository_adapter.get_nearest_neighbors` renvoyait `[]` contre un contrat de port `Optional[Dict]` → `None`.
  - 🔎 Dette restante (3 modules, par conception) : `settings.py` (Django dynamique / star-imports), `core.utils.lazy_import` (métaprogrammation), `emoji_service` (décision produit). Plusieurs déréférencements `None` latents (multi_agent_bus, cinematic, advanced_rag, swarm_consensus, fallback) ont été **gardés** au passage.
  - ⏭️ `emoji_service` reporté (le fix correct = parser la str LLM en liste, mais ça change le comportement et casse un test qui encode l'ancien comportement → décision produit).
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
