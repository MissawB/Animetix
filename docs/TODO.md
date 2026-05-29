# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md` et dans la section des succès.

## 🛠️ Dette Technique & Architecture

*(Toutes les tâches de dette technique identifiées lors de l'audit de mai 2026 ont été entièrement résolues et archivées.)*

## 🧬 Fonctionnalités Créatives SOTA 2026

- [ ] **Génération Structurée** : Passer du parsing JSON simple à une validation de schéma native plus robuste (via Instructor/Ollama).
- [ ] **Modération de contenu sémantique** : Étendre l'implémentation par mots-clés actuelle vers une approche sémantique (Llama Guard).
- [ ] **Diagnostics & Incertitude** : Implémenter `get_diagnostics` et `calculate_uncertainty` dans `InferencePort`.

## ✅ Tâches Récemment Complétées (Archivées)

- [x] **Optimisation sémantique (Swarm Consensus)** : Interconnexion de `SwarmConsensusOrchestrator` avec un LLM (`InferencePort`) pour un vote sémantique unifié via Pydantic en un seul appel API, avec repli résilient sur les mots-clés locaux.
- [x] **Dégradation élégante (Inférence de Modèles Lourds)** : Détection dynamique de CUDA GPU dans `DiffusersAdapter` et `AudioTransformersAdapter` pour bloquer les chargements lourds sur CPU et basculer sur le cloud distant (`BrainAPIAdapter`) de manière transparente.
- [x] **Gestion des erreurs (Pipelines d'Ingestion - pass silencieux)** : Élimination complète de tous les blocs `except:` anonymes et silencieux dans 5 pipelines (`vectorize_anime.py`, `ingest_vg_characters.py`, `eval_ragas.py`, `regression_benchmark.py`, `models_registry.py`), remplacés par des logs nommés explicites.
- [x] **Intégration Réelle de la Recherche Web (DuckDuckGo)** : Connexion de l'Agentic RAG à DuckDuckGo Search réel via la bibliothèque `ddgs`.
- [x] **Gestion des erreurs (Adapteurs d'Inférence - pass silencieux)** : Nettoyage des exceptions silencieuses dans `FallbackInferenceAdapter` et `Qwen3VLAdapter`.
- [x] **Middleware (ASGI)** : Restructuration synchrone/asynchrone asynchrone des middlewares Django et isolation via `ContextVar`.
- [x] **Rigueur des Agents (Critic & Judge)** : Durcissement des prompts et mode "Fail-Safe" défensif pour le RAG en cas de crash infrastructure.
- [x] **Gestion des erreurs (Graph & Debate)** : Clarification des logs dans le MultiAgentBus, le Debate Manager et les pipelines d'entraînement de sentiments de personnages.
- [x] **Transfert de style vidéo (FateZero)** : Implémentation du `CrossFrameAttentionProcessor` pour la cohérence temporelle video-to-anime.
- [x] **Génération sonore (AudioLDM)** : Implémentation de la génération de paysages sonores basée sur des métadonnées vidéo.
- [x] **Clonage Vocal & S2S (XTTS v2 / Moshi)** : Support du clonage voix zéro-shot et speech-to-speech natif Kyutai Moshi.
- [x] **Maintenance des Tests (Imports)** : Résolution globale du `pythonpath` pytest et des conflits d'importations sous Windows.
- [x] **Inférence (Simplification)** : Standardisation sur BrainAPI and Ollama, suppression complète de vLLM et GGUF locaux.
- [x] **Injection DI Manga & Inpainting Résilient** : Câblage DI et fallback local Pillow en cas d'absence de GPU.
- [x] **Stabilisation des Mocks** : Stabilisation des namespaces mocks `src.adapters` en les associant via meta-path finder dans `conftest.py`.
