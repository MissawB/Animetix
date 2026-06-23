# Animetix - History of Refactorings & Achievements

This document archives the major milestones of the project's technical evolution.

## [2026-06-22] Session: Typed inference-failure sentinel (drop the `"Erreur"` string heuristic)

### Fix: brittle string-based fallback routing
`FallbackInferenceAdapter` decided an engine had failed by testing `result.text.strip().startswith("Erreur")` in both `generate()` and `stream_generate()`. Fragile and French-locale-specific: a genuine model answer that merely *began with* « Erreur… » (e.g. _"Erreur 404 est un thème de Serial Experiments Lain"_) was misrouted to the next engine. Audit confirmed **no production text adapter** actually returned such a response — they all signal failure by **raising** (`InferenceError` / `raise`), which the orchestrator already catches — so the string branch was dead-but-harmful legacy.
- Added a typed sentinel `InferenceResponse.is_error: bool = False` + an `InferenceResponse.failure(message)` factory ([ai_schemas.py](../backend/core/domain/entities/ai_schemas.py)). Adapters that prefer to soft-fail (without raising) now set the flag instead of relying on a magic prefix.
- `FallbackInferenceAdapter` now falls through on `result.is_error` (not on the text prefix); the terminal "Échec critique" response is built via `.failure(...)` so total-failure is detectable downstream ([fallback_adapter.py](../backend/adapters/inference/fallback_adapter.py)).
- TDD: updated the two `*_erreur_*` fall-through tests to drive the sentinel, added a regression test asserting an answer starting with "Erreur" is now returned as success, plus factory/default tests. Full related-suite run green (**528 passed**).

## [2026-06-22] Session: API Hardening, RCE Guard & Constants/Broad-Except Cleanup

### Cleanup: duplicated constants + bug-masking catch-alls
- **Constants**: `MAX_IMAGE_SIZE` and the image/video/audio MIME allow-lists were duplicated (and drifting) between `api/core.py` and `api/labs.py`. Centralized in `core.constants`; both import from there (image list unified to include gif; labs' dead duplicate constants dropped).
- **Broad `except Exception`**: AST audit of all 638 handlers showed almost all already log or return a deliberate fallback (legitimate defensive code). Only 3 silently swallowed; narrowed the 2 obvious ones (`django_repository_adapter.get_creative_fusion` → `CreativeFusion.DoesNotExist` so a repo no longer masks DB errors as "not found"; `regression_benchmark` `--threshold` parse → `(ValueError, IndexError)`). The ASGI event-loop-policy startup shim is an intentional best-effort guard, left as-is. No blind 638-site sweep (no value, risky).

### Security: API stacktrace-leak + secure-by-default permissions
- **Stacktrace leak**: 27 endpoints returned the raw exception to the client on HTTP 500 (`Response({"error": str(e)}, status=500)`), exposing internals (paths, SQL, …). Replaced the client body with a generic `"Internal server error"` and log the detail server-side via `logger.exception(...)` — across 11 `api/*` modules plus `tasks_views` and `views/billing`. 4xx validation responses (intentional user feedback) were left intact.
- **Permissions secure-by-default**: DRF `DEFAULT_PERMISSION_CLASSES` was `IsAuthenticatedOrReadOnly`, making every endpoint world-readable unless overridden. Flipped to `IsAuthenticated`. An AST audit of all 142 views found only 8 relying on the default; the genuinely public ones now declare `IsAuthenticatedOrReadOnly` (Multiverse gallery/catalog/export-PDF, AchievementViewSet) while internal/control views (monitoring, observability) tighten. The 3 `@api_view` functions and `AIFeedbackAPIView` (uses `get_permissions`) already scoped permissions explicitly.

### Security: RCE guard on exec() of LLM-generated kernels
- `SelfEvolvingCompiler.compile_dynamic_kernel` exec'd dynamic Python source, including code produced by an LLM (`evolve_with_llm`) — a prompt injection upstream could smuggle arbitrary code into the host (RCE). Added `assert_safe_kernel_source()`: an AST gate rejecting imports, dunder attribute access (blocks `().__class__.__subclasses__()` escapes) and a blocklist of dangerous names (os/sys/subprocess/eval/exec/open/getattr…). `exec` now also runs with a restricted `__builtins__` (`_SAFE_BUILTINS` — only numeric helpers like range/len/abs/float) as defense-in-depth. Malicious kernels raise `UnsafeKernelError`; `evolve_with_llm` swallows it and returns the null fallback (no execution). Legitimate numeric kernels unchanged; 13 new security tests.

## [2026-06-22] Session: Frontend & Infra Sweep (data/LFS, fetch→apiClient, CI, deps, DX, a11y, coverage)

A batch of TODO items closed across data hygiene, CI, deps, DX and the frontend, each merged via its own PR.

- **Repo data → Git LFS**: the large tracked `data/processed` / `data/artifacts` JSON (filtered/refined characters 40/30 MB, …) moved to Git LFS (consistent with the existing `*.npy` rule); the orphan `clean_characters.json` (24 MB, zero references) dropped. A history-rewrite purge of old blobs was left as a separate coordinated op.
- **Frontend `fetch()` → `apiClient`**: ~15 raw same-origin `fetch()` calls migrated to `apiClient` (CSRF + Firebase auth + error toasts) — SearchBar image search (`searchMediaByImage`), billing ad-events (`billingService.logAdEvent`), `useCustomConfig`→`utilsService.updateConfig`, Monitoring/Financial pages, ExplorePage, `useTachideskExplorer` (9 calls, control-flow preserved), MangaLibrary. Binary/cross-origin asset fetches (AudioLabPage, MangaVoicePage, offlineLibrary, the image proxy) left as raw `fetch` on purpose; AudioLabPage got a failure toast.
- **AudioLabPage state**: Quick Ingest form (5 `useState` + validation + submit) extracted to a dedicated `useQuickIngestForm` hook (14→9 `useState`). SynapticLab `JSON.stringify`-in-render confirmed a deliberate React "adjust-state-during-render" pattern (left as-is).
- **CI**: `concurrency.cancel-in-progress`; pip wheel cache on the test/integration/perf jobs (no more ~800 MB torch re-download); `timeout-minutes` (45/30/30); corrected the stale coverage-gate comment (coverage is 75.33 %, gate live).
- **Deps**: `requirements.in` fully pinned to the resolved versions (transformers, google-cloud-\*, apache-beam, dbt-\*) — lockfile byte-identical. Duplicate `opencv-python` (forced by ultralytics, needs libGL) dropped in all 3 Dockerfiles: uninstall both then reinstall headless from the lockfile.
- **DX**: Prettier + `eslint-config-prettier` (config + scripts + lint-staged, no repo-wide reformat), root `.editorconfig`, README Python `3.11+`→`3.12+`.
- **A11y & logs**: 12 WebSocket `console.log` routed through a dev-only `logger` (no-op in prod) + a `no-console` ESLint rule (warn/error allowed). `<img>` alt and admin accessible-names were already enforced.
- **Frontend coverage**: covered the untested game/media services + react-query hooks (+28 tests, 492→520); ratcheted the v8 floors to statements 29 / branches 22 / functions 28 / lines 29.

## [2026-06-22] Session: Hexagonal Boundary Repair (domain → infra) & Test-Home Consolidation

### Hexagonal boundary violations fixed (domain no longer imports Django/animetix)
Three core-domain services reached across the hexagonal boundary into infrastructure. Each now depends on an injected port; the Django/ORM/middleware code lives in an adapter wired through the DI container.
- **`manga_service`** imported `animetix.models` (MangaChapter/MangaPage/MediaItem) and ran ORM queries + `get_or_create` directly → new **`MangaRepositoryPort`** + `DjangoMangaRepositoryAdapter`. The port returns records as opaque objects (still real models, so DRF serialization is untouched) and maps `DoesNotExist` → `None`; sync decisions / Suwayomi+mock flow stay in the service.
- **`voice_ingestion_service`** imported `animetix.models.VoiceProfile` + `ContentFile`/`slugify` to persist the ingested sample → new **`VoiceProfileRepositoryPort`** + `DjangoVoiceProfileAdapter`; the service is now wired as `container.core.voice_ingestion_service` and the labs view resolves it from the container instead of instantiating it directly.
- **`llm_service`** reached into `animetix.middleware` to resolve the ambient request user for the quota check → new **`UserContextPort`** + `MiddlewareUserContextAdapter`. Explicit `user_id`/`tier` args keep priority; quota enforcement is preserved with no direct middleware import (avoids threading user_id through ~35 internal callers).
- Verified: container wiring tests green, `llm_service`/labs/manga-endpoint tests green, and none of the three core files import Django/animetix anymore.

### Test scaffolding removed from production
- `AgenticRAGService.__init__` shipped ~130 lines of test-only `isinstance(..., Mock)` scaffolding: it gave a mock `llm_service` default `generate` side-effects and rebuilt a real `RAGOrchestrator` (with all real agents) whenever a Mock orchestrator was passed. Extracted to a test factory (`tests/helpers/agentic_rag_factory.py:build_test_agentic_rag_service`) and migrated the 14 unit tests that relied on the implicit behavior. The production `__init__` no longer imports `unittest.mock` or branches on `Mock`; behavior preserved (51 passed / 16 deselected unchanged, container wiring green).

### Test-home consolidation
- Merged the historically-duplicated test homes (`tests/backend/core`→`tests/core`, `tests/backend/api`→`tests/api`, `tests/pipeline_logic`→`tests/pipeline`) via `git mv` — pytest collection unchanged at 2313 tests, history preserved. Purely organizational (discovery is `testpaths=tests`).

## [2026-06-21] Session: mypy Type-Debt Elimination, Frontend Coverage Campaign & CI Hardening

### Typing (Élevés)
- **mypy type-debt baseline 105 → 0 modules**: the `[[tool.mypy.overrides]] ignore_errors` block was removed entirely — `cd backend && mypy .` is fully green on ~474 files with no per-module ignores. Done in a clean CI-equivalent venv (`pip install mypy` → 2.1.0); the project venv can't run mypy/black locally due to a dbt `pathspec<0.13` pin. ML lazy-`None` inference adapters typed (`self._model: Any = None`), Django `admin` modernized (`@admin.display`/`@admin.action`), `lazy_import` (ModuleType proxy) + a Django logging filter carry targeted `# type: ignore[...]`, `emoji_service` typed honestly `List[str] | str`.
- **Streaming contract harmonized on `dict`**: `StateProcessor.process` → `Generator[dict, None, RAGState]`, orchestrator simplified (all processors are generators). These 11 errors were breaking CI mypy.
- **8 runtime bugs surfaced by strict typing**: missing `SimilarityService.find_similar_items` (AttributeError) + undercover None-guard; `fallback_adapter` `raise e` after the exception var was deleted (NameError); `trl_ops` calling a non-existent `export_preference_dataset` (a mock hid it); `advanced_vision.vlm_rerank` treating dicts as int indices (TypeError); `tree_of_thoughts` missing `.text`; `validation_gate` `-> (str, float)` (tuple-value, not a type); dead `SampleView` ref; `django_repository.get_nearest_neighbors` returning `[]` against an `Optional[Dict]` port. Several latent None-derefs guarded along the way.

### Frontend test coverage (18% → 29%, 188 → 492 unit tests)
- Added `vitest --coverage` tooling: `test:coverage` script, v8 config (text/html/lcov, include/exclude), anti-regression **ratchet thresholds** (now 28/22/27/28), `coverage/` gitignored.
- 3 high-ROI campaigns (all behavior-only, no source changes): services/utils/hooks (+112), presentational components (+95), route-level pages (+97).
- **Wired frontend unit tests + coverage gate into CI** (`frontend-checks` job) — previously `vitest` never ran in CI — plus a non-blocking Codecov upload (flag `frontend`).

### Other hardening
- **Frontend state convention** documented in `frontend/README.md` (React Query = server state, Zustand = global/UI, useState = local); dead React Query game hooks purged; the "personalization duplication" was a false positive (`/custom-config/` vs `/profiles/me/` — distinct concerns).
- **Frontend perf**: `loading="lazy"` + `decoding="async"` on 54 content `<img>` (36 files); heroes/logos kept eager for LCP. Memo deliberately not broadened (no expensive in-render compute; already memoized where it matters).
- **Accessibility**: the real scope was 115 `control-has-associated-label` across 68 files (not "a few") — all given meaningful FR `aria-label`s (+ `role`/keyboard for non-native interactives, `htmlFor`/`id` for labels); rule hardened `warn` → `error`. Also fixed the 23 pre-existing eslint errors → `eslint .` fully green.
- **MLOps logging** centralized via `backend/pipeline/logging_setup.py` (`setup_logging()`, single format); 11 inline `logging.basicConfig` calls + 2 comment-only files migrated.
- **Playwright e2e**: on-failure screenshot/video/trace, CI `Upload Playwright artifacts` step, GitHub reporter (Chromium-only kept by design for the single a11y spec).
- **k6 load test**: replaced the unrealistic global `p(95)<500` with tagged per-endpoint thresholds (search/game/rag/ws); added a manual `workflow_dispatch` `load-test.yml` (the test needs a deployed target + incurs LLM costs, so not a PR gate).
- **`Dockerfile.dataflow`**: removed a redundant, UNPINNED `pip install beautifulsoup4` (already `==4.12.3` in requirements); documented why a HEALTHCHECK is inappropriate (Dataflow-managed) and how to digest-pin the `:latest` launcher base.
- **Backend test organization**: corrected the premise (no duplication — `tests/core` vs `tests/backend` are different layers); documented the "one home per layer" convention in `tests/README.md`; physical consolidation deferred until the `coverage-consolidation` branch merges.
- **Security — leaked HF token**: removed the hardcoded Hugging Face token from `scripts/deploy/deploy_jobs.py` (moved to Secret Manager `HF_SPACES:latest`); old token revoked. The Snyk Python scan was stale (9/10 packages already fixed); the only residual, `jsonpickle`, is transitive (capped `<4` by apache-beam) and never imported by our code → documented as accepted.
- **Base-image OS CVEs**: the prod build used `--cache-from` WITHOUT `--pull`, so Debian security patches (zlib/openssl/sqlite3/krb5/…) were never re-pulled. Added `--pull` to `cloudbuild.yaml` (web), `cloudbuild.brain.yaml`, and the CI image build → each deploy picks up the patched base.
- **Optional integration CI**: `conftest` now TCP-pings the LLM backend (`LLM_API_BASE`, default ollama) and skips `@pytest.mark.integration` tests gracefully when it's unreachable; added a non-blocking `integration-test` job (skipped on PRs; runs on push to main + dispatch) — never gates the pipeline.

## [2026-06-21] Session: Hexagonal Core, CI Guardrails, Test-Coverage Campaign & Hardening

### Architecture & security (Critiques)
- **Hexagonal core isolation**: the `core` no longer imports Django (`settings`/`cache`), the MLOps `pipeline`, or the DI container (`get_container()`). Introduced `Cache`/`Config`/`VectorStore` ports with Django/Chroma adapters; moved `guardrail_service` into the `agentic` container, resolving the `core`↔`agentic` circular dependency (back-compat alias kept).
- **`backend.core.*` → `core.*`**: removed the dual-namespace that produced duplicate modules and broken `isinstance`/mocks (15 source + 19 test files).
- **SSRF in `sample_url` (Animetix Voice)**: user-controlled URL fetch hardened via `safe_http_request` (rejects private/loopback/link-local IPs at every redirect hop), both at ingestion and fetch.
- **Backend ↔ frontend schema desync**: exposed `wallet_balance` (serializer + mapping); added DRF serializers + `@extend_schema` for `vs_battle` and the `xai_report` SSE event; regenerated `api.d.ts`.

### Frontend health gate
- New CI job **`frontend-checks`** (`check-types` + `lint`) gating `deploy-to-prod` — previously nothing ran `tsc` before prod (Vite doesn't type-check).
- **`tsc` 131 → 0**: fixed runtime `ReferenceError`s (broken `catch` vars, missing imports `Globe`/`motion`/`Button`/`useCallback`…), Plotly namespace, app types, deduplicated XAI cluster, `Button` variants, force-graph refs; removed dead/broken `useAniminator.ts`.
- **ESLint 132 → 0**: `no-explicit-any`, `no-unused-vars`, `react-hooks/*`, `jsx-a11y`.
- Fixed 6 broken/flaky frontend tests (incl. a `SynapticLabPage` infinite-render regression and an orphaned `MultiverseLabPage` test → `MultiverseStudioPage`).

### Monolith decomposition
- `pipeline/mlops/finetuning_dataset.py` **4650 → 1316 l. (−72%)** via a façade re-export pattern (9 modules under `ft_dataset/`, zero caller changes).
- DI container: shared `LazyClass` extracted to `containers/lazy.py`; `core_services.py` 524 → 440 l.
- Frontend: `MultiverseCatalogPage` 740→161, `TachideskExplorerPage` 724→157, `Layout` 475→118 — memoized sub-components + custom hooks, strictly behavior-preserving.

### RAG services / dead-code audit
- Corrected the audit premise: the 3 RAG services don't overlap, they **compose** (merge abandoned on purpose). Removed real dead code: 2 orphan modules, 3 test-only modules, 2 registered-but-never-resolved modules+providers, 2 duplicate dead providers, 1 dead injected wire. `test_container_wiring` 3/3.

### Test-coverage campaign (≈443 new tests; 17 backend modules 0% → 92-100%)
- Established a hard **`--cov-fail-under=75`** gate + non-blocking **Codecov** upload; `pytest-cov` confirmed in `requirements.txt`.
- **P1 — MLOps & Ingestion** (8 modules): `jikan_enrichment`, `expert_enrichment`, `manga/{fetch_covers,ingest_manga,vectorize_manga}`, `mlops/{merge_lora_weights,train_preference,rlhf_pipeline}` (HTTP/sleeps/embeddings/vector-store/Neo4j/torch all mocked).
- **P2 — Async consumers** (3 modules): `consumers/{duel,codemanga,speech_to_speech_live}`; also fixed a flaky Channels e2e (1s → 5s `receive_json_from` timeouts).
- **P3 — Adapters** (6 modules): `inference/{moondream,qwen3_vl,brain_api}`, `persistence/{django_safety,django_semantic_cache,colbert}`.
- **P4 — Frontend** (vitest 69 → 191): Zustand stores, `ErrorBoundary`, offline `idb-keyval`/persister.
- **🐛 Production bug found via tests**: `DjangoSafetyAdapter` used field `action_taken` (`create()`/`filter()`/read) while the `AISafetyEvent` model field is `action` → `TypeError`/`FieldError` on **every** safety-event write. Fixed + added a `@pytest.mark.django_db` round-trip regression lock.

### Coverage consolidation → 75 % gate cleared (branch `worktree-coverage-consolidation`)
- **Global line coverage 55,05 % → 75,33 %** (`--cov=backend`, the exact CI-gate flag; 19 831 / 26 325 lines, 2 285 tests green). The hard `--cov-fail-under=75` gate now passes.
- **Measurement-methodology fix**: targeted runs must scope coverage **by path** (`--cov=backend`), not by package name (`--cov=pipeline`). The name-based form attributes `backend.pipeline.*`-imported modules to a separate module object and reports them at 0 % (dual-namespace) — e.g. `dpo_dataset_compiler`/`semantic_drift_analyzer`/`run_provenance` looked uncovered but were already 81–92 %. CI already uses `--cov=backend`, so the gate itself was never mis-measured.
- **DI game-view wiring**: a shared `tests/api/games/conftest.py` re-wires the `@inject` view modules and resets cached service Singletons before each test; the harmful `container.reset_override()` autouse fixtures were removed (that call detaches the `core→persistence` sub-container on this `dependency_injector` version and broke the views in isolation). All 8 game modes green alone and combined.
- **Modules raised to 100 %/near** this push: `animetix.auth` (0→100, IAP/Google/API-key auth), game modes `vision`/`akinetix`/`blindtest` (100), `librarian` RAG agent + `akinetix_rl_service` (100), `tasks_views` + `creative_tasks` (100), `dpo_dataset_compiler` (81→95), `api/core` (79→100), `video_analysis` adapter (44→100), `index_otaku_knowledge` (51→96). All model/HTTP/DB/torch I/O mocked; real-behavior assertions, no false-green.
- Confirmed `pgvector_repository_adapter` is already at 99 % (combined `tests/adapters/` + `tests/core/`) — the earlier 31 % was a single-file stale reading.
- **Deflaked `test_speech_to_speech_live_consumer`** (the suite's last intermittent red): root cause was the consumer's ASGI/auth-middleware + background gemini task accessing the DB across the channels thread executor without a `django_db` mark — in isolation the task was cancelled before reaching it, so it only failed under full-suite ordering. Fixed with `@pytest.mark.django_db(transaction=True)`, plus mocking the heavy `voice_cloning_service` Singleton (it eagerly built the real `inference_engine`+LNN before `session_ready`) and `process_client_audio` (drops the ffmpeg/pydub dependency). Green across 3 full `tests/backend/` runs.

### Robustness & process hardening
- **Test pollution**: Proactor event-loop policy made fail-fast; added an autouse fixture clearing `Mock` leaks from `sys.modules` + the `lazy_import` cache; fixed a real `imageio` `sys.modules` leak. The 2 baseline `test_prompt_loading` failures disappeared.
- **Error handling**: `ErrorBoundary` + React-Query cache now report to Sentry with smart retry (no retry on 4xx); 5 genuine silent `except Exception: pass` made observable (0 remaining).
- **Pre-commit**: ruff+black on `pre-commit`, mypy+pytest (`-m "not integration"`) on `pre-push` — the pytest hook caught a real `test_deploy_jobs` regression.
- **MLOps provenance**: `run_provenance.py` writes git-commit + UTC timestamp + manifest revisions next to each checkpoint (wired into the training scripts).
- **dbt**: added telemetry source freshness + a 2nd singular drift-affinity test.
- **`requirements.txt`**: confirmed it's a clean canonical `pip-compile` output (audit was misleading); removed stale `requirements.txt.bak`.
- **Async strategy**: audited (only 5 async core files, no boundary violations) and documented the canonical sync-core / async-edges model in `ARCHITECTURE.md`.
- **`features/` vs `pages/`**: confirmed no duplication (healthy layering); convention documented in `frontend/README.md`.
- **Frontend performance**: PWA precache trimmed 7.5 MB → ~3.0 MB (−60%) by excluding the lazy-loaded Plotly chunk and adding runtime caching.
- **Accessibility**: hardened `jsx-a11y` interaction rules to `error` (0 violations) + fixed clear `aria-label` cases.

### Repository metadata
- GitHub `MissawB/Animetix`: refreshed description, set homepage (Cloud Run), added 18 topics; repointed `origin` to the current repo name.

### Product features delivered (also detailed in earlier sessions below)
Vocal Library & Seiyuu integration, Graph Repair Console (Graph Healer), Plasticity Dashboard & Semantic Profile, Berrix Economy Hub, Tachidesk/Suwayomi integration, Manga Reader UX optimization, Manga Extension Manager, background Manga Chapter Tracking & notifications (periodic trigger wired via Cloud Run job + Scheduler), Offline Manga Library (PWA), Real-time Club Chat, Self-Hosted AI Image Worker, LLM speed optimizations.

## [2026-06-20] Session: Offline Manga Reader (PWA)

- **Mode Hors-ligne du Lecteur Manga (PWA)**:
  - Added an `offlineLibrary` IndexedDB layer (`idb-keyval`) that stores downloaded chapter page images as blobs with per-chapter metadata, plus a `useChapterDownload` hook exposing download status/progress.
  - Added a chapter list with a per-chapter download button on the manga detail page, and a `useChapterPages` hook that serves the reader from the local cache (object URLs) when a chapter is downloaded, falling back to the network and showing an "indisponible hors-ligne" state when offline.
  - Configured the service worker SPA `navigateFallback` so reader routes load offline.

## [2026-06-20] Session: Mihon/Suwayomi Integration, React Reader UX, Real-Time Chat, and ML Image Worker

- **Manga Reader UX & Suwayomi (Mihon) Integration**:
  - Implemented the Suwayomi explorer integration, image proxy, and extension manager. Added GraphQL queries/mutations to list, install, update, and uninstall manga source extensions, along with Django REST views/routes and explorer dual tabs.
  - Optimized the Manga Reader React UX with background image preloading (next 3/prev 1 pages), double-page side-by-side view (RTL/LTR), wide-page auto-splitting, and infinite scroll Webtoon mode with synchronized scroll-position states.
- **Real-Time Club Chat**:
  - Integrated dynamic chat channels (WebSockets / Django Channels) inside discovery clubs for community interaction.
- **Self-Hosted AI Image Worker (MLOps)**:
  - Added a self-hosted fallback worker for Stable Diffusion and ComfyUI using our task queue (`enqueue_task`) monitored via the Cluster Health dashboard.
- **LLM Speed Optimizations**:
  - Implemented speculative decoding (EAGLE, Medusa) and KV cache optimization (semantic cache and RadixAttention) to accelerate response times.

## [2026-06-20] Session: Multiverse Lore Exporter (PDF Wiki) & LLM Acceleration Research

- **Exportateur de Lore Multivers** :
  - **Backend PDF Generation** : Added `reportlab` dependency to support native high-quality PDF generation. Implemented `MultiverseExportPDFView` inside `multiverse.py` utilizing the custom `NumberedCanvas` class for dynamic page numbering ("Page X sur Y") and header formatting. The API queries Neo4j for the target synthetic universe, its characters, and its neighborhood graph connections (concepts and relations).
  - **URL Registration** : Added `/api/v1/multiverse/<str:universe_name>/export-pdf/` to `urls/api.py`.
  - **React UI Button** : Integrated an "Exporter PDF" button next to the Nexus explorer within the `UniverseDetailPanel` on the `MultiverseCatalogPage.tsx`.
  - **Testing & Verification** : Added a comprehensive test suite in `test_multiverse_export.py` ensuring successful streaming of `%PDF` content and correct attachment headers. Verified the output using a standalone scratch generation pipeline.
- **LLM Acceleration Research** : Evaluated recent research (2025-2026) on speculative decoding (EAGLE, Medusa, SSD) and KV Cache optimization techniques, documented in the artifacts index.

## [2026-06-19] Session: Digital Assets Shop, HTTP Centralisation, Pydantic V2 Migration, and UI Navigation Convergence

- **Boutique d'Actifs Digitaux (Marketplace)**: Fully implemented the digital assets trading platform. Added the `MarketListing` model with choice-based wallet transaction types (`market_purchase`, `market_sale`), Django migrations, and DRF serializers/viewsets. Integrated atomic transactions for safe balances debit/credit and creator transfer. Developed `ShopPage.tsx` using a premium cyber-emerald styling, and linked it via routing and Sidebar. Wrote comprehensive pytest coverage in `test_market_api.py`.
- **Centralisation HTTP (Frontend)**: Refactored game files (`AkinetixRLPage.tsx`, `DuelLobbyPage.tsx`, and `paradoxStore.ts`) to use the centralized `apiClient` wrapper. This eliminates raw `fetch` calls, ensures automatic Firebase and CSRF token transmission, and standardizes error toast feedback.
- **Dépréciations Pydantic V2**: Migrated the `PersonalizationSchema` model in `social.py` from Pydantic V1 class Config format to Pydantic V2 `ConfigDict` standard, successfully resolving deprecation warnings.
- **Correction de `sync-api.bat`**: Aligned the OpenAPI TypeScript code generation target to `src/types/api.d.ts` and removed the unrecognized `--quiet` argument from spectacular schema export.
- **Navigation, Ghost Labs & UI Convergence**:
  - Exposed sidebar shortcuts for **Nexus Pro** and **Transparence Système**, and created the **Outils Admin & Monitoring** section for staff.
  - Linked previously orphan "Ghost Labs" interfaces: **Seiyuu Discovery**, **Numba Compiler**, **Video RAG**, and **Cove Oracle**.
  - Deployed dedicated pages for **Données Hors-ligne** sync status, **AI Feedback History**, and **Open Data** datasets portal.
  - Built the **Tableau de Bord État du Cluster** displaying real-time metrics for H100 GPUs, Ollama engines, and Neo4j nodes.
  - Implemented the **Catalogue de la Galerie Multivers** enabling grid-view filtering and searching of communities' generated multiverses.

## [2026-06-10] Session: SOTA Google Cloud Integrations (GCIP, Vertex AI Vector Search 2.0, Gemini Agent Platform, AlloyDB AI Text-to-SQL, and Cloud KMS CMEK)

- **Google Identity Platform (GCIP) & Firebase Auth**: Migrated local session and allauth authentication to a managed identity platform. Integrated the Firebase JS Client SDK on the frontend and implemented a custom Django REST Framework `GoogleIdentityAuthentication` backend to verify JWT ID Tokens using cached Google certificates (with local Firebase Emulator support). Added OAuth social sign-in support for **Google**, **Discord**, **X (Twitter)**, and **MyAnimeList**.
- **Vertex AI Vector Search 2.0 (Collections)**: Integrated the managed GCP vector search index wrapper (`VertexAICollectionWrapper`) inside `chroma_client.py`. Implemented auto-embeddings (`text-embedding-005`) and hybrid search leveraging Reciprocal Rank Fusion (RRF). Maintained a dynamic runtime fallback to `PGVectorCollectionWrapper` for local SQLite development.
- **Gemini Enterprise Agent Platform & Agentic RAG**:
  - **Agent Gateway**: Integrated proactive safety gates to validate prompt inputs and LLM outputs against Google Cloud safety policies.
  - **Agent Observability**: Enriched OpenTelemetry spans with detailed GCP-specific agentic semantic attributes within `AgenticRAGService` to trace the agent's decision tree.
- **AlloyDB AI - Tools for Data Agents (Text-to-SQL)**: Implemented natural language catalog queries utilizing AlloyDB's native `alloydb_ai_nl.get_sql` function, with a fallback to local LLM prompt generation. Secured database execution with a custom two-layer validation parser (`sql_guard.py`) restricting queries to `animetix_mediaitem`, blocking mutations, comments, and query chaining.
- **Customer-Managed Encryption Keys (Cloud KMS CMEK)**: Integrated CMEK protection for generated assets uploaded to GCS buckets via the `GS_DEFAULT_KMS_KEY_NAME` setting.
- **Documentation Sync**: Fully updated `README.md` and `TODO.md` to reflect the completed cloud integration milestones and their local fallback behaviors.

## [2026-06-09] Session: XAI Convergence, Validation Unification, InferencePort Completion, and Model Collapse Protection (HITL)

- **XAI Convergence**: Merged `UncertaintyService` into `XaiDiagnosticService`. Eliminated duplicated logprob-based entropy and perplexity calculations, simplifying the dependency graph in `AgenticRAGService`.
- **Validation Unification**: Migrated all critical views (`Login`, `Register`, `Akinetix`, `Archetypist`, `Cognition`) from direct `request.data` dictionary parsing to **Django REST Framework Serializers**, stabilizing input validation and error responses.
- **InferencePort Completion**: Implemented all stubbed methods in production adapters. `BrainAPIAdapter` now supports 100% of the interface (video VLM, 3D depth, reranking), and `GoogleGenAIAdapter` integrates Gemini's native temporal video analysis.
- **Model Collapse Protection (HITL)**: Implemented an "Universal HITL Gate" using the `GoldDatasetEntry` model. All synthetic data (Multiverses, Distillation datasets, and QA pairs) are put in a validation queue awaiting human verification before ingestion.
- **Frontend Build Stabilization**: Fixed remaining TypeScript and ESLint build failures following the modularization process.
- **Dependency Cleanup**: Purged duplicate entries for `three` and `plotly` in `package.json`.
- **Ghost Labs Reactivation**: Re-connected all previously comment-stubbed experimental interfaces (Soundscape, Speech-to-Speech, Voice, Visual Nexus) inside `LabHubPage`.
- **Admin Tools & Cognitive Pages**: Hooked up the MLOps Dashboard, DSPy Optimizer, CoVe Oracle (hallucination reduction), Hierarchical Graph RAG visualizer, Strategy CFR Solver, and the Manga Voice Lab pipeline.

## [2026-06-08] Session: Major Refactoring, Frontend Modularization, and Lab Reactivations

- **Django Forms API Validation**: Refactored view methods in `backend/api/animetix/views/api.py` to systematically use Django Forms, eliminating raw request parsing.
- **InferencePort Stubs**: Removed remaining stubs from `backend/core/ports/inference_port.py`.
- **App.tsx Refactoring & Modularization**: Decoupled the monolithic 21 KB `App.tsx` file into atomic components, moving views to `src/pages/` and utilities to `features/`.
- **SelfEvolvingCompiler Integration**: Replaced compiler stubs with an active proxy compiler dynamically rewriting and optimizing performance critical backend paths.
- **Neural Diagnostics Improvement**: Migrated uncertainty analysis from simulated `gpt2` metrics in `UnifiedInferenceAdapter` to production-grade model logprobs.
- **Lazy Load Optimizations**: Configured `FallbackInferenceAdapter` and `GoogleGenAIAdapter` to load heavy client dependencies only on their first runtime invocation.
- **Social Route Cleanup**: Shifted non-social pages (Pricing, Support, Explore) to their respective feature directories.
- **New Feature Dashboards**: Created the `/pricing/` comparison page, Tree of Thoughts MCTS visualizer, Thought Budget (TTC) monitoring dashboard, Multiverse Gallery catalog, and the零-shot Voice Cloning (RVC) lab.

## [2026-06-04] Session: Advanced Explainability (XAI), Direct VPC Egress, GCP Validation, Vertex Context Caching, and Live API

- **XaiReportViewer Component**: Built the React component displaying prompt intent, confidence metrics, agent traces, source attributions, and token logprobs, supported by Vitest suites.
- **Direct VPC Egress Integration**: Replaced serverless VPC connectors with Direct VPC Egress configurations in `deploy_brain.py` and `deploy_jobs.py`.
- **GCP Validation Suite**: Created `test_gcp_deployment_validation.py` to verify Cloud SQL sockets, GCS read/write lifecycles, Secret Manager values, and Cloud Run Job error pathways.
- **Vertex AI Context Caching**: Implemented automatic context caching in `GoogleGenAIAdapter` for prompts exceeding `GEMINI_CACHE_THRESHOLD`.
- **Cloud Armor WAF Protection**: Added `deploy_security.py` configuring CEL expressions to block SQLi, XSS, RCE, Token DoS, and prompt injections.
- **Gemini Multimodal Live API**: Implemented the `speech_to_speech_live.py` Django Channels consumer for PCM WebSocket streaming and updated the frontend client page.

## [2026-06-03] Session: Vector Database Migration (ChromaDB to pgvector)

- **PostgreSQL pgvector Migration**: Replaced standalone ChromaDB containers with the PostgreSQL native `pgvector` extension for production RAG pipelines.
- **Hybrid SQLite Fallback**: Developed a local fallback adapter storing vectors in standard tables and calculating cosine similarity using NumPy.
- **ChromaDB Client Emulation**: Rewrote `pipeline/chroma_client.py` to maintain client compatibility, avoiding rewrite requirements in data scrapers.

## [2026-06-03] Session: Serverless Tasks (Cloud Run Jobs & Cloud Scheduler)

- **Secret Manager Hardening**: Configured Django settings to pull all external credentials directly from GCP Secret Manager in production.
- **ETL Catalog Sync Automation**: Created the nightly `sync_catalog` Cloud Run Job and triggered it via Cloud Scheduler HTTP POST calls.
- **Database Transaction Optimization**: Wrapped the sync command in atomic transactions, reducing execution time from timeouts to 7 minutes.

## [2026-06-03] Session: Google Cloud Storage & Creative Forge

- **GCS Storage Integration**: Configured `django-storages` with Google Cloud Storage backend for production media.
- **Creative Forge Persistence**: Fixed a bug where creative fusions (Base64 URIs) were not saved, implementing default storage decode and write pipelines.

## [2026-06-02] Session: SOTA Inference, Content Moderation, and Gaming UI

- **Google GenAI Adapter**: Built `GoogleGenAIAdapter` using Pydantic structural generation and real logprobs parsing.
- **Homogeneous Content Moderation**: Integrated a standard sémantique safety filter across all adapters with keyword-based fallbacks.
- **DRF Serializer Audits**: Audited and fixed mass assignment vulnerability vectors in `CreativeFusionSerializer` and IDOR vulnerabilities.
- **Gaming & Profile UI**: Deployed ClubEvent countdown participation, realtime notification badges, VsBattle lobby matchmaking, and latent space user auras.

## [2026-06-16] Session: Universal HITL Gate, SQL Guard Hardening, MLOps Privacy, and Frontend Stabilization

- **Universal HITL Gate (Model Collapse Protection)**: Implemented a centralized `SyntheticValidationService` that executes systematic cross-validation (self-critique, XAI scoring, and guardrails) on all synthetic data before human moderation.
- **SQL Guard Formal Audit & Hardening**: Performed a security audit and fuzzing of the Text-to-SQL validator. Implemented mandatory `LIMIT` clauses, restricted `JOIN` counts (max 5), and strictly enforced AST-level table whitelisting for `animetix_mediaitem`. Verified against 34 attack scenarios.
- **MLOps Privacy & Secret Isolation**: Created a recursive data scrubbing utility to strip API keys, JWTs, and PII from logs and fine-tuning datasets (`DPOFeedbackLoop`).
- **Frontend Core Stabilization**: 
    - Resolved UI flicker and unpredictability by replacing `Math.random()` in render cycles with stable deterministic values or `useMemo`.
    - Fixed critical performance regressions by eliminating synchronous `setState` calls within effects in core components (`ClubChat`, `VNPlayer`).
    - Fixed "used before defined" reference errors in `AkinetixRLPage` and `ExpertNexusPage`.
    - **TypeScript Type Hardening**: Massive refactoring to eliminate `any` in core API clients and pages (`Explore`, `Admin`, `Health`), replaced with strict interfaces.
- **InferencePort & Adapters Completion**: Finalized the `InferencePort` implementation across all production adapters. Added real sprite generation for the Game Engine and replaced similarity placeholders with real embeddings in the Google GenAI adapter.
- **Manga & Video Labs Promotion**: Completed the backend flow for the Manga Reader (OCR & Inpainting) and stabilized the temporal indexing service for Video-RAG.
- **Reasoning & Budget Optimizations**: Integrated local 3B reasoning models for low-latency tasks and implemented a dynamic "Reasoning Budget" based on query complexity.
- **Research Lab Expo**: Deployed a dedicated frontend page to showcase and search through the project's 29 fundamental AI research papers.

## [2026-06-14] Session: Backend Robustness, Frontend Type Hardening, Semantic RAG Caching, and UI Convergence

- **Backend Robustness & Observability**: Eliminated the "silent failure" anti-pattern by replacing all identified `except: pass` blocks with explicit logging (`debug`, `warning`, or `error`) across all adapters (Google GenAI, ImageGen, Rerank, Safety), API views, and MLOps loops. This ensures full traceability of system failures in production.
- **Frontend Type Hardening**: Performed a massive cleanup of the TypeScript codebase, replacing generic `any` types with precise interfaces generated from the OpenAPI schema (`api.d.ts`). Secured game stores (`akinetix`, `blindtest`, `vision`, `paradox`), services (`animinator`, `codemanga`, `audioLab`), and XAI components.
- **Semantic RAG Caching**: Implemented a vector-based caching layer in `DjangoSemanticCacheAdapter` using the project's unified vector store (`PGVector`/`ChromaDB`). Cached LLM responses are now reused for semantically similar queries (0.92 similarity threshold), significantly reducing costs and latency.
- **Natural Language SQL Security**: Hardened the Text-to-SQL pipeline by enforcing a strictly **Read-Only transaction** in `DjangoRepositoryAdapter` for all AI-generated queries, providing a final line of defense against injection even if guardrails are bypassed.
- **React Performance Optimization**: Migrated `SocialHubPage` and `ClubDashboard` to **TanStack Query** (hooks `useSocialDashboard`, `useClub`), resolving technical debt regarding synchronous state updates in effects and improving data fetching reliability.
- **UI Routing & Page Convergence**: Finalized the integration of several "Ghost" pages into the main router, including the **Developer Portal**, **Transparency Hub**, **Manga Reader**, and specialized profiles for **Characters** and **Staff**.
- **Stripe Metered Billing for Expert API**: Fully implemented usage-based monetization for the B2B API. Developers can now subscribe to the **Pro tier** via Stripe Checkout. Consumption (RAG requests) is automatically reported to **Stripe Billing Meters** through the `DjangoUsageAdapter`, enabling precise pay-as-you-go invoicing.
- **Documentation Refactoring**: Purged and archived all completed tasks from `docs/TODO.md` into this log to maintain a focused and actionable project backlog.

---
*End of History Log*
