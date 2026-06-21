# TODO — Améliorations du projet Animetix

> Audit du 2026-06-20. Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [x] **Renforcer le typage** _(backend terminé — branche `typing-burndown`)_
  - ✅ Burn-down backend : **105 → 0 modules** en `ignore_errors` (baseline supprimée). `cd backend && mypy .` **verte sur 471 fichiers, sans aucun override**. Fait dans un venv propre type-CI (`pip install mypy` → mypy 2.1.0 + pathspec 1.1.1, sans dbt) ; le conflit dbt/pathspec n'existe que dans le venv projet. Les 6 adapters d'inférence ML lazy-`None` typés (`self._model: Any = None`, accumulateurs `_last_*`, override `generate_3d_scene` aligné) ; `admin.py` modernisé (`@admin.display`/`@admin.action`) ; `lazy_import` (proxy `ModuleType`) et un filtre de logging Django portent des `# type: ignore[<code>]` ciblés et commentés ; `emoji_service` typé honnêtement `List[str] | str` (comportement inchangé).
  - ✅ Contrat de streaming harmonisé sur `dict` (le runtime réel : les processors yieldent `StreamStep(...).model_dump()`, l'orchestrateur fait `yield from`, `streams.py` `json.dumps`). `StateProcessor.process` annonce désormais `Generator[dict, None, RAGState]` ; orchestrateur simplifié (tous les processors sont des générateurs). **Ces 11 erreurs bloquaient mypy en CI.**
  - 🐞✅ **Bugs runtime corrigés (révélés par le typage strict)** :
    - `SimilarityService.find_similar_items` **manquait** alors que `game_service`/`undercover_service` l'appelaient (`AttributeError`) → implémentée par délégation à `repository.get_nearest_neighbors` (format chroma `{"metadatas": [[...]]}`), + garde `None` dans `undercover` (n'indexait plus à l'aveugle).
    - `fallback_adapter` : `raise e` après un `except … as e` interne qui **supprimait** `e` → `NameError` si le décrément de cache échouait. Exception interne renommée (`cache_err`).
    - `trl_ops.trl_ready_dataset` appelait `loop.export_preference_dataset()` **inexistante** sur le `DPOFeedbackLoop` du pipeline (le test la masquait en mockant la classe) → corrigé en `process_and_export(raw_data_path, output_path)` (convention `ai_feedback.jsonl`) + test mis à jour.
    - Vue morte : `urls/api.py` référençait `api_views.SampleView` (inexistante) en fallback de `LatentSpaceDataView` (toujours présente) → simplifié.
    - `advanced_vision_service.vlm_rerank` traitait le retour de `visual_rerank` (liste de **dicts** `{"index", "score"}`) comme des **index entiers** (`0 <= idx < len`, `candidate_items[idx]`) → `TypeError` au runtime. Corrigé en extrayant `ranked.get("index")` (comme `VlmRerankProcessor`).
    - `tree_of_thoughts_service:144` : `InferenceResponse` réassignée puis utilisée comme `str` dans la branche `except` → `.text` ajouté.
    - `validation_gate._run_ai_critique` annoté `-> (str, float)` (un tuple-valeur, pas un type) → `tuple[str, float]`. `django_repository_adapter.get_nearest_neighbors` renvoyait `[]` contre un contrat de port `Optional[Dict]` → `None`.
  - 🔎 Dette restante : **aucune** (baseline `ignore_errors` vide). Plusieurs déréférencements `None` latents (multi_agent_bus, cinematic, advanced_rag, swarm_consensus, fallback) ont été **gardés** au passage.
  - ⏭️ `emoji_service` reporté (le fix correct = parser la str LLM en liste, mais ça change le comportement et casse un test qui encode l'ancien comportement → décision produit).
  - Frontend : durcir progressivement les interfaces les plus laxistes (les `any` bloquants sont déjà résorbés). _(non traité ici)_

- [ ] **CI couverture — job d'intégration optionnel** _(le gate `--cov-fail-under=75` + upload Codecov sont posés)_
  - Hook `conftest` qui ping ollama et **skip gracieusement** les tests `@pytest.mark.integration` s'il est injoignable, + job CI dédié non-bloquant.

## 🟡 Moyens

- [x] **MLOps — versioning data/modèles** — couvert : tracking expériences/artefacts via HF Trackio + wandb (`log_param`/`log_metric`/`log_artifact("dataset"…)`/`log_artifact("adapter"…)`), provenance des checkpoints via `run_provenance` (commit git + timestamp UTC + révisions manifest → `run_metadata.json`). Choix d'architecture délibéré « sans dépendance lourde (ni MLflow ni DVC) ». _Reste éventuel : un remote dédié de data-versioning si besoin futur._
- [x] **État frontend — convention de state** — convention cadrée et documentée dans `frontend/README.md` (§ « Convention de state ») : React Query = état serveur ; Zustand = global client/UI/auth (+ session de jeu tolérée) ; useState = local. Hooks React Query de jeu **morts purgés** (useAkinetix/useBlindtest/useCodeManga/useParadox/useVision + tests). La « duplication » personnalisation était un **faux positif** (`/custom-config/` RQ vs `/profiles/me/` Zustand = concerns distincts). _Les `window.location.reload()` avaient déjà été éliminés._
- [x] **Performance frontend — fignolages** — `loading="lazy"` + `decoding="async"` ajoutés sur **54 `<img>` de contenu** (36 fichiers) ; héros/logos (HeroSection, Navbar, HomeNav) laissés en **eager** pour ne pas dégrader le LCP. **Memo : non appliqué** — pas de calcul coûteux en render (un seul `reduce` trivial), et le code mémoïse déjà là où ça compte (React.memo ×18, useMemo ×6) ; mémoïser à l'aveugle serait net-négatif sans profilage. _Le gros levier (précache PWA −60 %) était déjà fait._

## 🟢 Faibles

- [x] **Accessibilité — labels restants** — périmètre réel **115** `control-has-associated-label` sur **68 fichiers** (pas « quelques ») : tous étiquetés via `aria-label` FR pertinents (+ `role`/clavier pour les éléments interactifs non-natifs, `htmlFor`/`id` pour les labels). Règle **passée en `error`**. Au passage, les **23 autres erreurs eslint préexistantes** (sessions parallèles : `no-(non)interactive-element-interactions`, `no-explicit-any`, `no-unused-vars`, `label-has-associated-control`, `set-state-in-effect`) ont aussi été corrigées → **lint front entièrement vert** (`eslint .` exit 0), tsc vert, 188 tests OK.
- [~] **Couverture de tests frontend** — ✅ **outillage ajouté** : script `test:coverage` (`vitest run --project unit --coverage`), config v8 (reporters text/html/lcov, include/exclude), **seuils plancher anti-régression** (stmts 18 / branches 10 / funcs 14 / lines 18), `coverage/` gitignoré. **Baseline mesurée ≈ 18 % stmts** (1088/5981 ; 188 tests). ✅ **Campagnes ROI élevé** : round 1 (services/utils/hooks, +112) + round 2 (composants présentationnels : ToastContainer, drawers, multiverse-catalog, charts XAI…, +95) → **18.19 % → 24.09 % stmts** (188 → **395 tests**), plancher remonté à 24/15/22/24. ✅ **CI câblée** : étape `Unit Tests + Coverage` (`npm run test:coverage`) au job `frontend-checks` (projet unit jsdom) avec le gate de seuils, + upload Codecov non-bloquant (flag `frontend`). ✅ **Round 3** (pages : jeux, admin, social, media, research — +97 tests) → **24.09 % → 28.89 % stmts** (395 → **492 tests** ; branches 23 %), plancher remonté à 28/22/27/28. ⏭️ Reste (optionnel) : flows complexes restants (3D/canvas/WebSocket — ROI faible).
- [~] **Organisation des tests backend** — prémisse corrigée : **aucune duplication** (0 basename commun) ; `tests/core/` (cœur) et `tests/backend/` (couche Django) testent des **couches différentes**. Le vrai souci = quelques couches à **deux foyers** (core dans `tests/core` + `tests/backend/core` ; API dans `tests/api` + `tests/backend/api` ; pipeline dans `tests/pipeline` + `tests/pipeline_logic`). ✅ **Convention documentée** dans `tests/README.md` (un foyer par couche + cibles de consolidation). ⏭️ **Déplacement physique différé** jusqu'au merge de `coverage-consolidation` (qui écrit activement dans `tests/api`, `tests/backend`, `tests/pipeline` → conflits sinon ; gain fonctionnel nul, découverte via `testpaths=tests`).
- [x] **Logging MLOps** — centralisé via `backend/pipeline/logging_setup.py` (`setup_logging()`, format unique). Les 11 `logging.basicConfig` inline des scripts pipeline/MLOps + 2 fichiers comment-only remplacés par `setup_logging()` (niveau/emplacement préservés). mypy + ruff + black verts (474 fichiers). _(Le `logging_config.py` Django reste séparé, légitime.)_
- [ ] **E2E Playwright** — Chromium seul, pas de screenshots on failure ni d'artefacts CI.
- [ ] **K6 load test** présent mais hors CI, sans baseline.
- [ ] **`Dockerfile.dataflow`** — pas de HEALTHCHECK, fichier pipeline figé.
