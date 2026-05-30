# Animetix - Historique des Refactorisations et Succès

Ce document archive les étapes majeures de l'évolution technique du projet.

## [2026-05-29] Session Intensive : Robustesse & Innovation SOTA
- **FateZero (Consistance Temporelle Vidéo) :** Implémentation du `CrossFrameAttentionProcessor` dans `DiffusersAdapter`. Transformation Video-to-Anime avec consistance temporelle Zero-Shot via traitement par lots et attention croisée sur frame d'ancrage.
- **AudioLDM & Soundscapes :** Activation du pipeline de génération d'ambiances sonores basées sur le contexte visuel. Correction des injections de services dans l'API Labs.
- **Clonage Vocal & S2S Natif :** Activation de `VoiceCloningService` (XTTS v2) et de `NativeSpeechLLMService` (Kyutai Moshi) pour des interactions vocales temps réel sans latence TTS.
- **Génération Structurée Native (Instructor) :** Migration des adaptateurs `BrainAPI` et `Unified` vers `instructor`. Validation native des schémas Pydantic avec fallback regex ultra-résilient.
- **Agent Rigor & Defensive RAG :** Durcissement des agents `ResponseCritic`, `ResponseJudge` et `DebateManager`. Mode "Fail-Safe" (pessimiste) systématique en cas d'erreur infrastructure ou d'inférence.
- **Consolidation Graphes & Bus d'Agents :** Élimination des erreurs silencieuses dans le `MultiAgentBus` et les scripts d'entraînement. Amélioration de l'observabilité système.
- **Inference Adapter Silent Exception Cleanup :** Éradication totale des blocs `except: pass` dans `FallbackInferenceAdapter` et `Qwen3VLAdapter`. Logging structuré et EMA de latence pour l'ordonnancement dynamique.
- **ASGI Middleware & Async Isolation :** Refactorisation des middlewares pour support asynchrone complet et isolation garantie via `ContextVars`.
- **Test Suite Restoration :** Standardisation globale des namespaces d'importation. Pytest collecte désormais l'intégralité de la suite (435 tests) sans erreur.

## 2026 - Restructuration Majeure
- **Fullstack Monorepo Restructuring :** Réorganisation radicale en `frontend/` (React SPA) et `backend/` (Python). Migration de Django vers `backend/api/`.
- **Pure SPA Transition :** Suppression totale de la couche de templates Django. Transition vers une API Headless.
- **Prompt Externalization :** Suppression des prompts codés en dur. Gestion centralisée via `PromptManager` et YAML.
- **State Decoupling :** Migration de la logique de jeu (`Akinetix`, `Paradox`, `CreativeFusion`) des vues Django vers des **Domain Services** purs.
- **Purge du Legacy :** Suppression des contrôleurs de vue HTML, configurations d'URL obsolètes et tests associés.
- **Manga Translation & DI Realignment :** Réalignement de l'injection du conteneur de dépendances (DI) dans `MangaFlowService` et développement d'un fallback algorithmique Pillow-only résilient en local 100% hors-ligne si SDXL-Turbo n'est pas opérationnel (GPU absent).
- **Web Search Real Integration :** Remplacement de la recherche DuckDuckGo simulée par une intégration réelle via la bibliothèque `ddgs` (DuckDuckGo Search), fournissant une information temps réel fiable pour l'Agentic RAG avec gestion d'erreurs robuste.

## État de l'API d'Inférence (InferencePort)
Les capacités suivantes ont été stabilisées et intégrées via le système d'adaptateurs :
- **Consistance Vidéo (FateZero)**
- **Génération Structurée Native (Instructor)**
- **Soundscape AudioLDM**
- **Clonage Vocal & S2S Natif**
- **Optimisation Fallback (EMA Latency)**
- **Robustesse & Observabilité**
- **Texte :** BrainAPI, Ollama, Reranking.
- **Vision :** Diffusers, Moondream2, CLIP, OWL-ViT, DepthAnything, Img2Img, Point Cloud, ColPali.
- **Vidéo :** Qwen2-VL, Video-to-Anime.
- **Manga :** OCR (TrOCR/MangaOCR), Inpainting.
