# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.

## 🔴 Critiques

_Aucun item ouvert._

## 🟠 Élevés

- [ ] **Backend — exceptions avalées dans les adapters d'inférence, dont le guardrail (fail-open)** _(audit dette 2026-07-11)_
  - ~14 blocs `except: pass` dans [google_genai_adapter.py](backend/adapters/inference/google_genai_adapter.py), idem `brain_api_adapter`, `moondream_adapter`, `manga_ocr_adapter`, `diffusers_adapter`, `vision_transformers_adapter` (~4 chacun) — un échec d'inférence disparaît sans trace. Cas sensible : **6 avalages dans `guardrail_service.py`** = fail-open potentiel d'un service de sécurité. **Reco** : logger en `warning` a minima (pattern existant : [vs_battle_service.py:141](backend/core/domain/services/creative/vs_battle_service.py#L141)).
- [ ] **CI — topologie fragile : docker-build bloque les tests, perf-test paie des API réelles** _(audit dette 2026-07-11)_
  - `test` a `needs: [lint, docker-build]` ([ci.yml:78](.github/workflows/ci.yml#L78)) : build d'image lent/cassé = zéro feedback unitaire ; `frontend-test` dépend aussi de `docker-build` sans besoin réel ([ci.yml:292](.github/workflows/ci.yml#L292)). `perf-test` (bloquant deploy) appelle Gemini/OpenAI réels à chaque push ([ci.yml:251-253](.github/workflows/ci.yml#L251-L253)) → coût + flakiness. Ollama installé + `ollama pull qwen2.5:0.5b` à chaque run **sans cache** ([ci.yml:165-182](.github/workflows/ci.yml#L165-L182)). **Reco** : découpler `test` du build Docker, cacher ollama, passer perf-test en job planifié ou non-bloquant.
- [ ] **Tests — métier critique quasi non testé sous un gate à 1,45 pt de marge** _(audit dette 2026-07-11)_
  - Global 76,45 % vs `--cov-fail-under=75` ([ci.yml:135](.github/workflows/ci.yml#L135)) : toute petite régression casse le deploy. Le global masque : **`stripe_billing.py` 20 % (paiement)**, `alert_service.py` **0 %**, `validation_gate.py` **0 %**, consumers `undercover` 38 %, `quiz_who.py` 23 %, `animinator.py` 26 %, `semantic_cache_service.py` 31 %. **Reco** : tester Stripe billing en priorité, puis re-calibrer le gate.

## 🟡 Moyens

- [ ] **Frontend — finir la migration `api.ts` → services de feature** _(audit dette 2026-07-11)_
  - [api.ts](frontend/src/api.ts) god-module legacy (415 lignes, ~60 fonctions, importé par **31 fichiers**) coexiste avec 20 services modernes dans `features/*/services/`. Deux conventions pour la même chose. **Reco** : migrer les 31 importeurs puis supprimer le module.
- [ ] **Frontend — frontière API non typée + types maintenus en double** _(audit dette 2026-07-11)_
  - [apiClient.ts](frontend/src/utils/apiClient.ts) retourne `any` implicite ; les services castent à l'aveugle (`as RawBlindtestState`, [blindtestService.ts:79](frontend/src/features/games/services/blindtestService.ts#L79)) alors que **zod est installé** (2 imports seulement). 79 interfaces manuelles dans [types/index.ts](frontend/src/types/index.ts) doublonnent `types/api.d.ts` généré depuis OpenAPI (8 références à `components['schemas']` seulement). **Reco** : dériver les types du schéma généré + valider les réponses critiques avec zod.
- [ ] **Backend — extraction JSON réimplémentée 4× avec logiques divergentes** _(audit dette 2026-07-11)_
  - [agentic_rag_service.py:671](backend/core/domain/services/agentic_rag_service.py#L671) `_extract_json`, [vs_battle_service.py:121](backend/core/domain/services/creative/vs_battle_service.py#L121) `_extract_json`, [orchestrator_agent_service.py:145](backend/core/domain/services/orchestrator_agent_service.py#L145) `_safe_json_generate`, [llm_service.py:214](backend/core/domain/services/llm_service.py#L214) `_parse_json`. **Reco** : un utilitaire unique dans `core/utils/`.
- [ ] **Backend — module `dpo_feedback_loop` en double (core vs pipeline)** _(audit dette 2026-07-11)_
  - [core/domain/services/dpo_feedback_loop.py](backend/core/domain/services/dpo_feedback_loop.py) (225 l., câblé au container) et [pipeline/mlops/dpo_feedback_loop.py](backend/pipeline/mlops/dpo_feedback_loop.py) (246 l.) — même nom, deux implémentations proches, risque de divergence. Trancher lequel est canonique.
- [ ] **Frontend — extraire un hook `useSSE` partagé** _(audit dette 2026-07-11)_
  - [TreeOfThoughtsPage.tsx:57-113](frontend/src/pages/labs/TreeOfThoughtsPage.tsx#L57-L113) et [ExpertNexusPage.tsx:79-249](frontend/src/pages/search/ExpertNexusPage.tsx#L79-L249) réimplémentent chacune le cycle de vie EventSource (ref, cleanup, contournement 401/402) avec des commentaires quasi identiques. Le streaming est central au projet ; `hooks/useSocket.ts` existe déjà pour les WS — faire l'équivalent SSE.
- [ ] **Backend — vue `multiverse.py` de 280 lignes : Cypher + PDF inline** _(audit dette 2026-07-11)_
  - [multiverse.py:289](backend/api/animetix/api/multiverse.py#L289) : le `get()` exécute 3 requêtes Cypher directement puis génère un PDF reportlab inline — aucune couche service ; une 2e vue de 127 l. au même fichier ([multiverse.py:107](backend/api/animetix/api/multiverse.py#L107)). **Reco** : extraire service + presenter.
- [ ] **Backend — secrets par défaut incohérents : scripts pipeline cassés** _(audit dette 2026-07-11)_
  - `BRAIN_API_KEY` default `"dev-insecure-key-animetix-2026"` ([settings.py:190](backend/api/animetix_project/settings.py#L190), [brain_service.py:46](backend/adapters/inference/brain_service.py#L46)) mais `eval_ragas.py:40`, `compare_models_wandb.py:35`, `data_intelligence.py:26` utilisent `default="dev-secret-key"` → auth silencieusement cassée pour ces scripts. Correction triviale.
- [ ] **Infra — durcir `Dockerfile.brain` et `Dockerfile.dataflow`** _(audit dette 2026-07-11)_
  - `Dockerfile.brain` : single-stage (build-essential/gcc conservés), **root** (aucune directive `USER`), base `python:3.11-slim` vs 3.12 ailleurs, pas de HEALTHCHECK. [Dockerfile.dataflow:19](deploy/Dockerfile.dataflow#L19) : `USER root` jamais redescendu, launcher `:latest` non épinglé (build non reproductible).
- [ ] **Backend — config hardcodée à externaliser** _(audit dette 2026-07-11)_
  - URL de prod HF en dur [workflows_client.py:72](backend/adapters/inference/workflows_client.py#L72) (la même classe lit `BRAIN_API_URL` en env ligne 24 — incohérent) ; table de tiers ~85 l. dans [vs_battle_service.py:367](backend/core/domain/services/creative/vs_battle_service.py#L367) ; modèles en dur (`clip-ViT-B-32` ×3 dans `clip_vision.py`, `imagen-3.0-generate-001`, `jina-embeddings-v3`) ; [otaku_concepts.py](backend/pipeline/mlops/otaku_concepts.py) = 2459 lignes de dictionnaire de données → asset JSON/YAML.
- [ ] **Tests — hygiène : fixtures dupliquées, snapshot `sys.modules`, env forcé à l'import** _(audit dette 2026-07-11)_
  - `api_client` défini **38×**, `mock_prompt_manager` et `mock_engine` **22×** chacun (2 conftest seulement) → factoriser. Fixture autouse [tests/conftest.py:107-139](tests/conftest.py#L107-L139) snapshot/restore `sys.modules` entier à chaque test pour compenser les mocks fuyants (`test_diffusers_adapter.py:25`). `BRAIN_API_URL` forcé au niveau import ([tests/conftest.py:12](tests/conftest.py#L12)) masque les tests d'absence de config.

## 🟢 Faibles

- [ ] **Brain — intégration Moshi (S2S local) chimérique : réécrire ou supprimer**
  - [audio_mixin.py:105](backend/adapters/inference/audio_mixin.py#L105) importe `from moshi.models import Moshi` — cette classe **n'existe pas** dans le package réel (API : `loaders.get_mimi`/`get_moshi_lm` + boucle streaming `LMGen`). Le chemin S2S local n'a jamais fonctionné (le package n'a de plus jamais été dans un lockfile) et lève proprement `InferenceError` — le S2S passe par le brain/Gemini Live. **Décision à prendre** : réécrire l'intégration sur la vraie API (chantier GPU, ~24 Go VRAM pour moshiko-bf16, invérifiable localement) ou supprimer le chemin mort. Le package `moshi` n'est volontairement PAS ajouté aux locks (constat 2026-07-11, en réparant ColPali qui, lui, correspondait à la vraie API).
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0` (dernière release publiée). Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. **Condition de déblocage** : la levée du cap (`jsonpickle>=3.0.4,<5.0.0`) n'existe que sur la branche `master` d'apache-beam ([PR #38769](https://github.com/apache/beam/pull/38769) ; prévue ~2.75.0, **non confirmée**). À ce moment-là : montée d'`apache-beam` dans [requirements.in](requirements.in) + re-`pip-compile` **complet** (beam co-épingle protobuf/grpcio/pyarrow/numpy/dill — pas d'épinglage chirurgical) + bump **lockstep** du tag de base [Dockerfile.dataflow:10](deploy/Dockerfile.dataflow#L10) (`apache/beam_python3.12_sdk:2.74.0`, sinon mismatch SDK worker ↔ pin = échec de soumission Dataflow). _Caveat_ : aucune release `jsonpickle` 4.x n'est à ce jour marquée comme corrigeant les CVE (CVE-2020-22083, CVE-2025-55136 : « Patched: None », disputées par le mainteneur) — la montée **défige** la version sans forcément clore formellement le finding. (Recherche multi-agents 2026-06-25.)
- [ ] **Frontend — plotly.js (~4,6 Mo) importé statiquement dans 8 pages** _(audit dette 2026-07-11)_
  - [AIUsagePage.tsx:18](frontend/src/pages/auth/AIUsagePage.tsx#L18), `LatentSpacePage`, `LiquidNeuralNetworkLabPage`, `StrategyLabPage`, `SeichijunreiMapPage`, `ArchetypeNexusPage`, `TransparencyPage`… Le chunk est isolé (`plotly-vendor`, [vite.config.ts:98](frontend/vite.config.ts#L98)) mais chaque visite télécharge 4,6 Mo — `AIUsagePage` n'affiche qu'un historique simple. + three.js dans 5 fichiers. **Reco** : lazy-import interne ou lib légère pour les graphes simples ; auditer via `stats.html` déjà généré.
- [ ] **Tests frontend — gate de couverture cosmétique (~29 %)** _(audit dette 2026-07-11)_
  - 145 fichiers de test + Playwright e2e + a11y bien câblés en CI, mais seuils vitest à statements 29 / branches 22 / functions 28 / lines 29 ([vite.config.ts:129-133](frontend/vite.config.ts#L129-L133)). Remonter progressivement.
- [ ] **CI — mono-cible : Windows jamais testé** _(audit dette 2026-07-11)_
  - Un seul `ubuntu-latest` / Python 3.12, aucune matrix — alors que toute la logique anti-pollution async du conftest cible Windows ([tests/conftest.py:14-18](tests/conftest.py#L14-L18)). Angle mort jamais couvert.
- [ ] **`scripts/` — 44 scripts one-off accumulés** _(audit dette 2026-07-11)_
  - `fix_prompt.py`, `fix_adapters_batch.py`, `migrate_gold_set.py`, `add_prompt.py`, `merge_translation_fragments.py`… (pic 2026-07-02, import massif) + des `test_*.pyc` dans `scripts/__pycache__/`. Archiver, supprimer ou documenter.
- [ ] **Frontend — composants > 500 lignes** _(audit dette 2026-07-11)_
  - [BlindtestPage.tsx](frontend/src/pages/games/BlindtestPage.tsx) (753 — filtres/scoring + sous-composants inline + rendu), `TransparencyPage` (614), `AudioLabPage` (573), `LabHubPage` (569), `SpeechToSpeechLabPage` (544)… Découper au fil de l'eau (sous-composants + hooks métier).
- [ ] **Deps — doublons et divers** _(audit dette 2026-07-11)_
  - Lock backend : 3 clients HTTP (aiohttp/httpx/requests), 2 sérialiseurs JSON (orjson/ujson) — souvent transitifs, à vérifier. `@tanstack/react-query-devtools` en `dependencies` ([package.json:31](frontend/package.json#L31)) — vérifier le tree-shaking prod. `docs/COST_AUDIT.md` cite encore GPT-4o/Claude 3 Sonnet (daté). Full-scan Python évitable : [admin_api.py:165-169](backend/api/animetix/api/admin_api.py#L165-L169) charge toute la table Profile pour filtrer en Python.
- [ ] **Backend — DI contourné et double voie Neo4j** _(audit dette 2026-07-11)_
  - [dependencies.py:14-19](backend/api/animetix/api/dependencies.py#L14-L19) résout via l'instance globale du container (work-around coverage documenté) au lieu de `@inject/Provide`. Les scripts pipeline instancient `Neo4jClient` directement ([neo4j_client.py:55](backend/pipeline/neo4j_client.py#L55), [neo4j_sync.py:29](backend/pipeline/neo4j_sync.py#L29)) hors container → deux voies d'accès Neo4j.
