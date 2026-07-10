# Animetix - History of Refactorings & Achievements

This document archives the major milestones of the project's technical evolution.

## [2026-07-10] Session: Service locator eradicated from the view layer — constructor injection everywhere

Closure of the 🟡 debt item "service locator au lieu d'injection" (2026-07-05 audit). The view layer resolved services through 49 `get_container()` call sites (~158 `container.x.y()` expressions across 20 files); all converted to `dependency_injector` constructor injection (`@inject __init__` with `Provide[Container.<sub>.<service>]` defaults, the house pattern already used by MediaSearchView/Suwayomi/ToT), including the 5 native-async SSE views in [streams.py](../backend/api/animetix/api/streams.py) and the function view `run_vs_battle` (`@inject` on the function). [apps.py](../backend/api/animetix/apps.py) wiring extended with the 5 modules that were missing (cognition, developer, monitoring, streams, games.vs_battle).

- **`ProviderDelegate` monkey-patch deleted** ([containers/\_\_init\_\_.py](../backend/api/animetix/containers/__init__.py)): its 8 flat root-container shortcuts had 10 real consumers (scripts benchmark/curation/verify, `run_red_teaming`, codemanga consumer, 3 evaluation pipelines, `regression_benchmark`) — all migrated to the explicit sub-container paths (`container.core.x()`, `container.agentic.y()`, …).
- **Latent prod breakage found and fixed**: [creative_tasks.py](../backend/api/animetix/creative_tasks.py) called five flat services (`studio_transform_service`, `manga_flow_service`, `soundscape_service`, `spatial_computing_service`, `fusion_service`) that never existed on the root container nor among the delegate shortcuts — every one of those task paths raised AttributeError in production and only passed in tests because the whole container was mocked. Now routed through `container.core.*`. Similarly, `pre_flight_check`'s `if not container.neo4j_manager:` guard could never trigger (a delegate instance is always truthy) — it now checks the resolved port.
- **Dead code removed**: `views/common.py` shrunk to its logger — the `LazyServiceProxy` shim and its 9 service proxies resolved flat attribute names that don't exist on the root container (broken since the sub-container split) and had zero consumers.
- **Canonical test pattern switched**: mocking `module.get_container` replaced by real-container provider overrides (`container.core.x.override(mock)` + provider-level `reset_override()` in `finally`) or, for directly-instantiated views, passing mocks as constructor kwargs — ~20 test files migrated. The generic `mock_container` fixture no longer pre-seeds misleading flat attributes.
- Accepted residual: the 4 WebSocket consumers (undercover, codemanga, duel, speech_to_speech_live) keep a `get_container()` call each — long-lived stateful objects where per-connection constructor injection buys little; their accesses now use the explicit sub-container paths.

## [2026-07-10] Session: `Profile.rank` defined — authenticated `/config/` no longer 500s

Closure of the 🟡 item "`Profile.rank` n'existe pas". Empirical reproduction confirmed both halves of the finding: `ProfileSerializer.rank` (a `ReadOnlyField` with no matching model attribute) silently serialized to nothing — which is why the leaderboard and `/auth/me` never crashed and the frontend showed its `'Explorateur'` fallback — while the authenticated `GET /api/v1/config/` genuinely crashed with `AttributeError: 'Profile' object has no attribute 'rank'` (500 on every authenticated call, critical now that the maintenance-mode frontend polls this endpoint). Root cause: the ranked ladder existed only on the domain entity (`UserProfile.rank_label` — zero consumers, dead code) and was never bridged to the Django model. Fix at the source: the ladder extracted into `rank_label_for(ranked_points)` in [entities/user.py](../backend/core/domain/entities/user.py) (single source of truth, the entity property delegates), and `Profile.rank` added as a property using it. TDD: 10 regression locks written first and watched fail with the AttributeError ([test_profile_rank.py](../tests/api/test_profile_rank.py) — ladder thresholds, serializer exposure, endpoint 200), the artificial `patch(..., create=True)` in the config coverage test removed in favor of asserting the real value ("Bronze 🥉"). 152 tests green across the impacted suites.

## [2026-07-10] Session: API god-files decomposed — `api/labs.py` and `api/core.py` split into domain packages

Closure of the 🟡 debt item "fichiers-dieux dans la couche API" (2026-07-05 audit). Both worst runtime offenders are now domain packages whose `__init__` star-re-exports keep the public surface intact (the `api_views.py` aggregator and every URL keep working unchanged):

- **`api/labs.py` (1262 lines, 25 views) → `api/labs/`**: `dashboards` (daily challenge, latent space), `singularity` (evolving-AI actions, LNN, ToT, command center, neural diagnostics), `manga` (clean/translate/voice), `video` (FateZero, Video-RAG), `audio` (seiyuu, voice ingest/clone, soundscape, S2S), `spatial` (image/video→3D).
- **`api/core.py` (1234 lines, 25 views) → `api/core/`**: `accounts` (login/logout/register/me + game session), `media` (search, detail, signed image proxy), `config` (app config incl. maintenance mode, transparency report), `manga` (chapters, favorites, tracker sync), `suwayomi` (proxy + sources/search/import/extensions).
- **DI wiring** ([apps.py](../backend/api/animetix/apps.py)) now lists the 11 domain submodules; ~15 test files' `@patch` targets repointed to the submodule that defines each view (shared helpers like `_container_patch`/`GET_CONTAINER` parametrized per domain).
- **Latent bug fixed by the move**: `DailyChallengeDataView`'s authenticated branch did `from ...models import DailyResult` — from the old monolith (package `animetix.api`) that 3-dot relative import climbed beyond the top-level package and raised ImportError (→ 500) on every authenticated daily-challenge request. Inside the new `animetix.api.labs` package it resolves correctly to `animetix.models`; a regression test creating a real `DailyResult` locks the path.
- Also fixed 4 pre-existing test failures along the way (3 diagnostics tests + the anonymous config test lacked `django_db` while the views traverse middleware/`SiteConfiguration` DB reads). The impacted suites went from 166 passed / 3 failed to **170 passed / 0 failed**; ruff clean. The API layer no longer has any file > 500 lines except the flat URL table (`urls/api.py`); the remaining big files are offline pipeline/mlops scripts, outside this item's runtime scope. Side-finding tracked in TODO: `Profile.rank` is consumed by ConfigView/ProfileSerializer but not defined on the model.

## [2026-07-10] Session: List-endpoint N+1s fixed (TDD) + broken public-profile endpoint repaired

Closure of the 🟠 debt item "N+1 quasi garantis sur les endpoints listes" (2026-07-05 audit). The inventory corrected the audit: most list endpoints were **already optimized** (club list/feed/friends/leaderboard/user-search in [social.py](../backend/api/animetix/api/social.py), manga favorites via a correlated-subquery annotation in core.py, explore, world_boss) — notably `members.count()` on a prefetched M2M uses the prefetch cache on this Django version, so the club list was sound. Three real N+1s remained, each fixed test-first with a scaling assertion (query count captured on 2 rows, dataset grown, count must be identical — [tests/api/test_query_counts.py](../tests/api/test_query_counts.py), 5 locks):

- **`ProfileDetailView` top/recent fusions** (19 → 34 queries observed): `CreativeFusionSerializer` reads `creator.username` + `likes` per fusion → `select_related("creator")` + `prefetch_related("likes")` (the serializer was already prefetch-aware).
- **VS Battle arena list** (7 → 31 queries): `VsBattleSerializer` reads `creator.username`, the `likes` M2M field, `likes.count` and `is_liked` per battle → `select_related("creator")` + `prefetch_related("likes")` on the view, and `get_is_liked` made prefetch-aware (`user in obj.likes.all()`), matching the `CreativeFusionSerializer` house pattern.
- **AI feedback history** ([mlops.py](../backend/api/animetix/api/mlops.py), 3 → 11 queries, up to 100 rows): `username` per row → `select_related("user")`.

**Bonus real bug surfaced by the RED phase**: `ProfileDetailView` crashed with a 500 on **every** request — `user.user_achievements` is not a valid reverse accessor (`UserAchievement` has no `related_name`; it's `userachievement_set`). A coverage test even asserted the 500 as "known bug". Fixed the accessor and rewrote the test to lock the correct behavior (200 + achievements/fusions payload). 113 tests green across the impacted suites (social, mlops, vs_battle, query-count locks).

## [2026-07-09] Session: Post-leak hygiene closed — secrets mounted on `animetix-web` + pre-exclusion registry purge

Closure of the 🔴 item "secrets manquants sur `animetix-web` + hygiène post-fuite" (follow-up of the 2026-07-05 `.env` remediation), except the two dead-key revocations which stay tracked in TODO.

- **Secrets on the web service**: verified already mounted (fixed by a later deploy since the 07-05 finding) — the live revision `animetix-web-00043-t7v` reads `HF_SPACES`, `HUGGINGFACE_API_KEY` (→ `HF_TOKEN`), `NEO4J_URI`, `NEO4J_USER` and `NEO4J_PASSWORD` from Secret Manager `secretKeyRef`s; no literal env values remain besides non-sensitive config.
- **Artifact Registry purge**: deleted the **33 `animetix-repo/web` images predating the 2026-07-05 `.env` exclusion** (26 untagged local `gcloud builds submit` builds — the actual at-risk set, one of which had even served revision `00036` — plus 7 clean-but-obsolete CI builds tagged by commit SHA). Only the 5 post-exclusion July images remain, including the serving `latest`. Prod verified healthy after the purge. Side effect (accepted): Cloud Run revisions older than 2026-07-04 can no longer cold-start — they were inert at 0 % traffic.

## [2026-07-09] Session: Playwright e2e suite consolidated and actually running

Closure of the 🟡 debt item "les e2e Playwright ne tournent nulle part" (2026-07-05 audit): `npm run test:e2e` filtered on `--grep @e2e` but no spec carried that tag (0 tests selected), and CI only ran `a11y.spec.ts`. The suite was consolidated onto the Playwright TS specs, dropping the redundant Python e2e harness (`7dde6d05`); stale routes and bad mocks in the a11y/vrt specs were fixed (`9724600d`). Actually running the flows surfaced real bugs: an `apiClient` crash on null Firebase auth hit by the akinetix e2e (`1c93b6f3`) and 3 WCAG AA contrast violations on LabHubPage (`92fb6a81`), both fixed.

## [2026-07-08] Session: Dev dependencies out of the prod lock, migrations squashed, HF deploy workflow repaired

- **Dev dependencies embedded in the prod image** (🟠 closed): [requirements.in](../requirements.in) mixed pytest/pytest-playwright/playwright/watchdog/coloredlogs into the prod lock (playwright pulls a whole browser stack). 9 dev packages moved out to `requirements-dev.{in,txt}` (layered via `-c requirements.txt`); the 3 Docker images slim down with no behavior change; the 3 pytest CI jobs install the dev lock. Commits `22a12a30` / `6d045714` / `8294c9c8`.
- **Migrations squash landed**: `0001_squashed_0049_…` created, with the redundant `RenameIndex` operations collapsed so fresh DBs build (`68fec496`). Deleting the 49 original migration files once the squash is applied everywhere stays tracked in TODO.
- **HF deploy workflow repaired** (🟠 closed): [deploy_to_hf.yml](../.github/workflows/deploy_to_hf.yml) now calls the real script path `scripts/deploy/huggingface/hf_deploy.py` (it pointed at a non-existent `scripts/deploy/hf_deploy.py`, failing every trigger); `hf_deploy.py` also fixed to resolve `project_root` at the right depth so it finds `deploy/Dockerfile` (`ed30faca`) and to skip `create_repo` when the Space already exists, avoiding a 402 (`ecbb9e3a`).

## [2026-07-07] Session: Debt-audit batch closure — frontend refactors, test hygiene, CI parity, infra-as-data, scripts & repo cleanup

Batch closure of 13 items from the 2026-07-05 debt audit, each verified.

### Frontend
- **God components (14 pages of 400-560 lines)**: refactored the three worst pages — `ForgePage.tsx`, `SynapticLabPage.tsx`, `UndercoverRoom.tsx`. State and network/socket logic extracted into reusable hooks (`useForge.ts`, `useSynapticLab.ts`, `useUndercoverRoom.ts`); complex UIs split into modular presentational sub-components under `components/forge/`, `components/labs/` and `components/games/`. All unit tests and TypeScript typing green.
- **Two divergent WebSocket implementations (+2 bugs)**: fixed the assignment-order bug in `useSocket.ts` (the « Connexion rétablie ! » toast now fires on successful reconnect) and aligned `notificationStore.ts` reconnection on `useSocket`: 5-attempt cap, exponential backoff, no reconnect on voluntary close (code `1000` logout), info toasts, and timeout cleanup on `disconnect()`.

### Tests
- **Coverage asymmetry + blind spots**: 25 targeted unit tests on the blind spots (`pipeline/movies`, `pipeline/games`, `pipeline/actors`, `adapters/infrastructure`) → 78.83 % targeted coverage (above the 75 % gate); Ollama configured and the integration tests made blocking in CI.
- **77 raw `sys.modules` mutations across 16 files**: inter-test cleanup secured via a full snapshot/restore of `sys.modules` in `conftest.py`; module-level `os.environ` assignments in the `brain_api` test files replaced with `setdefault` (no more temporal coupling); real 50 ms `asyncio.sleep` replaced with `asyncio.sleep(0)` in `test_cove_parallel.py`; shared global mock objects in `test_s2s_inference.py` made per-test.

### CI / DX
- **pre-commit ↔ CI drift + fake frontend security audit**: `.pre-commit-config.yaml` now runs mypy (`--no-site-packages`, matching CI) and pytest with the 75 % coverage bar, through cross-platform `run_in_venv.py`/`run_cmd.py` runners; unified frontend hooks (`lint-staged` on commit, `vitest` on push); mypy brought to 0 errors on 515 files; the `frontend-security` job now runs a real `npm audit --audit-level=high`, and 12 vulnerabilities were fixed via `npm audit fix`.

### Infra
- **`animetix.xyz` missing from `ALLOWED_HOSTS`/CORS defaults**: the custom domain and its subdomains (`.animetix.xyz`) added to the production defaults of `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`; `CORS_ALLOWED_ORIGINS` made env-driven with these domains as defaults.
- **Duplicated deploy logic, no IaC**: single declarative source [deployments.yaml](../deploy/deployments.yaml) centralizing all deployment parameters (GCP services, Cloud Run GPU, the 8 scheduled jobs, Load Balancer/CDN, Cloud Armor, the Cloudflare Worker and the HF Space); the 3 build files merged into a root [cloudbuild.yaml](../cloudbuild.yaml) supporting selective or global builds via `_BUILD_TARGET`; the Python deploy scripts (`deploy_brain.py`, `deploy_jobs.py`, `deploy_budget.py`, `deploy_cdn.py`, `deploy_security.py`) now read from `deployments.yaml` instead of hardcoded params; `.gcloudignore` aligned on `.dockerignore` via `#!include:.dockerignore` (one canonical build context).
- **Scripts sprawl (~55 scripts)**: deleted `scripts/test/` (7 non-pytest exploratory scripts); the DB utility scripts (Qdrant vector counts, migration checks, SQLite catalog checks, Neo4j reconciliation) promoted to Django management commands (`check_db_status`, `reconcile_db`, `generate_offline_db`); `reconcile_db` bulk-loads (`values_list` + `item_id__in`, no N+1) and validates Neo4j connectivity once; non-ASCII console output stripped (Windows `UnicodeEncodeError`).

### Git / docs / hygiene
- **`dev/null/` versioned**: removed the literal path and the 4 Git-LFS hooks accidentally committed via a Windows redirect (`3df26086`).
- **~30 MB of raw PNG blobs (64 files)**: `*.png` now auto-tracked by Git LFS in [.gitattributes](../.gitattributes); the 64 existing PNGs converted in place to LFS pointers via `git add --renormalize .` (history untouched).
- **Two contradictory TODOs + stale docs**: deleted the duplicate `docs/TODO.md` (the root `TODO.md` is the single source of truth); fixed the `setup_e2e.py` path in the README; replaced the Celery reference in `docs/ARCHITECTURE.md` with the active Cloud Run Jobs; updated `docs/FULL_GUIDE.md` and `docs/ROADMAP.md` for the July 2026 features (drift detection, XAI transparency diagnostics, billing-budget safety).
- **Working-tree residues**: `/src/` added to `.gitignore`; verified `error_latent.html`/`brainstorming_status.txt` were already ignored.
- **Misc cosmetic/hygiene**: compiled `.mo` translation binaries de-indexed and gitignored; the NOTICE file rebranded from « Double Scenario Project » to Animetix; Windows-only `sync-api.bat` replaced by the cross-platform `scripts/sync_api.py`; redundant `WSGI_APPLICATION` setting removed (server is ASGI-only); `frontend/.env.production` de-indexed and gitignored; `downloadDataset` migrated from raw XHR onto `apiClient` (which gained `responseType: 'blob'` support); `@extend_schema` bound to the right serializers on the XAI audit endpoints (fixing schema-generation TypeScript errors).

## [2026-07-07] Session: Removed all Stripe payment features

Purchasing Berrix (or a Pro subscription) via Stripe is no longer offered, so the payment code was removed end to end: the `CreateBxCheckoutView` / `CreateProSubscriptionCheckoutView` / `StripeWebhookView` endpoints, the `StripeBillingService`, the metered usage reporting in `django_usage_adapter`, the purchasable `PACKS`, the six `STRIPE_*` settings, the `stripe` dependency, and the three `Profile` Stripe columns (dropped via migration — to be applied to the Neon prod DB manually). The front had no live purchase path: `NexusGatewayModal` (the only priced component) was dead (test-only) and was deleted; PowerStation/Pricing already run on earned Berrix (rewarded ads + mining) and sponsor/donation. The `tier` (free/pro) concept stays: `DeveloperSubscriptionMockView` now simply sets `tier="pro"` for free. The Stripe-key log-scrubbing regex was intentionally kept.

## [2026-07-06] Session: i18n externalization completed + `dependency_injector` wiring bug fixed at the root

- **i18n (~500 hardcoded FR strings)** (🟡 closed): the ~150 remaining files (labs, social, admin, media, search, dev) externalized with `t('key', 'FR default')`; translation fragments generated and merged via `merge_translation_fragments.py`; pre-existing key inconsistencies (`games.akinetix` vs `labs.akinetix`, `labs.ai_debate_arena.protocol_text`) resolved and verified by `compare_translations.py` (100 % key parity). 611 vitest unit tests + type checking green.
- **Games conftest landmine (`dependency_injector` bug)** (🟡 closed): fixed at the root in `dependency_injector.wiring` — `_is_marker` and the `Provide`/`Provider`/`Closing` type checks switched to duck-typing and class-name comparison, resolving the multiple-import collision under test coverage. The skipped test in `test_archetypist_coverage.py` restored and fixed; full suite green.

## [2026-07-05] Session: Prod WebSockets repaired (missing `channels_redis`) + CSS design tokens fixed

- **Prod — WS 500 on every handshake** (🔴 closed): root cause confirmed via Cloud Run logs (live repro, trace `b03e26f1…`) — `ModuleNotFoundError: No module named 'channels_redis'`. The Redis channel-layer backend was selected whenever `REDIS_URL` exists (prod), but the package was never in requirements; locally there is no `REDIS_URL` → InMemory fallback → invisible. Fix: `channels-redis==4.3.0` added (lock regenerated without drift); [channels_config.py](../backend/api/animetix_project/channels_config.py) extracted with a **fail-fast** `ImproperlyConfigured` if `REDIS_URL` is missing in prod (per-process InMemory breaks fan-out with 2 workers) and the `ssl_cert_reqs=None` mirror for `rediss://`; regression tests in [test_channel_layers.py](../tests/backend/test_channel_layers.py) (including the `import_string` test that would have caught the bug). Deployed and **verified live**: the handshake returns `101 Switching Protocols` (re-checked 2026-07-09). Gotcha: WS routes need a trailing slash, else channels 500s with "No route found".
- **Frontend — broken CSS design tokens (comma-separated RGB triplets)** (🟠 closed): the 23 tokens of [index.css](../frontend/src/index.css) converted to space-separated triplets (`37 99 235`) so Tailwind `<alpha-value>` consumption works. Verified in-browser: `bg-brand-primary` → `rgb(37, 99, 235)`, `bg-anime-accent/20` → `rgba(253, 185, 19, 0.2)`; the only other consumers (`rgb(var(--color-bg))` on body) accept both formats.

## [2026-07-05] Session: Secured the anonymous AI/GPU endpoints + rationalized throttling

Closure of the 🟠 debt item on `AllowAny` AI endpoints. A precise inventory corrected the audit: 3 of the 4 named labs views (`MangaLabDataView`, `AudioLabDataView`, `SeiyuuDiscoveryView`) are CPU/DB and stayed public; the real anonymous GPU holes were the Speech-to-Speech Live WebSocket (a full Gemini Live session — now auth-gated with a flat 12-Bx per-session charge, a 10-minute cap, and the Firebase token passed via the `Sec-WebSocket-Protocol` subprotocol rather than the URL query string so it never lands in access logs), `GraphWorldMapView` (per-hit LLM community summaries, now a 24 h shared cache with an anti-stampede lock — the map is identical for everyone, so it stays public and bills no one), `VideoRAGSearchView` (now IsAuthenticated + 6-Bx via the canonical deduct_berrix pattern), and the guardrail's `_llm_moderate` fallback on `MediaSearchView` (now authenticated-only via an `allow_llm` flag; anonymous search keeps the heuristic layer). Throttling went from "daily cap or nothing" to two-speed: per-minute burst throttles (anon 30/min, user 120/min) added globally, the long-dead `gpu` scope wired to a real 30/hour rate, and a `CpuGameThrottle` (60/min) applied to every AllowAny CPU-game view (emoji/undercover/covertest + blindtest/classic/akinetix/quiz_who/animinator/archetypist/vision/world_boss), replacing the `throttle_classes = []` overrides that had removed all protection. Two bugs caught in review: `CpuGameThrottle` initially inherited `ScopedRateThrottle` (whose `allow_request` reset the scope to None → a silent no-op) and was reparented to `SimpleRateThrottle`; and the WS token was first put in the URL (flagged HIGH by commit review) before moving to the subprotocol. Frontend login-gates added to VideoLab/VisualNexus/S2S pages.

## [2026-07-05] Session: Unified the import namespace on the bare root

Closure of the 🟠 debt item "triple espace de noms d'import" (2026-07-05 audit). The same packages were importable as `animetix` / `backend.api.animetix` / `backend.animetix` (and `core` / `backend.core`, etc., plus a legacy `src.pipeline` alias in tests), because three sys.path roots (`.`, `backend`, `backend/api`) coexist — Django genuinely loaded both identities in prod (settings mixed them inside MIDDLEWARE/AUTHENTICATION_BACKENDS) and `middleware.py` carried a runtime contextvars-sync hack between the module copies. Unified everything on the bare root (INSTALLED_APPS' identity, ~95% of the code already): ~31 files rewritten (imports, `@patch` targets, `sys.modules` keys, settings dotted strings), both compat hacks deleted (middleware sync, `SrcPipelineMapper`/`AliasLoader` in tests/conftest.py), standalone pipeline script headers cleaned of dead `src/` path entries, and a 3-layer tripwire installed: `backend/__init__.py` now raises ImportError on any `backend.*` import (implicit-namespace-package-proof), ruff TID251 bans `backend`/`src` imports, and `tests/test_import_hygiene.py` scans for textual regressions.

## [2026-07-05] Session: Removed the dead LLM text-to-SQL surface

Closure of the 🔴 debt item "SQL généré par LLM exécuté en base" (2026-07-05 audit). Exploration showed the whole chain was dead code: zero production callers (only the port, adapters and tests referenced it), `ALLOYDB_NL_QUERY_ACTIVE=False` by default, and prod runs on Neon where the native `alloydb_ai_nl.get_sql` path cannot execute — while the LLM fallback would have run with `neondb_owner` privileges gated only by a `READ ONLY` transaction. Decision (user-validated): delete rather than harden — removed `query_data_natural_language` from `RepositoryPort` and its three adapters, `is_alloydb_nl_query_supported()`, `sql_guard.py` (sqlglot AST validator), its fuzzing tests and `scripts/verify/audit_sql_guard.py`, the `ALLOYDB_NL_*` settings, and the `sqlglot` dependency. Everything is recoverable from git if the feature ever ships for real (spec: `docs/plans/2026-07-05-remove-text-to-sql-design.md`).

## [2026-07-05] Session: Secret hygiene — `.env` can no longer reach the prod image or the HF Space

Closure of the 🔴 debt item "Prod — secrets réels embarqués dans l'image Docker" (2026-07-05 debt audit). Both leak channels are shut and verified:

- **Cloud Build / Docker channel**: `.env` added to [.gcloudignore](../.gcloudignore) (verified with `gcloud meta list-files-for-upload` — only the placeholder `.env.example` remains in the upload context) and a **root** [.dockerignore](../.dockerignore) created (`.env` + `**/.env`, mirroring `.gcloudignore` so local, CI and Cloud Build contexts match). The old `deploy/.dockerignore` was dead config — Docker only reads the `.dockerignore` at the build-context root (the build is `docker build -f deploy/Dockerfile .`) — and has been deleted.
- **HF Space channel**: [hf_deploy.py](../scripts/deploy/huggingface/hf_deploy.py) now enforces an unconditional `always_ignore = [".env", "**/.env", …]` inside `deploy_space()`, independent of the caller-supplied ignore list.
- **Actual exposure was narrower than feared**: the current prod image (`web:5f8a0886…`) was built by CI from a git checkout, which has no `.env` (untracked) → clean; the HF Space never received a `.env` (verified via the Hub API — the callers' ignore lists had worked). The residual risk was old Artifact-Registry tags built locally via `gcloud builds submit` before the exclusion, plus two dead-but-real keys in the local `.env` (`TRIPO_API_KEY`, `MAPBOX_TOKEN` — consumed nowhere in the code) → follow-ups tracked in TODO (purge old tags, revoke dead keys). Stripe/Cohere/Tavily/OpenAI values in `.env` were already empty; the 8 Cloud Run jobs already mount all their secrets via Secret Manager and `ci.yml` deploys with `--update-env-vars` (merge), so nothing depended on the baked file anymore — except the web service's missing `NEO4J_*`/`HUGGINGFACE_API_KEY`, split out as its own open TODO item.

## [2026-06-22 → 2026-07-08] Architecture-review follow-ups: model registry, adapter dedup, config validation, native async streaming

Progressive closure of 2026-06-22 AI-architecture-review items shipped across late June / early July (the residual sub-items stay tracked in TODO).

- **Hardcoded model names — Phases 1 & 2a**: security registry [model_registry.py](../backend/core/utils/model_registry.py) (model_id → pinned SHA + trust policy); Gemini unified on 3 canonical roles via [gemini_models.py](../backend/core/utils/gemini_models.py) (`gemini-3.5-flash` / `live-2.5-native-audio` / `embedding-2`) with an anti-literal guard; embedding revisions resolved from the central `EMBEDDING_VERSIONS` registry (manifest approach abandoned). Phase 2b (registry of local logical IDs + `pipeline/models_registry.py` merge) stays open.
- **Inference-adapter duplication**: API-adapter reachability `health_check` factored into [ReachabilityHealthCheckMixin](../backend/adapters/inference/reachability_health_mixin.py); local-model readiness `health_check` into [LazyLocalModelAdapter](../backend/adapters/inference/lazy_local_model_adapter.py) (all local-model adapters migrated); the multi-submodel `_load_model()` motif into [LazyLoadMixin](../backend/adapters/inference/lazy_load_mixin.py) (`ImageGenMixin`/`AudioMixin`). Residual (`RerankMixin`, `LocalTextAdapter.get_text_embedding`, `LocalGuardrailAdapter`) accepted as out of scope, tracked in TODO.
- **Inference env-var validation** (closed): `BrainAPIAdapter` fails early (`ConfigurationError` if `BRAIN_API_URL` is missing, unified message, malformed-URL check); coherence guards for `unified` (`LLM_API_BASE` malformed) and `google_genai` (blank `GEMINI_API_KEY`) in their `__init__`; aggregated startup validation via `validate_inference_config()` ([inference_config.py](../backend/core/utils/inference_config.py)), wired into the container ([inference.py](../backend/api/animetix/containers/inference.py)).
- **Sync adapters → native async streaming** (closed): native `astream_generate` (non-blocking I/O) on `UnifiedInferenceAdapter` (httpx.AsyncClient/SSE), `GoogleGenAIAdapter` (`client.aio`) and async orchestration in `FallbackInferenceAdapter`; local models stay on `InferencePort`'s default thread bridge. Multiple streams can now be parallelized via `asyncio.gather`. (Documented caveat: `UnifiedInferenceAdapter`'s `_last_completion` diagnostics cache is best-effort under concurrent streams on the Singleton.)
- **Async streaming exposed to the HTTP endpoints** (all shipped except the 8 one-shot processors, tracked in TODO): the **5 SSE views are now native async Django views** (Animinator, Emoji, Paradox, ToT, AgenticRAG) sharing the `api/sse.py` helper (`check_rate_limit` + `sse_stream_response`), freeing worker threads for the whole stream duration; ToT's `asolve_with_tree_of_thoughts_stream` parallelizes each level via `asyncio.gather` (first real gather win on remote engines); AgenticRAG got an end-to-end async pipeline (`StateProcessor.aprocess`, `RAGOrchestrator.arun_workflow`, `aplan_and_solve_stream`) with native-streaming `FallbackRagProcessor`/`SynthesizeProcessor` (`asynthesize_stream`); `Cache-Control: no-cache` harmonized across the 5 views; 4 dead non-routed sync stream views removed with their tests; and the latent `.text` bug (stream chunks are `InferenceResponse` objects) eradicated in every streaming consumer (`emoji_service`, `paradox_service`, `fallback_rag_processor`, `synthesize_processor`, `AniminatorStreamView`) with regression tests feeding `InferenceResponse` — the Oracle SSE endpoint works again.

## [2026-06-25] Session: Architecture & Financial Review — Backlog Closure

Closure of the high/medium items raised by the 2026-06-22 AI-architecture and financial review (each shipped on its own branch; TODO trimmed back to open work only).

### Resilience & security
- **Neo4j single-point-of-failure (silent degradation)**: user-preference context ([agentic_rag_service.py](../backend/core/domain/services/agentic_rag_service.py)) **and** CoVe fact-checking ([cove_oracle_service.py](../backend/core/domain/services/cove_oracle_service.py)) silently fell back to empty when the graph was unavailable — aggravated by CoVe's bias of marking a real-but-absent fact as "unverified". Added an explicit fallback (ChromaDB/web) plus a degraded-state signal.
- **Prompt-injection sanitisation (tag-breaking)**: the companion wrapped input in `<user_input>…</user_input>` but didn't catch payloads that close then re-open the tag (`</user_input>ignore previous<user_input>`) ([companion.py](../backend/api/animetix/api/companion.py)). Delimiters are now escaped/neutralised and validated beyond a pure regex.
- **`trust_remote_code=True` on HF models**: central allowlist ([model_registry.py](../backend/core/utils/model_registry.py)) maps model_id → pinned SHA + `trust_remote_code` policy; default `False`, only allowlisted models (jina, LightonOCR…) get it, pinned to SHA. All adapters (vlm/image_gen/…) + pipeline/scripts gate via `resolve_trust_remote_code()`; a test guard forbids raw literals.

### AI architecture
- **Cognitive boosters in the prod RAG path**: `advanced_rag_service` wired `quantum_cognitive_service` + `neuromorphic_lnn_service` into real reranking without proof of gain. Instrumented the path via `ragas_eval_service` (faithfulness/relevance) and ran ablations — kept what measurably helped, demoted the rest toward the Ghost Labs demos (reducing the maintenance + billed-GPU surface of a solo project).
- **`UnifiedInferenceAdapter` god object**: 8 mixins / ~476 l. with a fragile MRO ([unified_inference_adapter.py](../backend/adapters/inference/unified_inference_adapter.py)) refactored toward composition over multiple inheritance.
- **`FallbackInferenceAdapter` god object + central coupling**: 30+ methods across 7 mixins mixing orchestration + fallback + health-check + capability-detection + reporting ([fallback_adapter.py](../backend/adapters/inference/fallback_adapter.py)), with ~60 dependent services. Selection/health-check extracted from orchestration.
- **Companion long-term memory**: `memory_service` wired via DI into [companion.py](../backend/api/animetix/api/companion.py) — long-term memory retrieval + background `remember()` + persistence of evicted turns (`{memories}` slot in the personality prompts).
- **CoVe parallelised**: claim verification now runs via `asyncio.gather` in [cove_oracle_service.py](../backend/core/domain/services/cove_oracle_service.py).
- **Health-checks re-run on every orchestration → short-TTL cache**: the fallback re-probed every adapter on each call. Added a TTL-throttled health refresh ([fallback_adapter.py](../backend/adapters/inference/fallback_adapter.py)) — adapters are re-probed at most once per `FALLBACK_HEALTH_TTL_SECONDS` (default 30 s) window, shared by routing (`_online_adapters`) and the public `health_check` (`_cached_statuses`).
- **API-adapter reachability `health_check` factored into a mixin**: the per-adapter HTTP-ping / client-init reachability probe (Brain HTTP `/health`, Google client-init, Unified Ollama/OpenAI) extracted into [ReachabilityHealthCheckMixin](../backend/adapters/inference/reachability_health_mixin.py) — a standardized status builder + a generic probe driven by a caller-supplied `requester` (so each adapter keeps its own HTTP client and test patch targets).

### Cost & viability (financial review)
- **24/7 fixed GPU → spot/serverless on-demand**: the always-on L4/A100 cost **450–1 200 $/month** regardless of traffic ([docs/COST_AUDIT.md](COST_AUDIT.md)) — the dominant fixed cost, forcing ~30 000–80 000 ad-clips/month to break even. Migrated to on-demand spot/serverless GPU per §5.1‑5.2 of the cost audit, cutting the break-even threshold 3–5× (the n°1 viability lever).
- **Brain GPU scaling bounds made explicit**: [deploy_brain.py](../scripts/deploy/deploy_brain.py) left `--min/--max-instances` at Cloud Run defaults (implicit min=0, uncapped max=100). Pinned `--min-instances=0` (auditable scale-to-zero) and `--max-instances=3` (cost ceiling, aligned with `restore_brain_service`); COST_AUDIT corrected — the "fixed GPU 24/7" premise was inaccurate.
- **Zero-margin "social equilibrium" model → minimum margin**: the Berrix model recalibrated to zero margin (13/06) left no cushion for a GPU spike, an eCPM drop or churn. Restored a minimum **5–15 % margin** to build a treasury cushion; the budget-alert webhook that scales the brain service to 0 on overrun stays as an anti-bankruptcy guard.

### Frontend coverage
- **Frontend test coverage broadened** to **551 unit tests** with ratchet floors at statements 29 / branches 22 / functions 28 / lines 29. Remaining (decreasing ROI, left open): complex 3D/canvas/WebSocket flows (`useTachideskExplorer`, `useSocket`, `useMultiverseCatalog`).

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
