# TODO — Améliorations du projet Animetix

> Audit du 2026-06-20. Priorisé par sévérité. Cette liste ne contient que le **travail ouvert** ; voir « Terminé » en bas pour le récap de ce qui est fait.

## 🔴 Critiques

_Rien d'ouvert._ (core hexagonal, imports `core.*`, SSRF, gate CI front + tsc/eslint à 0 — voir Terminé.)

## 🟠 Élevés

- [x] **Découper les fichiers monolithes** ✅ — _les 3 cibles traitées (backend dataset, frontend, conteneur DI)_
  - [x] Backend `backend/pipeline/mlops/finetuning_dataset.py` (**4650 → 1316 l., −72 %**) ✅ — approche façade (ré-export, zéro changement appelants). **9 modules** sous `ft_dataset/` (~3120 l. ; mypy ignore via wildcard `pipeline.mlops.ft_dataset.*`).
    - `text_cleaning`, `profile_builders`, `paths`, `paraphrase` (test re-ciblé), `relation_generators`, `market_profile_generators`, `synthetic_generators` (mcp_tool/rag_context/negative_refusal), `otaku_generators`, `dialogue_generators`.
    - Reste dans le facade : l'orchestrateur `run_generate_instruction_dataset` (point d'entrée/glue, légitime) + 3 petits helpers. Vérifié : `tests/mlops` **69/69**, ruff OK.
  - [x] Backend conteneur DI ✅ — `LazyClass` (dupliqué à l'identique dans 4 fichiers) extrait dans `containers/lazy.py` partagé ; `core_services.py` 524 → 440 l. (dedup + passe « registered-only »). Smoke `test_container_wiring` 3/3, ruff OK. _NB : un découpage en sous-conteneurs câblés a été écarté — refs croisées entre ~70 providers (hubs `catalog_service`/`cfr_game_solver`) → risque élevé au démarrage pour une valeur faible (config déclarative)._
  - [x] **Frontend monolithes décomposés** ✅ (3 fichiers, refactor préservateur via 3 agents parallèles) :
    - `MultiverseCatalogPage.tsx` **740 → 161 l.** → `pages/labs/multiverse-catalog/` (8 sous-composants `React.memo` + hook `useMultiverseCatalog`).
    - `TachideskExplorerPage.tsx` **724 → 157 l.** → `pages/explore/tachidesk/` (7 sous-composants `React.memo` + hook `useTachideskExplorer`).
    - `Layout.tsx` **475 → 118 l.** → `components/layout/` (Sidebar/Settings/Overlay/Footer `React.memo` + hook `useThemeSync`) ; export par défaut + `LayoutProps` inchangés.
    - Préservation stricte (DOM/classNames/ids/hook-order identiques ; callbacks `useCallback` pour les enfants memoïsés). Vérifs : `tsc` 0, eslint 0 sur les zones touchées, `vite build` OK, vitest 69/69.

- [x] **Services RAG / dead-code** — _fait ; prémisse de l'audit initial corrigée_ ✅
  - [x] **Audit dead-code** (script réutilisable `scripts/audit_dead_services.py`, cherche imports + chaînes DI + noms de classes) : sur 123 modules, **118 prod / 3 test-only / 2 morts**. La prémisse « ~125 services, probable code mort » était **fausse**.
  - [x] Supprimé les 2 morts (0 réf nulle part) : `akinetix/self_play_collector.py`, `akinetix_rl_trainer.py` + nettoyage `pyproject.toml`.
  - [x] Supprimé les 3 test-only (jamais câblés en prod) + leurs tests : `dynamic_tool_agent.py` (+2 tests), `multimodal_orchestrator.py` (+1 test), `synaptic_plasticity.py` (doublon de `neuromorphic_plasticity_service.SynapticPlasticityService` ; section retirée de `test_singularity.py`) + nettoyage `pyproject.toml`.
  - **Re-audit final : 0 mort / 0 test-only, 0 référence résiduelle** ; `test_singularity` 4/4, collection tests/core+pipeline OK, tests akinetix/rl verts.
  - [x] **Passe DI « registered-only » (analyse résolution-réelle, au-delà du script)** : providers enregistrés mais **jamais résolus** → supprimés avec leurs modules : `static_diorama_3d_service.py`, `video_language_indexing_service.py`. Providers morts dupliqués retirés (modules conservés car utilisés via un provider frère) : `akinetix_expert_service` (→ `akinetix_service`), `vlm_indexing_service` (→ `cross_modal_search_service`). Wire mort retiré : `video_rag_service` injecté dans `ResearchProcessor` mais jamais lu (5 sites + scaffolding). Vérifs : `test_container_wiring` 3/3, suite RAG processors/state-machine verte (hors 2 tests ollama-dépendants préexistants).
  - ~~Consolider les 3 RAG en un `RAGService`~~ : **abandonné** — `advanced_rag` / `agentic_rag` / `hierarchical_graph_rag` ne se recouvrent pas, ils se **composent** (agentic orchestre + utilise advanced ; hierarchical = enrichisseur de graphe). Fusionner réduirait la clarté.

- [ ] **Renforcer le typage**
  - Backend : 106 → **105** modules en `ignore_errors=true`. Retiré l'entrée morte `static_diorama_3d_service` (module supprimé ; mypy signalait « unused section »).
  - ⚠️ **Burn-down complet bloqué localement** : impossible de lancer un mypy équivalent à la CI. (1) dbt épingle `pathspec<0.13`, incompatible avec le mypy installé qui exige `pathspec.patterns.gitignore` (≥1.x) ; (2) le seul mypy qui tourne localement est un **v2.1.0 non-standard** qui **diverge de la CI** (trouve 14 erreurs hors-liste alors que la CI mypy est verte). Piloter le burn-down dessus risquerait de casser la CI. → **À faire dans un venv propre type-CI** (`pip install mypy`, sans dbt).
  - Méthode pour le burn-down (env CI) : désactiver l'override `ignore_errors`, lancer `cd backend && mypy .`, retirer de la liste tout module à **0 erreur** (sûr), puis verifier vert.
  - 🔎 Piste détectée (à confirmer en env CI) : contrat de streaming incohérent — `StateProcessor.process` annonce `Generator[StreamStep,…]` mais les processors (`judge/graph_explore/fallback/acquire_knowledge`) annotent `Generator[dict,…]` et yieldent `StreamStep(...).model_dump()` (dicts). Harmoniser le type (base en `dict`, ou implémentations sans `.model_dump()`).
  - Frontend : les `any` bloquants sont résorbés (eslint `no-explicit-any` actif et vert). Reste à durcir progressivement les interfaces les plus laxistes.

- [~] **CI : garde-fou de couverture** — _gate posé + backlog de tests fait ; reste le job d'intégration_
  - [x] `pytest-cov` dans `requirements.txt` (déjà épinglé `==5.0.0`) ; `pip install` redondant retiré de la CI.
  - [x] **`--cov-fail-under=75`** ajouté (gate dur, bloque `deploy-to-prod`) — intentionnellement rouge tant que le backlog ci-dessous n'a pas remonté la couverture globale (baseline 55,73 %).
  - [x] **Upload Codecov** (`codecov-action@v4`, `if: always()`, non-bloquant). Dépôt public → tokenless OK.
  - [ ] Job d'intégration optionnel (skip gracieux si Ollama absent) — **reporté** : nécessite un hook `conftest` qui ping ollama et skip les tests `integration` s'il est injoignable.
  - **Listing des chantiers de tests à implémenter** (Couverture actuelle: 55.73% / requis: 75%) :
    - [x] *Priorité 1 : MLOps & Ingestion* ✅ — **8 modules à 0 % → ~92 % agrégé, ~105 tests verts**
      - [x] Scrapers/ingesteurs externes : `jikan_enrichment` (81 %), `expert_enrichment` (95 %) — 18 tests, HTTP/sleep/I-O mockés.
      - [x] Ingestion/vectorisation manga : `fetch_covers` (96 %), `ingest_manga` (97 %), `vectorize_manga` (93 %) — 38 tests, HTTP/embeddings/vector-store/Neo4j mockés.
      - [x] Entraînement/DPO/Fusion : `rlhf_pipeline` (99 %), `merge_lora_weights` (97 %), `train_preference` (87 %) — 49 tests, torch/peft/transformers/datasets/trl mockés. Plafond honnête 87 % sur train_preference (chemin unsloth = glue non testable sans faux-vert).
    - [x] *Priorité 2 : Consumers temps réel (Django Channels)* ✅ — **3 modules à 0 % → ~97 % agrégé, 66 tests verts**
      - [x] `consumers/duel.py` (**100 %**, 13 tests) : réconciliation d'état du duel (guess correct/faux, scoring, tour, win, reward).
      - [x] `consumers/codemanga.py` (**100 %**, 19 tests) : génération de grille (9 bleu/8 rouge/7 neutre/1 assassin), clic-carte, tours, win, masquage de rôles.
      - [x] `consumers/speech_to_speech_live.py` (**95 %**, 34 tests) : helpers audio purs (`pcm_to_wav`/`process_client_audio` via `audioop`) + handshake/receive/run_gemini_session/disconnect mockés.
      - [x] **Flakiness corrigée** : l'e2e Channels existant (`test_speech_to_speech_live`) cassait par moments sous charge (timeouts `receive_json_from` à 1 s par défaut) → timeouts portés à 5 s. Stable sur 3 runs consécutifs. _NB : namespace de couverture = `animetix.consumers.*` (pas `api.animetix.*`, double-registration de modèles)._
    - [x] *Priorité 3 : Adaptateurs & Mocks de services externes* ✅ — **6 modules à 0 % → 100 % chacun, ~155 tests verts**
      - [x] Inférence multimodale/GPU OOM : `moondream_adapter` (100 %, 18 t.), `qwen3_vl_adapter` (100 %, 24 t.), `brain_api_adapter` (26 %→**100 %**, 67 t.) — model load/generate/OOM/HTTP mockés.
      - [x] pgvector/cache sémantique/reranker : `django_safety_adapter` (100 %), `django_semantic_cache_adapter` (100 %, store Chroma + cache exact), `colbert_adapter` (100 %, MaxSim late-interaction).
      - [x] 🐛 **Vrai bug prod corrigé** : `django_safety_adapter` utilisait `action_taken` (create/filter/lecture) alors que le champ modèle est `action` → crash `TypeError`/`FieldError` à chaque event de sécurité. Corrigé + **test `@django_db` round-trip** ajouté comme verrou de régression (le test mocké masquait le bug).
    - [x] *Priorité 4 : Frontend React (Vitest)* ✅ — **117 tests, vitest 69 → 191**
      - [x] Stores Zustand : core (`uiStore`/`toastStore`/`passiveMiningStore`), jeux/labs/companion (`akinetix`/`blindtest`/`paradox`/`vision`/`videoRag`/`companion`), `authStore` (Firebase mocké), `notificationStore` (WebSocket mocké) — transitions d'état réelles, isolation `beforeEach`.
      - [x] `ErrorBoundary` : rendu enfant OK + fallback sur throw + report Sentry mocké.
      - [x] Offline/sync : `offlineLibrary` (idb-keyval via `fake-indexeddb`, round-trips download/list/read-blobs/delete, rollback 404, `QuotaExceededError`), `persister` (persist/restore/remove). _NB : Cache API/SW Workbox non unit-testables en jsdom._
      - _NB : exécuter via `--project unit` (le repo a aussi un projet vitest storybook-browser)._

- [x] **Pollution des tests** ✅ (2026-06-21)
  - **Proactor fail-fast** : `tests/conftest.py` — retiré le `try/except pass` qui masquait l'échec de la policy d'event-loop (toute erreur remonte désormais).
  - **Fixture globale anti-pollution** (`conftest._cleanup_module_pollution`, autouse) : après chaque test, retire les modules de type `Mock` ajoutés pendant le test dans `sys.modules` + vide le cache `core.utils.lazy_import._loaded_modules`. Défense en profondeur contre les fuites de mocks.
  - **Vraie fuite corrigée** : `tests/adapters/test_video_rag.py` écrasait `sys.modules["imageio"]` au niveau module (fuite sur toute la suite ; `imageio` est pourtant installé et importé paresseusement). → déplacé dans un fixture `monkeypatch.setitem` (auto-restauré). NB : `test_creative_inference.py` utilisait déjà `monkeypatch.setitem` (OK).
  - Vérif : `tests/adapters` + `tests/core` = **466 passed**, seuls restent les 4 tests ollama-dépendants préexistants ; les 2 échecs `test_prompt_loading` du baseline ont **disparu** (pollution `lazy_import` éliminée).

- [x] **Gestion d'erreurs** ✅ (2026-06-21)
  - **Frontend** (l'audit était dépassé : `ErrorBoundary` racine + `Sentry.init` via `initObservability()` existaient déjà). Ajouté ce qui manquait :
    - `ErrorBoundary.componentDidCatch` → **reporte à Sentry** (`captureException` + `componentStack`) au lieu d'un simple `console.error`.
    - `queryClient` : **handler d'erreurs centralisé** via `QueryCache`/`MutationCache` `onError` → Sentry ; **retry intelligent** (pas de retry sur 4xx). Pas de toast ici (déjà émis par `apiClient` → évite le doublon).
    - `apiClient` : attache le **code HTTP** (`.status`) à l'erreur levée (permet le retry-skip 4xx).
    - Vérifs : `tsc` 0, eslint 0, **vitest 74/74**, `vite build` OK.
  - **Backend** : les **9** `except: pass` recensés → seuls **5** étaient de vrais avalements silencieux d'`Exception` (best-effort cache/metric/download) : rendus **observables** par un `logger.debug/warning` sans changer le flux (health_dashboard, fallback_adapter ×2, tasks/__init__, models voice-sample). Les `except ImportError`/`except ValueError` (import optionnel, validation d'input) laissés tels quels (corrects). **0 `except Exception: pass` restant.**
  - _Volontairement non fait_ : narrer les ~615 autres `except Exception as e: logger…` — ce sont des fallbacks intentionnels ; un sweep aveugle « exceptions précises » serait risqué et à traiter au cas par cas, pas en masse.

## 🟡 Moyens

- [~] **MLOps reproductibilité** — _provenance des checkpoints faite ; DVC/MLflow écartés_ (2026-06-21)
  - Correction de l'audit : `manifest.json` **pin déjà** les modèles de base par `revision` (commit HF) ; le tracking d'expériences existe via **Trackio** (`train_expert_model`/`train_preference`). Vrai manque = pas de **provenance** (commit/timestamp) sur les checkpoints.
  - [x] Helper `pipeline/mlops/run_provenance.py` (commit git + timestamp UTC + révisions manifest → `run_metadata.json` à côté du checkpoint), **6 tests verts**. Câblé dans `train_expert_model.py` + `train_preference.py` (écrit le metadata + logge `git_commit` au tracker). py_compile + ruff OK ; `tests/mlops` 75/75. _(scripts d'entraînement non exécutables ici : torch/unsloth/GPU — câblage vérifié syntaxiquement.)_
  - [ ] _Optionnel, plus lourd_ : DVC/MLflow (versioning data/modèles avec remote) — écarté pour l'instant (infra + remotes à configurer, non vérifiable ici). « wandb en CI » n'a pas de sens (pas d'entraînement en CI).
- [~] **dbt** ✅ (2026-06-21) — _not-null/unicité/freshness faits ; metrics (semantic layer) écarté_
  - Correction de l'audit : not_null + unique + relationships + accepted_values **existaient déjà** dans les YAML de sources (« un seul test SQL » ne comptait que le test *singulier*).
  - [x] **Freshness** ajoutée à `telemetry_source` (streaming continu) : `loaded_at_field: created_at`, warn 6 h / error 24 h.
  - [x] `not_null` sur `created_at` des 2 tables telemetry (garantit le champ de freshness).
  - [x] 2ᵉ **test SQL singulier** `archetype_drift_affinity_check.sql` (affinités shonen/seinen ∈ [0,1], comme `intensity`).
  - Vérifié : `dbt parse` propre + `dbt list` confirme tests/sources enregistrés. _(`dbt test`/`source freshness` non exécutables ici : pas de connexion BQ/données.)_
  - [ ] _Écarté_ : **metrics** = couche sémantique dbt (MetricFlow) — opinion + setup lourd, non vérifiable sans semantic layer. À faire en chantier dédié si besoin.
- [x] **Pré-commit** ✅ (2026-06-21) — ajoutés à `.pre-commit-config.yaml`, alignés sur la CI :
  - ruff + black restent au stage **pre-commit** (rapide). mypy + pytest ajoutés au stage **pre-push** (lourds) via `default_install_hook_types: [pre-commit, pre-push]`.
  - **pytest** (`-m "not integration"`, miroir du job CI) : **vérifié vert (1061 passed)** — et a même attrapé une vraie régression (`test_deploy_jobs` resté à 7 jobs après l'ajout du job manga ; **corrigé** → 33 appels).
  - **mypy** (`cd backend && mypy . --config-file ../pyproject.toml`, miroir CI) : mécanisme du hook **vérifié** (se déclenche bien), mais échoue sur le bug **pathspec/dbt** local connu → documenté dans le fichier (`SKIP=mypy` ou venv propre type-CI). Fonctionne en env CI.
  - `--lf` non retenu (un gate pre-push doit lancer la suite pertinente, pas seulement les derniers échecs) ; noté comme option.
- [x] **`requirements.txt`** ✅ (2026-06-21) — _l'audit était trompeur_
  - « 22k lignes » = en fait **22 Ko / 1096 lignes**, un output **pip-compile propre et canonique** (`pip-compile --allow-unsafe --strip-extras requirements.in`, avec commentaires `via`). **Rien à nettoyer.**
  - Vérifié **en phase** avec `requirements.in` (75 déps directes toutes présentes) → pas de désync, **pas de régénération** (re-pinner vers les dernières versions = churn risqué non testé, d'autant que ce venv dbt/pathspec polluerait l'output).
  - [x] Supprimé `requirements.txt.bak` (backup local périmé, gitignoré/non suivi → suppression locale, rien à committer).
- [~] **État frontend fragmenté** — _`window.location.reload()` éliminés ; convention des stores laissée ouverte_
  - [x] **`window.location.reload()` → React Query / actions** (2026-06-21) : 6 reloads fonctionnels remplacés, le seul restant est l'`ErrorBoundary` (recovery de crash, légitime).
    - `useAkinetix` : reload redondant retiré (`invalidateQueries` déjà présent).
    - `akinetixStore.submitConfirmation` : `get().restartGame()` (le store avait déjà l'action) au lieu de reload.
    - 3 pages jeu (Classic/Covertest/Emoji) : nouveau `restart()` exposé par chaque hook (`invalidateQueries(QUERY_KEY)` → rejoue la queryFn comme un remount) ; bouton REJOUER câblé dessus.
    - `ClubDashboard` (création d'événement) : `invalidateQueries(['club', clubId, 'events'])` (clé de `useClub`) au lieu de reload.
    - Vérifs : `tsc` 0, eslint 0 (fichiers touchés), **vitest 74/74**, `vite build` OK.
  - [ ] _Reste (architectural, non mécanique)_ : harmoniser la convention de state (9 stores Zustand vs React Query vs useState) — décision de design à cadrer, pas un sweep.
- [x] **`features/` ↔ `pages/`** ✅ (2026-06-21) — _prémisse corrigée : pas de duplication_
  - Vérifié : **0 fichier en double** entre `features/` et `pages/`. C'est un **layering sain** (`features/` = logique : hooks/services/stores/components/routes ; `pages/` = composants d'écran). Les seuls hooks sous `pages/` (tachidesk, multiverse-catalog) sont **page-spécifiques co-localisés** (issus du découpage des monolithes) → légitime.
  - **Migration `modules/` écartée** : ≈265 fichiers + imports/routing/lazy/PWA/tests = haut risque pour un gain marginal sur une convention déjà correcte (l'audit disait « envisager »).
  - [x] **Convention documentée** : section « Structure & conventions » réécrite dans `frontend/README.md` (était obsolète) avec un tableau « où mettre quoi » (features vs pages vs components vs store).
- [x] **Async backend — stratégie tranchée & documentée** ✅ (2026-06-21)
  - Audit du réel : async dans le core = **5 fichiers seulement** (multi_agent_bus, orchestrator_agent, reasoning_agent + `state_port` abstrait + helper HTTP). **0 `asyncio.run`, 0 `async_to_sync`/`sync_to_async`** → **aucune violation de frontière active**. Le split est propre (ex. `ReasoningAgentService` : API publique **sync** `solve_complex_query`, callback bus `_on_bus_message` **async** confiné au bus).
  - **Décision** (modèle canonique Django+Channels) : **core/vues = sync** ; async confiné à 2 edges — (1) consumers ASGI/Channels, (2) sous-système bus multi-agent (Redis pub/sub, non câblé HTTP, expérimental). Règles de frontière : `async_to_sync`/`sync_to_async` aux jonctions, jamais `asyncio.run()` par requête sous ASGI.
  - **Documenté** : nouvelle section « 4bis. Async / Sync Strategy » dans `docs/ARCHITECTURE.md` (edges, règles de frontière, helpers HTTP sync/async). Pas de réécriture (aucun bug actif).
- [~] **Performance frontend** — _gros levier (précache PWA) fait ; fignolages restants_
  - Constat : les pages lourdes sont **déjà lazy** (115 routes `lazy()`) → `plotly-vendor` (4,6 Mo) et three.js (`GLBViewer`) ne sont **pas** chargés d'office. Le vrai problème était le **précache PWA** (limite 6 Mo → plotly précaché pour tous).
  - [x] **Précache PWA allégé** (`vite.config.ts`) : `maximumFileSizeToCacheInBytes` 6 → 2 Mo + `globIgnores` du chunk plotly + `runtimeCaching` (StaleWhileRevalidate sur `/static/assets/*.{js,css}`). **Précache 144 entrées / 7,5 Mo → 143 / ~3,0 Mo (−60 %, ≈4,5 Mo de moins par visiteur)** ; offline préservé après 1re visite. `vite build` OK.
  - [ ] _Fignolages (diffus, ROI moindre)_ : `loading="lazy"` sur les `<img>` ; `React.memo`/`useMemo` ciblés (déjà partiellement fait via le découpage des monolithes).

## 🟢 Faibles

- [~] **Accessibilité frontend** — _règles durcies ; quelques labels restants en warn_
  - Constat : `jsx-a11y` **recommended** était déjà actif. Le lint (`eslint .`) **ne casse pas sur les warnings**.
  - [x] **Durci `eslint.config.js`** : `no-static-element-interactions`, `click-events-have-key-events`, `no-noninteractive-element-interactions`, `no-noninteractive-tabindex` passés en **`error`** (déjà 0 violation → enforcement sans risque) ; `control-has-associated-label` en **`warn`** (cas existants à résorber, gate-safe).
  - [x] Corrigé les cas clairs (`aria-label`) : boutons de couleur (`AccountSettingsPage`) + 2 boutons d'action admin (`UserManagementPage`). Mes fichiers : **0 erreur**.
  - [ ] Restent quelques `control-has-associated-label` en **warn** (contrôles icône / lignes de tableau / div draggable `AudioLabPage`) à étiqueter, puis passer la règle en `error`.
  - ⚠️ NB (hors périmètre) : le front est momentanément **rouge** (≈19 erreurs eslint + `check-types` KO sur `ProfilePage.tsx`) à cause de **travail parallèle concurrent** — non lié à ces changements a11y.
- [ ] **Couverture de tests frontend faible** (~12 %) — ajouter `vitest --coverage`, tests stores/hooks/UI.
- [ ] **Organisation des tests backend** — `tests/backend/` vs `tests/core/` se recouvrent.
- [ ] **Logging MLOps** — `logging.basicConfig` répété par script ; centraliser.
- [ ] **E2E Playwright** — Chromium seul, pas de screenshots on failure ni d'artefacts CI.
- [ ] **K6 load test** présent mais hors CI, sans baseline.
- [ ] **`Dockerfile.dataflow`** — pas de HEALTHCHECK, fichier pipeline figé.

---

## ✅ Terminé (récap — détail dans l'historique git)

- **Architecture core hexagonale** — `core` n'importe plus Django/`pipeline`/`get_container()`. 4 tranches : ports `Cache`/`Config`/`VectorStore` + adapters, `guardrail_service` déplacé dans le conteneur `agentic` (dépendance circulaire résolue).
- **Imports `backend.core.*` → `core.*`** — double-namespace éliminé (15 fichiers source + 19 de test).
- **SSRF `sample_url` (Animetix Voice)** — validation `safe_http_request` (IP privées/loopback/link-local à chaque hop) + à l'ingestion.
- **Garde-fou CI front** — job `frontend-checks` (`check-types` + `lint`) branché sur `deploy-to-prod` ; `api.d.ts` ignoré par ESLint.
- **Frontend `tsc` 131 → 0** — `ReferenceError` runtime (catch cassés, imports manquants), Plotly, types app, cluster XAI, variantes `Button`, force-graph ; `useAniminator.ts` mort supprimé.
- **Frontend ESLint 132 → 0** — `no-explicit-any`, `no-unused-vars`, `react-hooks/*`, `jsx-a11y`.
- **Désync schéma backend ↔ front** — `wallet_balance` (serializer + mapping) ; vs_battle (serializers DRF + `@extend_schema`) ; XAI (6 serializers structurés sur l'évènement SSE `xai_report`, conteneurs optionnels). `api.d.ts` resync.
- **Tests frontend** — 6 tests réparés/réécrits (régression boucle infinie `SynapticLabPage` ; `Navbar`/`AdminCuration`/`Akinetix` ; test orphelin `MultiverseLabPage` → `MultiverseStudioPage`). Suite **69/69**.
