# TODO — Améliorations du projet Animetix

> Audit du 2026-06-21 (passe fraîche, 5 axes). Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).
>
> _Note de vérification : le `.env` contenant de vraies clés n'est PAS suivi par git (gitignored, jamais commité) — pas de fuite dans le dépôt, pas de rotation d'urgence. `error_latent.html` et `.coverage` ne sont pas suivis non plus._

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [x] **Repo — 125 Mo de données suivies dans git** _(vérifié)_
  - `data/processed/filtered_characters.json` (40 Mo), `refined_characters.json` (30 Mo), `clean_characters.json` (24 Mo), etc. Artefacts générés qui gonflent l'historique et ralentissent les clones.
  - Migrer vers Git LFS **ou** `git rm --cached` + régénération au build ; documenter le téléchargement dans le README.
- [x] **Sécu — `exec()` sur du code généré par LLM (surface RCE)** ✅ _(2026-06-22)_
  - Garde AST `assert_safe_kernel_source()` ajouté avant `exec` dans `self_evolving_compiler` : rejette `import`/`from`, l'accès aux attributs dunder (bloque les évasions `().__class__.__subclasses__()`), et une blocklist de noms dangereux (os/sys/subprocess/eval/exec/open/getattr…). `exec` tourne désormais avec des `__builtins__` restreints (`_SAFE_BUILTINS` : seulement range/len/abs/float…) — défense en profondeur. Kernel malveillant → `UnsafeKernelError` ; `evolve_with_llm` retombe sur le fallback nul sans exécuter. Kernels numériques légitimes inchangés. 13 tests de sécurité ajoutés.
- [x] **Archi — violations de la frontière hexagonale (domaine → infra)** ✅ _(2026-06-22)_
  - `manga_service` → `MangaRepositoryPort` + `DjangoMangaRepositoryAdapter` (toute la persistance ORM derrière le port ; retourne des modèles opaques pour préserver la sérialisation DRF, `DoesNotExist`→`None`).
  - `voice_ingestion_service` → `VoiceProfileRepositoryPort` + `DjangoVoiceProfileAdapter` ; service câblé via `container.core.voice_ingestion_service`.
  - `llm_service` → `UserContextPort` + `MiddlewareUserContextAdapter` (plus de reach dans `animetix.middleware` ; `user_id`/`tier` explicites prioritaires, quota préservé).
  - Aucun des 3 fichiers du cœur n'importe plus Django/animetix. Vérifié : wiring conteneur OK, tests llm/labs/manga verts.
- [x] **Archi — code de test (Mock/MagicMock) dans un service de prod** ✅ _(2026-06-22)_
  - Les 2 branches `isinstance(..., Mock)` de `AgenticRAGService.__init__` (side_effects sur llm mocké + reconstruction d'un RAGOrchestrator réel avec agents, ~130 l.) sont sorties dans une fabrique de test `tests/helpers/agentic_rag_factory.py:build_test_agentic_rag_service`. Les 14 tests qui en dépendaient sont migrés. Le `__init__` de prod n'importe plus `unittest.mock` ni ne teste de `Mock`. Comportement préservé (51 passed / 16 deselected inchangé ; wiring conteneur vert).

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

- [x] **API — fuite de stacktrace + permission par défaut trop ouverte** ✅ _(2026-06-22)_
  - **Fuite** : 27 réponses HTTP 500 qui renvoyaient `str(e)`/exception au client sont génériques (`"Internal server error"`) + `logger.exception()` côté serveur (11 fichiers `api/*`, `tasks_views`, `views/billing`). Les 4xx (feedback de validation) sont conservés.
  - **Permissions** : défaut DRF `IsAuthenticatedOrReadOnly` → **`IsAuthenticated`** (secure-by-default). Audit AST des 142 vues : seules 8 héritaient du défaut ; les vues publiques (`Multiverse*`, `AchievementViewSet`) déclarent désormais `IsAuthenticatedOrReadOnly`, les internes (monitoring/observability) se durcissent.
- [x] **Backend — `except Exception:` trop larges + constantes dupliquées** ✅ _(2026-06-22)_
  - **Constantes** : `MAX_IMAGE_SIZE` + allow-lists MIME (image/vidéo/audio) centralisées dans `backend/core/constants.py` ; `core.py`/`labs.py` importent de là (liste image unifiée avec gif ; doublons morts de labs supprimés).
  - **catch-all** : audit AST des **638** `except Exception` — la quasi-totalité loguent/renvoient un fallback délibéré (défensif légitime). Seuls **3** avalaient silencieusement ; 2 resserrés (`CreativeFusion.DoesNotExist` dans le repository ; `(ValueError, IndexError)` au parse `--threshold`), le 3e (shim de policy event-loop ASGI) laissé volontairement (best-effort commenté + `nosec`). Pas de sweep aveugle des 638 (sans valeur + risqué).
- [x] **Backend — `UnifiedInferenceAdapter` god object**
  - 8 mixins, ~476 lignes ([unified_inference_adapter.py:30](backend/adapters/inference/unified_inference_adapter.py#L30)) ; MRO fragile, dur à tester → composition plutôt qu'héritage multiple.
- [x] **Frontend — `fetch()` brut qui contourne `apiClient`**
  - [SearchBar.tsx:81](frontend/src/components/SearchBar.tsx#L81) et [AudioLabPage.tsx:127](frontend/src/pages/labs/AudioLabPage.tsx#L127) bypassent CSRF + auth Firebase + toasts → tout passer par `apiClient`.
- [ ] **Frontend — état local fragmenté**
  - [AudioLabPage.tsx:64](frontend/src/pages/labs/AudioLabPage.tsx#L64) (~13 `useState`) ; anti-pattern `JSON.stringify` en render dans [SynapticLabPage.tsx:110](frontend/src/pages/labs/SynapticLabPage.tsx#L110) → `useReducer`/hook dédié.
- [ ] **CI — gaspillage et robustesse**
  - Pas de `concurrency: cancel-in-progress` → runs redondants empilés.
  - PyTorch (~800 Mo) réinstallé sans cache dans 3 jobs ([ci.yml](.github/workflows/ci.yml) ~97/163/203).
  - Pas de `timeout-minutes` sur `perf-test`/`integration-test`.
  - À confirmer : `--cov-fail-under=75` ([ci.yml:119](.github/workflows/ci.yml#L119)) annoncé comme *hard gate* bloquant le deploy — vérifier la cohérence avec la couverture réelle.

## 🟢 Faibles

- [x] **A11y & logs frontend** : `<img>` sans `alt`, boutons admin sans `aria-label`, `console.error` laissés en prod (~41 fichiers).
- [x] **Deps** : doublon `opencv-python` + `opencv-python-headless` ([requirements.txt:580](requirements.txt#L580)) ; GCP / `transformers` peu ou pas pinnés dans [requirements.in](requirements.in) (build non reproductible).
- [x] **DX** : pas de Prettier ni `.editorconfig` ; badge README « Python 3.11+ » alors que CI/pyproject ciblent 3.12.
- [ ] **Couverture frontend — élargir** _(outillage + CI faits ; ~29 % stmts, 492 tests — cf. [HISTORY](docs/HISTORY.md))_
  - Optionnel / ROI décroissant : couvrir les flows complexes restants (3D/canvas/WebSocket) et remonter le plancher de seuils au fil de l'eau.
- [x] **Organisation des tests backend — consolidation physique** ✅ _(2026-06-21)_
  - Fusionné `tests/backend/core`→`tests/core`, `tests/backend/api`→`tests/api`, `tests/pipeline_logic`→`tests/pipeline` via `git mv` (historique préservé). Collection pytest **inchangée à 2313 tests**, échantillons rejoués verts (200 + 74 passed). `tests/README.md` mis à jour. Reste à trancher (séparé) : `tests/backend/views/…` → `tests/api/` ou conserver.
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. À purger lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).
