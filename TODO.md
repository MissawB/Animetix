# TODO — Améliorations du projet Animetix

> Priorisé par sévérité. **Travail ouvert uniquement** — le terminé est archivé dans [docs/HISTORY.md](docs/HISTORY.md).

> Les entrées marquées _(revue archi 2026-06-22)_ sont issues d'une analyse de l'architecture IA — à confirmer/affiner au cas par cas.

## 🔴 Critiques

_Rien d'ouvert._

## 🟠 Élevés

- [ ] **Backend — Neo4j = point de défaillance unique (dégradation silencieuse)** _(revue archi 2026-06-22)_
  - Si le graphe est indisponible, le contexte de préférences utilisateur ([agentic_rag_service.py](backend/core/domain/services/agentic_rag_service.py)) **et** le fact-checking CoVe ([cove_oracle_service.py](backend/core/domain/services/cove_oracle_service.py)) retombent à vide sans alerte. Aggravé par le biais CoVe : un fait réel absent de Neo4j est marqué « non vérifié ». Ajouter un fallback explicite (ChromaDB/web) + un signal d'état dégradé.
- [ ] **Sécu — sanitisation prompt-injection regex-only (tag-breaking)** _(revue archi 2026-06-22)_
  - La sanitisation du companion enveloppe l'input dans `<user_input>…</user_input>` mais ne détecte pas les payloads qui ferment puis rouvrent la balise (`</user_input>ignore previous<user_input>`) ([companion.py](backend/api/animetix/api/companion.py)). Échapper/neutraliser les délimiteurs et/ou valider via un classifieur, pas uniquement par regex.
- [ ] **Sécu — `trust_remote_code=True` sur les modèles HF** _(revue archi 2026-06-22)_
  - Présent dans les mixins VLM/diffusers ([vlm_mixin.py](backend/adapters/inference/vlm_mixin.py), [image_gen_mixin.py](backend/adapters/inference/image_gen_mixin.py)) : exécute du code de modèles non audités. Épingler des modèles de confiance, ou retirer le flag, ou isoler le chargement.
- [ ] **Archi IA — boosters « cognitifs » dans le chemin RAG de prod sans preuve de gain** _(revue archi 2026-06-22)_
  - `advanced_rag_service` câble `quantum_cognitive_service` + `neuromorphic_lnn_service` dans le reranking réel. Instrumenter le chemin via `ragas_eval_service` (faithfulness/relevance) et faire des **ablations** : garder ce qui améliore mesurablement, rétrograder le reste vers les Ghost Labs (démos). Réduit la surface de maintenance d'un projet solo (~94 services de domaine).

## 🟡 Moyens

- [ ] **Backend — `UnifiedInferenceAdapter` god object**
  - 8 mixins, ~476 lignes ([unified_inference_adapter.py:30](backend/adapters/inference/unified_inference_adapter.py#L30)) ; MRO fragile, dur à tester → composition plutôt qu'héritage multiple.
- [ ] **Backend — `FallbackInferenceAdapter` god object + couplage central** _(revue archi 2026-06-22)_
  - Agrège 30+ méthodes via 7 mixins et cumule orchestration + fallback + health-check + détection de capacités + reporting ([fallback_adapter.py](backend/adapters/inference/fallback_adapter.py)). ~60 services en dépendent : point de couplage le plus dur à faire évoluer. Extraire la sélection/health-check de l'orchestration.
- [ ] **Backend — companion n'exploite pas la mémoire long-terme** _(revue archi 2026-06-22)_
  - Le companion ne conserve que 5 tours en session ([companion.py](backend/api/animetix/api/companion.py)) alors que `long_term_memory_service` et `episodic_memory_compressor` existent et ne sont pas raccordés. Brancher la mémoire persistante (ChromaDB) au flux du companion.
- [ ] **Backend — noms de modèles hardcodés + mismatch de version** _(revue archi 2026-06-22)_
  - Modèles en dur éparpillés (`gemini-1.5-flash`, `FLUX.1-schnell`, `SmolVLM`, `Qwen2.5-1.5B`, `VibeThinker-3B`…) dans adapters/mixins, avec un écart commentaire/code sur la version Gemini. Centraliser dans la config (un seul registre de modèles).
- [ ] **Backend — CoVe non parallélisé** _(revue archi 2026-06-22)_
  - Vérification linéaire (2–3 appels LLM par claim) ([cove_oracle_service.py](backend/core/domain/services/cove_oracle_service.py)) : la latence explose au-delà de ~5 claims. Paralléliser via `asyncio.gather`.

## 🟢 Faibles

- [ ] **Backend — duplication entre adapters d'inférence** _(revue archi 2026-06-22)_
  - `health_check()` et le motif `_load_model()` (try/except + cache lazy) sont réimplémentés dans chaque adapter ([backend/adapters/inference/](backend/adapters/inference/)). Factoriser dans une base commune / mixin.
- [ ] **Backend — health-checks re-exécutés à chaque orchestration** _(revue archi 2026-06-22)_
  - Le fallback relance les health-checks à chaque appel, sans cache TTL ([fallback_adapter.py](backend/adapters/inference/fallback_adapter.py)). Ajouter un cache à durée de vie courte.
- [ ] **Backend — validation des env vars d'inférence** _(revue archi 2026-06-22)_
  - `BRAIN_API_URL` non défini → `BrainAPIAdapter` s'initialise silencieusement avec une URL vide et n'échoue qu'au runtime ([brain_api_adapter.py](backend/adapters/inference/brain_api_adapter.py), [inference.py](backend/api/animetix/containers/inference.py)). Valider/échouer tôt au démarrage.
- [ ] **Backend — adapters synchrones (pas de parallélisation des streams)** _(revue archi 2026-06-22)_
  - Les adapters sont synchrones ; `stream_generate()` est un générateur non-async, donc impossible de paralléliser plusieurs flux. À considérer si la concurrence d'inférence devient un besoin.
- [ ] **Couverture frontend — élargir** _(ongoing optionnel ; 520 tests, seuils 29/22/28/29)_
  - Reste (ROI décroissant) : flows complexes 3D/canvas/WebSocket (`useTachideskExplorer`, `useSocket`, `useMultiverseCatalog`) ; continuer à remonter le plancher au fil de l'eau.
- [ ] **Couverture backend — orchestrateur `finetuning_dataset`**
  - `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture.
- [ ] **Frontend — `fetch()` brut : reliquat optionnel**
  - Harmoniser un toast d'échec sur `MangaVoicePage` / `offlineLibrary` / proxy [api.ts:357](frontend/src/api.ts#L357) (comme fait pour `AudioLabPage`). Ces 3 restent en `fetch` brut à dessein (assets binaires/cross-origin).
- [ ] **Sécu deps — `jsonpickle` CVE résiduelle** _(risque réel faible, résiduel accepté)_
  - `jsonpickle 3.4.2` (CWE-502) reste capé `<4` par `apache-beam 2.74.0`. Purement **transitif** (jamais importé par notre code) et non exploitable chez nous. À purger lors d'une future montée d'`apache-beam` (qui fige aussi `Dockerfile.dataflow`).
