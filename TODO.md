# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

_Rien d'ouvert._

## 🟡 Moyens

- [ ] **Backend — noms de modèles hardcodés + mismatch de version** _(revue archi 2026-06-22 ; en partie fait)_
  - ✅ Phase 1 : registre sécu [model_registry.py](backend/core/utils/model_registry.py) (SHA + trust). ✅ Phase 2a : unification Gemini en 3 rôles canoniques via [gemini_models.py](backend/core/utils/gemini_models.py) (`gemini-3.5-flash`/`live-2.5-native-audio`/`embedding-2`) + garde-fou anti-littéral. ✅ Révisions d'embeddings résolues depuis le registre central (`EMBEDDING_VERSIONS`, manifest abandonné).
  - ⏳ **Reste (Phase 2b)** : registre d'**IDs logiques locaux** (`llama3`, `Qwen2.5-1.5B` vs `Qwen3.5-4B`, `DRAFT_MODEL_ID`, `VibeThinker-3B`, `FLUX`) + fusion résiduelle [pipeline/models_registry.py](backend/pipeline/models_registry.py).

## 🟢 Faibles

- [ ] **Backend — duplication entre adapters d'inférence** _(revue archi 2026-06-22 ; en partie fait)_
  - ✅ `health_check` *reachability* des adapters API (`brain_api` HTTP-ping, `google_genai` client-init, `unified`/ollama) factorisé dans [ReachabilityHealthCheckMixin](backend/adapters/inference/reachability_health_mixin.py) (builder de statut standardisé + sonde HTTP générique pilotée par un `requester` injecté → chaque adapter garde son client HTTP et ses cibles de patch).
  - ✅ `health_check` *readiness* factorisé dans [LazyLocalModelAdapter](backend/adapters/inference/lazy_local_model_adapter.py) (tous les adapters à modèle local migrés) ; motif `_load_model()` multi-sous-modèles factorisé dans [LazyLoadMixin](backend/adapters/inference/lazy_load_mixin.py) (`ImageGenMixin`/`AudioMixin`).
  - ⏳ **Reste (résiduel, hors scope)** : `RerankMixin` et `LocalTextAdapter.get_text_embedding` (chargements inline aux sémantiques d'erreur différentes) ; `LocalGuardrailAdapter` (aucun modèle).
- [x] **Backend — validation des env vars d'inférence** _(revue archi 2026-06-22 ; fait)_
  - ✅ `BrainAPIAdapter` échoue tôt (`raise ConfigurationError` si `BRAIN_API_URL` manquant) ([brain_api_adapter.py](backend/adapters/inference/brain_api_adapter.py)).
  - ✅ Garde-fou de cohérence (coherence-only) pour `unified` (`LLM_API_BASE` malformé) et `google_genai` (`GEMINI_API_KEY` blanc) dans leurs `__init__`, + validation groupée à erreurs agrégées au démarrage du container via `validate_inference_config()` ([inference_config.py](backend/core/utils/inference_config.py), câblée dans [inference.py](backend/api/animetix/containers/inference.py)).
  - ✅ `BrainAPIAdapter` routé sur `check_brain_config` ([brain_api_adapter.py](backend/adapters/inference/brain_api_adapter.py)) : message unifié (`"BRAIN_API_URL is not configured"`) + check d'URL malformée côté adapter. En-tête d'erreur agrégée passé tout en anglais (`"Invalid inference configuration:"`) et filtre `is not None` dans `validate_inference_config()`.
- [x] **Backend — adapters synchrones (pas de parallélisation des streams)** _(revue archi 2026-06-22 ; fait)_
  - ✅ `astream_generate` natif (I/O non bloquante) pour `UnifiedInferenceAdapter` (httpx.AsyncClient/SSE), `GoogleGenAIAdapter` (`client.aio`) et orchestration async dans `FallbackInferenceAdapter` ; les modèles locaux restent sur le pont thread par défaut de `InferencePort`. Plusieurs streams peuvent désormais être parallélisés via `asyncio.gather` sans bloquer la boucle. (Caveat documenté : le cache de diagnostics `_last_completion` de `UnifiedInferenceAdapter` est best-effort sous streams concurrents sur le Singleton.)
- [ ] **Backend — exposer le streaming async aux endpoints HTTP** _(suite du streaming async natif)_
  - ✅ Chemin service async réutilisable : `LLMService.aask_oracle_stream` + `AniminatorDomainService.aask_oracle_stream` consomment `engine.astream_generate` (Neo4j off-loop via `asyncio.to_thread`). ✅ Bug latent corrigé : `AniminatorStreamView` lit `token.text` (les chunks sont des `InferenceResponse`) — l'endpoint SSE Oracle re-fonctionne.
  - ✅ `AniminatorStreamView` réécrite en vue Django async native (hors DRF) consommant `aask_oracle_stream` : libère le thread worker pendant le stream (meilleure tenue sous streams concurrents). Rate-limit via `is_ratelimited()` + `sync_to_async` ; session/ORM via `sync_to_async`.
  - ✅ `EmojiStreamView` & `ParadoxStreamView` réécrites en vues Django async natives via un helper SSE partagé `api/sse.py` (`check_rate_limit` + `sse_stream_response`) ; `AniminatorStreamView` refactorée pour réutiliser `check_rate_limit`. Chemins service async : `LLMService.astream_generate`, `EmojiDomainService.agenerate_emojis_stream`, `ParadoxDomainService.agenerate_logic_stream`.
  - ⏳ **Reste** : ToT (sous-projet 2 — `inference_engine.generate` synchrone par nœud ; foyer du `gather`) et AgenticRAG (sous-projet 3 — migration async de la state-machine RAG complète). (Aparté : harmoniser `Cache-Control: no-cache` sur toutes les vues SSE.)
  - ✅ Bug `.text` éradiqué dans tous les consommateurs de streaming : `emoji_service`, `paradox_service`, `fallback_rag_processor`, `synthesize_processor` lisent désormais `token.text` (+ annotation de `synthesize_stream` corrigée). Tests de régression feeding `InferenceResponse` ajoutés.
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0` (dernière release publiée). Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. **Condition de déblocage** : la levée du cap (`jsonpickle>=3.0.4,<5.0.0`) n'existe que sur la branche `master` d'apache-beam ([PR #38769](https://github.com/apache/beam/pull/38769) ; prévue ~2.75.0, **non confirmée**). À ce moment-là : montée d'`apache-beam` dans [requirements.in](requirements.in) + re-`pip-compile` **complet** (beam co-épingle protobuf/grpcio/pyarrow/numpy/dill — pas d'épinglage chirurgical) + bump **lockstep** du tag de base [Dockerfile.dataflow:10](deploy/Dockerfile.dataflow#L10) (`apache/beam_python3.12_sdk:2.74.0`, sinon mismatch SDK worker ↔ pin = échec de soumission Dataflow). _Caveat_ : aucune release `jsonpickle` 4.x n'est à ce jour marquée comme corrigeant les CVE (CVE-2020-22083, CVE-2025-55136 : « Patched: None », disputées par le mainteneur) — la montée **défige** la version sans forcément clore formellement le finding. (Recherche multi-agents 2026-06-25.)
