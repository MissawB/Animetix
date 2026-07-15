# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.
> Les entrées marquées _(audit dette 2026-07-11)_ sont issues d'un audit multi-agents backend/frontend/tests-CI/infra — preuves fichier:ligne vérifiées à l'écriture.

## 🔴 Critiques


_Aucun item ouvert._

## 🟠 Élevés

- [ ] **Fine-tune otaku — l'adaptateur est corrompu, le dataset est à refaire** _(expérience contrôlée 2026-07-13)_
  - `MissawB/otaku-qwen-7b-adapter` mergé dans sa vraie base et servi produit du **texte corrompu** : chiffres injectés au milieu des mots, personnages inventés (« Izanagi Eikichi1 » comme héros de Chainsaw Man). Même image, même quantification, même template : le modèle **stock** répond « Denji » proprement. La chaîne de service est donc saine — **c'est l'adaptateur**.
  - **Cause** : il a mémorisé le **gabarit** de `MissawB/otaku-expert-dataset`, qui est synthétique et templaté (« jouit d'une immense popularité », « figure incontournable », « se plaçant au rang numéro… »), et il **remplit les emplacements numériques au hasard**. Il a appris la forme d'une réponse, pas son contenu.
  - **Écartés** : désalignement du tokenizer (adaptateur et base partagent les mêmes 22 tokens ajoutés) et pollution du dataset (1 ligne sur 100 porte le motif, et c'est une formule mathématique).
  - **À faire** : assainir le dataset (varier les formulations, ancrer les faits, purger les emplacements numériques) **avant** tout réentraînement. Le re-servir est un `LLM_MODEL_NAME=otaku-qwen:7b` (déjà baké dans l'image, aucun rebuild).

- [ ] **Index visuel : phase 2 (35 292 portraits de personnages)** _(phase 1 livrée 2026-07-14)_
  - `unified_clip_space` contient désormais **9 165 jaquettes** (anime/manga/film/jeu) et la recherche par jaquette fonctionne en prod. `character_ccip_space` est **vide** : une recherche de personnage répond honnêtement 503 sans facturer.
  - CCIP est vérifié contre les **vrais poids** (768 dims, déterministe, personnages différents à 0,36-0,45 sur de vrais portraits du catalogue). La construction est un `python manage.py build_visual_index --target character` (reprenable, une image morte est sautée) — dominée par le téléchargement, ~35 000 images.
  - **La tour texte de CLIP est construite et testée mais aucun endpoint ne l'expose** : `VisualIndexService.encode_text` n'a aucun appelant. Soit on l'expose (la spec promet la recherche texte gratuite sur les œuvres), soit on l'assume en phase 2.

- [ ] **`PGVectorCollectionWrapper.upsert` ne sait pas écrire un vecteur pré-calculé sur AlloyDB** _(2026-07-14)_
  - La branche AlloyDB dérive l'embedding d'un `document` ; quand on lui passe un vecteur **et** aucun document — ce que fait `VisualIndexService.index` — elle ignorait l'argument et écrivait `embedding = NULL` sans exception. C'est **gardé** depuis (elle lève), mais cela signifie que le jour où l'on migre vers un vrai AlloyDB, le constructeur d'index refusera d'écrire. Lui apprendre à écrire un vecteur fourni.
- [ ] **URI Neo4j locale morte** _(constaté 2026-07-12)_
  - `Failed to DNS resolve a654e145.databases.neo4j.io` — l'instance configurée en local n'existe plus (la prod tourne sur l'instance `1254b9b8`). `reconcile_db` saute donc toutes les vérifications de graphe en silence, et personne ne le voit.

## 🟡 Moyens

- [ ] **Backend — extraction JSON réimplémentée 4× avec logiques divergentes** _(audit dette 2026-07-11)_
  - [agentic_rag_service.py:671](backend/core/domain/services/agentic_rag_service.py#L671) `_extract_json`, [vs_battle_service.py:121](backend/core/domain/services/creative/vs_battle_service.py#L121) `_extract_json`, [orchestrator_agent_service.py:145](backend/core/domain/services/orchestrator_agent_service.py#L145) `_safe_json_generate`, [llm_service.py:214](backend/core/domain/services/llm_service.py#L214) `_parse_json`. **Reco** : un utilitaire unique dans `core/utils/`.
- [ ] **Backend — module `dpo_feedback_loop` en double (core vs pipeline)** _(audit dette 2026-07-11)_
  - [core/domain/services/dpo_feedback_loop.py](backend/core/domain/services/dpo_feedback_loop.py) (225 l., câblé au container) et [pipeline/mlops/dpo_feedback_loop.py](backend/pipeline/mlops/dpo_feedback_loop.py) (246 l.) — même nom, deux implémentations proches, risque de divergence. Trancher lequel est canonique.
- [ ] **Frontend — extraire un hook `useSSE` partagé** _(audit dette 2026-07-11)_
  - [TreeOfThoughtsPage.tsx:57-113](frontend/src/pages/labs/TreeOfThoughtsPage.tsx#L57-L113) et [ExpertNexusPage.tsx:79-249](frontend/src/pages/search/ExpertNexusPage.tsx#L79-L249) réimplémentent chacune le cycle de vie EventSource (ref, cleanup, contournement 401/402) avec des commentaires quasi identiques. Le streaming est central au projet ; `hooks/useSocket.ts` existe déjà pour les WS — faire l'équivalent SSE.
- [x] **~~Backend — secrets par défaut incohérents : scripts pipeline cassés~~** _(audit dette 2026-07-11)_
  - `BRAIN_API_KEY` default `"dev-insecure-key-animetix-2026"` ([settings.py:190](backend/api/animetix_project/settings.py#L190), [brain_service.py:46](backend/adapters/inference/brain_service.py#L46)) mais `eval_ragas.py:40`, `compare_models_wandb.py:35`, `data_intelligence.py:26` utilisent `default="dev-secret-key"` → auth silencieusement cassée pour ces scripts. Correction triviale.
- [ ] **Infra — durcir `Dockerfile.brain` et `Dockerfile.dataflow`** _(audit dette 2026-07-11)_
  - `Dockerfile.brain` : single-stage (build-essential/gcc conservés), **root** (aucune directive `USER`), base `python:3.11-slim` vs 3.12 ailleurs, pas de HEALTHCHECK. [Dockerfile.dataflow:19](deploy/Dockerfile.dataflow#L19) : `USER root` jamais redescendu, launcher `:latest` non épinglé (build non reproductible).
- [ ] **Backend — config hardcodée à externaliser** _(audit dette 2026-07-11)_
  - URL de prod HF en dur [workflows_client.py:72](backend/adapters/inference/workflows_client.py#L72) (la même classe lit `BRAIN_API_URL` en env ligne 24 — incohérent) ; table de tiers ~85 l. dans [vs_battle_service.py:367](backend/core/domain/services/creative/vs_battle_service.py#L367) ; modèles en dur (`clip-ViT-B-32` ×3 dans `clip_vision.py`, `imagen-3.0-generate-001`, `jina-embeddings-v3`) ; [otaku_concepts.py](backend/pipeline/mlops/otaku_concepts.py) = 2459 lignes de dictionnaire de données → asset JSON/YAML.
- [ ] **Covertest — sortir les covers du blob JSON** _(suite de l'ingestion complète 2026-07-12)_
  - La base passe de 90 à ~4 000 mangas : [manga_covers.json](data/processed/manga_covers.json) grossit de 0,5 à ~25 Mo, chargé **intégralement en RAM** par le singleton ([pgvector_repository_adapter.py:199](backend/adapters/persistence/pgvector_repository_adapter.py#L199)) au premier appel, et `list_entries()` sérialise tout le référentiel vers le front à chaque partie. À cette taille ça doit passer en Postgres (ou au minimum : un index allégé `{id, title, aliases}` pour l'autocomplétion + les covers servies à la demande). Blob LFS lu au cold start Cloud Run = mauvais compromis au-delà de quelques Mo.
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
