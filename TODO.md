# TODO — Améliorations du projet Animetix

> Audit du 2026-06-21 (passe fraîche, 5 axes). Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).
>
> _Note de vérification : le `.env` contenant de vraies clés n'est PAS suivi par git (gitignored, jamais commité) — pas de fuite dans le dépôt, pas de rotation d'urgence. `error_latent.html` et `.coverage` ne sont pas suivis non plus._

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [ ] **Repo — 125 Mo de données suivies dans git** _(vérifié)_
  - `data/processed/filtered_characters.json` (40 Mo), `refined_characters.json` (30 Mo), `clean_characters.json` (24 Mo), etc. Artefacts générés qui gonflent l'historique et ralentissent les clones.
  - Migrer vers Git LFS **ou** `git rm --cached` + régénération au build ; documenter le téléchargement dans le README.
- [ ] **Sécu — `exec()` sur du code généré par LLM (surface RCE)**
  - [self_evolving_compiler.py:62](backend/core/domain/services/self_evolving_compiler.py#L62) exécute du source dynamique (`# nosec B102`). Une injection de prompt en amont permettrait l'exécution de code arbitraire.
  - Valider l'AST avant exécution (interdire `import`/`os`/`subprocess`), sandboxer (RestrictedPython), ou désactiver la feature en prod.
- [x] **Archi — violations de la frontière hexagonale (domaine → infra)** ✅ _(2026-06-22)_
  - `manga_service` → `MangaRepositoryPort` + `DjangoMangaRepositoryAdapter` (toute la persistance ORM derrière le port ; retourne des modèles opaques pour préserver la sérialisation DRF, `DoesNotExist`→`None`).
  - `voice_ingestion_service` → `VoiceProfileRepositoryPort` + `DjangoVoiceProfileAdapter` ; service câblé via `container.core.voice_ingestion_service`.
  - `llm_service` → `UserContextPort` + `MiddlewareUserContextAdapter` (plus de reach dans `animetix.middleware` ; `user_id`/`tier` explicites prioritaires, quota préservé).
  - Aucun des 3 fichiers du cœur n'importe plus Django/animetix. Vérifié : wiring conteneur OK, tests llm/labs/manga verts.
- [ ] **Archi — code de test (Mock/MagicMock) dans un service de prod**
  - [agentic_rag_service.py:58-104](backend/core/domain/services/agentic_rag_service.py#L58) reconstruit des agents pour les mocks dans `__init__`. Fragile, ne devrait jamais tourner en prod.
  - Sortir la logique mock vers des fixtures de test.

- [x] **Consolidation de la couverture backend → 75 % — ✅ ATTEINT : 75,33 %** _(branche `worktree-coverage-consolidation`, 2285 tests verts)_
  - **Mesure finale 2026-06-21 : 75,33 % global** (`--cov=backend`, le flag exact du gate CI ; 19 831 / 26 325 lignes). Point de départ 55,05 %.
  - ⚠️ **Méthodologie** : mesurer **par chemin** (`--cov=backend`), PAS par nom de package (`--cov=pipeline` sous-compte les modules importés `backend.pipeline.*` à 0 % à cause du dual-namespace ; CI utilise déjà `--cov=backend`, donc le gate n'est pas affecté).
  - Modules portés à 100 %/quasi cette campagne : `auth` (0→100), games `vision`/`akinetix`/`blindtest` (100), `librarian`, `akinetix_rl_service`, `tasks_views`, `creative_tasks` (100), `dpo_dataset_compiler` (81→95), `api/core` (79→100), `video_analysis` (44→100), `index_otaku_knowledge` (51→96).
  - [x] ✅ Flaky e2e `test_speech_to_speech_live_consumer` **corrigé** : cause racine = accès DB du background task ASGI/auth sans `django_db` (visible seulement selon l'ordre de suite). Fix : `@pytest.mark.django_db(transaction=True)` + mock du `voice_cloning_service` lourd + mock `process_client_audio` (anti-ffmpeg). Vert sur 3 runs `tests/backend/` complets.
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

- [ ] **API — fuite de stacktrace + permission par défaut trop ouverte**
  - `return Response({"error": str(e)}, status=500)` expose l'exception au client : [labs.py:1021](backend/api/animetix/api/labs.py#L1021), [core.py:196](backend/api/animetix/api/core.py#L196) → `logger.exception()` + message générique.
  - Permission DRF par défaut = `IsAuthenticatedOrReadOnly` ([settings.py:250](backend/api/animetix_project/settings.py#L250)) : tout lisible sans auth sauf override → passer à `IsAuthenticated` par défaut, `AllowAny` ciblé.
- [ ] **Backend — `except Exception:` trop larges + constantes dupliquées**
  - Nombreux catch-all génériques masquant les vrais bugs → resserrer sur des exceptions spécifiques.
  - `MAX_IMAGE_SIZE` / allow-lists MIME dupliquées entre [labs.py](backend/api/animetix/api/labs.py) et [core.py](backend/api/animetix/api/core.py) → centraliser dans `backend/core/constants.py`.
- [ ] **Backend — `UnifiedInferenceAdapter` god object**
  - 8 mixins, ~476 lignes ([unified_inference_adapter.py:30](backend/adapters/inference/unified_inference_adapter.py#L30)) ; MRO fragile, dur à tester → composition plutôt qu'héritage multiple.
- [x] **Frontend — `fetch()` brut qui contourne `apiClient`** _(audit étendu : ~15 sites traités)_
  - Problème : `fetch()` direct → pas de CSRF, pas de header auth Firebase, pas de toast d'erreur (cf. [apiClient.ts](frontend/src/utils/apiClient.ts)).
  - [x] `SearchBar` (image search) → `searchMediaByImage()` dans `api.ts`.
  - [x] **Migrés vers `apiClient`** : `useAdminEval`, `SimulatedAdBanner` (×2) & `SponsorStreamModal` (factorisés dans `billingService.logAdEvent`, `skipToast`), `useCustomConfig` (→ `utilsService.updateConfig`), `FinancialDashboardPage`, `MonitoringConsolePage`, `ExplorePage`, `useTachideskExplorer` (9 appels, control-flow préservé), `MangaLibraryPage` (×2). Tests des 4 fichiers concernés mis à jour (mock `apiClient`).
  - [x] **Laissés en `fetch` brut à dessein** (assets binaires / cross-origin — `apiClient` parserait en JSON et fuiterait le token à un tiers) : `AudioLabPage` (sample audio, + toast d'échec ajouté), [MangaVoicePage.tsx:59](frontend/src/pages/labs/MangaVoicePage.tsx#L59) (`sample_url`), [offlineLibrary.ts:117](frontend/src/features/manga-reader/offline/offlineLibrary.ts#L117) (`image_url` blob), [api.ts:357](frontend/src/api.ts#L357) (proxy binaire).
  - [ ] _Reliquat optionnel_ : harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy `api.ts:357` (comme fait pour `AudioLabPage`).
- [ ] **Frontend — état local fragmenté**
  - [AudioLabPage.tsx:64](frontend/src/pages/labs/AudioLabPage.tsx#L64) (~13 `useState`) ; anti-pattern `JSON.stringify` en render dans [SynapticLabPage.tsx:110](frontend/src/pages/labs/SynapticLabPage.tsx#L110) → `useReducer`/hook dédié.
- [x] **CI — gaspillage et robustesse**
  - [x] `concurrency: cancel-in-progress` ajouté (groupe `workflow-ref-event` pour ne pas annuler un deploy manuel via un push main).
  - [x] Cache pip (`setup-python cache: pip`, clé `requirements.txt`) sur `test`/`integration-test`/`perf-test` + retrait des `--no-cache-dir` → torch/torchvision et requirements ne sont plus re-téléchargés à chaque run.
  - [x] `timeout-minutes` ajouté : `test` 45, `integration-test`/`perf-test` 30.
  - [x] Gate `--cov-fail-under=75` **confirmé cohérent** : couverture réelle = **75,33 %** (cf. [HISTORY](docs/HISTORY.md)), le gate passe et garde contre les régressions. Commentaire périmé (« ~56 %, intentionnellement rouge ») corrigé.

## 🟢 Faibles

- [ ] **A11y & logs frontend** : `<img>` sans `alt`, boutons admin sans `aria-label`, `console.error` laissés en prod (~41 fichiers).
- [x] **Deps**
  - [x] **Pins** : `requirements.in` entièrement épinglé — `transformers==4.57.6`, les 4 `google-cloud-*`, `apache-beam==2.74.0`, `dbt-core/sqlite/bigquery` figés aux versions **déjà résolues** par pip-compile. Le lockfile `requirements.txt` reste **byte-identique** (aucun recompile : ce serait dangereux sur Windows car le lock cible Linux/Py3.12) ; un futur recompile sera déterministe.
  - [x] **Doublon opencv** : `ultralytics` force `opencv-python` (GUI, besoin de `libGL` absent de l'image slim) à côté de notre `opencv-python-headless`. Un recompile ne peut PAS le retirer (dep transitive forcée). Fix au niveau des 3 Dockerfiles (`Dockerfile`, `.brain`, `.dataflow`) : après l'install, `pip uninstall` des **deux** (ils partagent les fichiers `cv2/`) puis réinstall de **headless seul** (version lue depuis le lockfile). Image plus légère + `import cv2` sans `libGL`.
  - _Note vérif_ : build-time validé par le job CI `docker-build` (pour `deploy/Dockerfile`) ; non vérifiable en runtime localement (Windows ≠ Linux/libGL). `.brain`/`.dataflow` ne sont pas buildés en CI.
- [ ] **DX** : pas de Prettier ni `.editorconfig` ; badge README « Python 3.11+ » alors que CI/pyproject ciblent 3.12.
- [ ] **Couverture frontend — élargir** _(ongoing optionnel ; 520 tests, seuils 29/22/28/29 — cf. [HISTORY](docs/HISTORY.md))_
  - [x] Lot 1 — services jeux (`akinetix`, `vision`, `covertest`, `animinator`) + `media` ; hooks logique (`useAchievements`, `useMediaDetail`, `useCovertest`).
  - [x] Lot 2 — hooks react-query restants (`useCurationTickets`, `useDPO`, `useSocialDashboard`, `useProfile`, `useLeaderboard`, `useDailyChallenge`, `useHealth`).
  - Total +28 tests (492→520) ; seuils remontés statements 28→29, functions 27→28, lines 28→29.
  - Reste (ROI décroissant) : flows complexes 3D/canvas/WebSocket (`useTachideskExplorer`, `useSocket`, `useMultiverseCatalog`) ; continuer à remonter le plancher au fil de l'eau.
- [x] **Organisation des tests backend — consolidation physique** ✅ _(2026-06-21)_
  - Fusionné `tests/backend/core`→`tests/core`, `tests/backend/api`→`tests/api`, `tests/pipeline_logic`→`tests/pipeline` via `git mv` (historique préservé). Collection pytest **inchangée à 2313 tests**, échantillons rejoués verts (200 + 74 passed). `tests/README.md` mis à jour. Reste à trancher (séparé) : `tests/backend/views/…` → `tests/api/` ou conserver.
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. À purger lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).
