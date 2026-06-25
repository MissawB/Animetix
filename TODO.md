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
  - ⏳ **Reste** : factoriser le motif `_load_model()` (try/except + cache lazy) et le `health_check` *readiness* des adapters de modèles **locaux**.
- [x] **Backend — validation des env vars d'inférence** _(revue archi 2026-06-22 ; fait)_
  - ✅ `BrainAPIAdapter` échoue tôt (`raise ConfigurationError` si `BRAIN_API_URL` manquant) ([brain_api_adapter.py](backend/adapters/inference/brain_api_adapter.py)).
  - ✅ Garde-fou de cohérence (coherence-only) pour `unified` (`LLM_API_BASE` malformé) et `google_genai` (`GEMINI_API_KEY` blanc) dans leurs `__init__`, + validation groupée à erreurs agrégées au démarrage du container via `validate_inference_config()` ([inference_config.py](backend/core/utils/inference_config.py), câblée dans [inference.py](backend/api/animetix/containers/inference.py)).
- [ ] **Backend — adapters synchrones (pas de parallélisation des streams)** _(revue archi 2026-06-22)_
  - Les adapters sont synchrones ; `stream_generate()` est un générateur non-async, donc impossible de paralléliser plusieurs flux. À considérer si la concurrence d'inférence devient un besoin.
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. À purger lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).
