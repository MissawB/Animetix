# Animetix - Historique des Refactorisations et Succès

Ce document archive les étapes majeures de l'évolution technique du projet.

## 2026 - Restructuration Majeure
- **Fullstack Monorepo Restructuring :** Réorganisation radicale en `frontend/` (React SPA) et `backend/` (Python). Migration de Django vers `backend/api/`.
- **Pure SPA Transition :** Suppression totale de la couche de templates Django. Transition vers une API Headless.
- **Prompt Externalization :** Suppression des prompts codés en dur. Gestion centralisée via `PromptManager` et YAML.
- **State Decoupling :** Migration de la logique de jeu (`Akinetix`, `Paradox`, `CreativeFusion`) des vues Django vers des **Domain Services** purs.
- **Purge du Legacy :** Suppression des contrôleurs de vue HTML, configurations d'URL obsolètes et tests associés.
- **Manga Translation & DI Realignment :** Réalignement de l'injection du conteneur de dépendances (DI) dans `MangaFlowService` et développement d'un fallback algorithmique Pillow-only résilient en local 100% hors-ligne si SDXL-Turbo n'est pas opérationnel (GPU absent).
- **Consolidation Graphes & Bus d'Agents :** Élimination des erreurs silencieuses dans le `MultiAgentBus` et les scripts d'entraînement (`train_vibe_characters.py`, `train_akinetix_rl.py`). Renforcement de la clarté des logs pour l'Expert Graphe.
- **Agent Rigor & Defensive RAG :** Durcissement des agents `ResponseCritic`, `ResponseJudge` et `DebateManager`. Mise en place d'un mode "Fail-Safe" (scores à 0.0, action REWRITE forcée) en cas de crash infrastructure ou d'erreurs d'inférence, garantissant l'intégrité des réponses RAG.
- **Test Suite Imports & Infrastructure Purge :** Standardisation globale des namespaces d'importation (sans préfixe `backend.` pour matcher la source) et éradication complète des adaptateurs/tests liés à GGUF et vLLM. Restauration de la collection globale de tests (435 items) via un nettoyage du `pythonpath` dans `pytest.ini`.
- **Web Search Real Integration :** Remplacement de la recherche DuckDuckGo simulée par une intégration réelle via la bibliothèque `ddgs` (DuckDuckGo Search), fournissant une information temps réel fiable pour l'Agentic RAG avec gestion d'erreurs robuste.


- **ASGI Middleware & ContextVars Namespace Resolution :** Restructuration des middlewares `UserTrackingMiddleware` et `UserTierMiddleware` pour les rendre pleinement compatibles synchrone/asynchrone (ASGI/WSGI) avec une synchronisation automatique des `ContextVar` en cas d'imports multiples, éliminant les fuites et assurant une isolation totale dans les requêtes asynchrones et WebSockets.
- **Inference Adapter Silent Exception Cleanup :** Éradication totale des blocs d'exceptions silencieux (`except: pass` ou fallbacks non loggés) dans `FallbackInferenceAdapter` et `Qwen3VLAdapter`. Introduction de `logger.debug` structurés capturant les détails des exceptions (ex. non-implémentation, échec d'indexation d'URL d'image) avant exécution des replis logiques, garantissant une observabilité parfaite sans altérer les flux de test.
- **Pipeline Silent Exception & Observer Ingestion Cleanup :** Élimination complète de tous les blocs `except:` anonymes et silencieux dans 5 pipelines critiques (`vectorize_anime.py`, `ingest_vg_characters.py`, `eval_ragas.py`, `regression_benchmark.py`, `models_registry.py`), remplacés par des structures `except Exception as e:` explicites et du logging structuré (`logger.error`, `logger.warning`, `logger.debug`).
- **Universal Test Mock Injection Mapper (AliasLoader) :** Implémentation d'un redirecteur d'imports (`SrcPipelineMapper`) extrêmement robuste au niveau de `tests/conftest.py` exploitant un chargeur d'alias (`AliasLoader`) dynamique via `sys.meta_path`. Ce mécanisme intercepte en toute transparence les cibles de patch sous `src.pipeline` et les redirige vers les instances uniques de modules sous `pipeline`, garantissant la cohérence mémoire et résolvant l'ensemble des conflits de mocks sans modification des fichiers de tests d'origine.
- **CUDA Dynamic GPU Check & CPU Memory Guard :** Implémentation d'une détection proactive et dynamique des GPU CUDA (`torch.cuda.is_available()`) dans `DiffusersAdapter` et `AudioTransformersAdapter` empêchant tout chargement de modèles neuronaux lourds (SDXL, XTTS, Moshi, AudioLDM) sur CPU, évitant ainsi les ralentissements excessifs et les crashs par épuisement de mémoire (OOM). Les exceptions `InferenceError` levées sont automatiquement interceptées par l'orchestrateur global `FallbackInferenceAdapter` pour basculer sur le cloud distant (`BrainAPIAdapter`) de manière transparente, tandis que l'inpainting de bulles de texte manga bascule localement et sans interruption sur le moteur Pillow-only CPU-safe.




## État de l'API d'Inférence (InferencePort)
Les capacités suivantes ont été stabilisées et intégrées via le système d'adaptateurs :
- **Consistance Vidéo (FateZero) :** Implémentation du `CrossFrameAttentionProcessor` dans `DiffusersAdapter` permettant une transformation Video-to-Anime avec consistance temporelle Zero-Shot (sans ré-entraînement) via traitement par lots et attention croisée sur frame d'ancrage.
- **Soundscape AudioLDM :** Activation complète du pipeline de génération d'ambiances sonores basées sur le contexte visuel (via `SoundscapeGenerationService`). L'injection de dépendances a été corrigée dans l'API (`labs.py`) pour exposer cette fonctionnalité SOTA 2026.
- **Clonage Vocal & S2S Natif :** Activation de `VoiceCloningService` (basé sur XTTS v2 pour du Zero-Shot RVC) et de `NativeSpeechLLMService` (basé sur Kyutai Moshi pour du Speech-to-Speech temps réel sans latence TTS intermédiaire). Tous les tests unitaires et les configurations d'injection associés ont été stabilisés.
- **Optimisation Fallback :** Implémentation d'un ordonnancement dynamique basé sur la latence (EMA) et les taux d'erreur, garantissant que les moteurs les plus performants sont sollicités en priorité.
- **Robustesse :** Élimination des erreurs silencieuses dans les adaptateurs `Fallback` et `Qwen3VL`.
- **Compatibilité ASGI :** Refactorisation des middlewares pour un support asynchrone complet et isolation via `contextvars`.
- **Texte :** Génération simple, structurée et streaming via BrainAPI et Ollama. Support du Reranking (CrossEncoder).
- **Vision :** Génération d'images/sprites (Diffusers), description d'images (Moondream2), classification et embeddings multimédaux (CLIP). Détection d'objets (OWL-ViT), estimation de profondeur (DepthAnything), transformation Image-to-Anime (Img2Img) et génération de scènes 3D (Point Cloud). Support des interactions multimodales tardives via ColPali.
- **Vidéo :** Embeddings temporels, localisation d'actions et descriptions via Qwen2-VL. Support initial du Video-to-Anime (séquentiel).
- **Manga :** OCR de pages (TrOCR/MangaOCR) et inpainting de bulles de texte.

