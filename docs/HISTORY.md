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




## État de l'API d'Inférence (InferencePort)
Les capacités suivantes ont été stabilisées et intégrées via le système d'adaptateurs :
- **Optimisation Fallback :** Implémentation d'un ordonnancement dynamique basé sur la latence (EMA) et les taux d'erreur, garantissant que les moteurs les plus performants sont sollicités en priorité.
- **Robustesse :** Élimination des erreurs silencieuses dans les adaptateurs `Fallback` et `Qwen3VL`.
- **Compatibilité ASGI :** Refactorisation des middlewares pour un support asynchrone complet et isolation via `contextvars`.
- **Texte :** Génération simple, structurée et streaming via BrainAPI et Ollama. Support du Reranking (CrossEncoder).
- **Vision :** Génération d'images/sprites (Diffusers), description d'images (Moondream2), classification et embeddings multimédaux (CLIP). Détection d'objets (OWL-ViT), estimation de profondeur (DepthAnything), transformation Image-to-Anime (Img2Img) et génération de scènes 3D (Point Cloud). Support des interactions multimodales tardives via ColPali.
- **Vidéo :** Embeddings temporels, localisation d'actions et descriptions via Qwen2-VL. Support initial du Video-to-Anime (séquentiel).
- **Manga :** OCR de pages (TrOCR/MangaOCR) et inpainting de bulles de texte.

