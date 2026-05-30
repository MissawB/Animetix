# Animetix - Historique des Refactorisations et Succès

Ce document archive les étapes majeures de l'évolution technique du projet.

## [2026-05-30] Session : Audit & Renforcement Sécurité 2026
- **Audit de Sécurité Complet :** Identification et correction de 7 vulnérabilités majeures impactant les APIs publiques, l'infrastructure et la gestion des données.
- **Déploiement des Guardrails :** Intégration systématique du `GuardrailService` sur tous les endpoints API critiques (`Companion`, `Search`, `Games`). Protection proactive contre les injections de prompt et validation de sécurité des sorties IA.
- **Protection contre l'Inference Abuse :** Implémentation d'une authentification obligatoire et de quotas journaliers (`UsagePort`) sur toutes les fonctionnalités d'IA lourdes (CLIP, RL, Fusions). Journalisation granulaire de la consommation par utilisateur.
- **Sécurisation Anti-SSRF :** Centralisation de la validation d'URL via `is_safe_url` (résolution DNS + filtrage IP privées). Sécurisation du proxy d'images, de la recherche Web et des communications Backend-to-BrainAPI.
- **Durcissement Neo4j (Anti-Injection Cypher) :** Renforcement de `sanitize_cypher_identifier` avec validation par Regex et Whitelist stricte. Gestion sécurisée des types de relations dynamiques extraits par l'IA.
- **Cloisonnement de l'Observabilité :** Restriction de l'accès aux métriques Prometheus et à la documentation Swagger/OpenAPI aux seuls membres du staff technique (`staff_member_required`).
- **Conformité RGPD & PII :** Désactivation de la transmission automatique des informations personnelles identifiables (PII) vers Sentry pour garantir la confidentialité des données utilisateurs.
- **Maintenance Sécurité (Dépendances) :** Mise à jour critique de **Django** (de 5.2.13 à **5.2.14**) pour corriger les vulnérabilités CVE-2026-5766 et CVE-2026-6907 impactant le noyau de l'application.
- **Simulations Cognitives & RAG :** Interconnexion réussie du `SynapticPlasticitySimulator` et du `QuantumCognitivePreferenceModel` au pipeline de RAG. L'historique conceptuel influence désormais dynamiquement les scores de pertinence.
- **Génération 3D & Dioramas :** Intégration réelle de l'API Tripo3D et déploiement du viewer React pour la reconstruction de scènes 3D à partir d'images d'anime.
- **Vidéo-RAG (Embeddings Temporels) :** Finalisation de l'infrastructure Celery pour l'indexation par segments temporels via Qwen2-VL, permettant une recherche sémantique précise "à l'intérieur" des clips.
- **Lab & MLOps UX :** Déploiement du `LabHubPage` et intégration du dashboard de curation DPO et du tableau de bord de transparence (Drift/Graph Health).

## [2026-05-29] Session Intensive : Robustesse & Innovation SOTA
- **Vidéo-RAG (Intégration E2E) :** Finalisation complète de la boucle de recherche sémantique intra-vidéo. Les endpoints `/api/v1/labs/video/index/` et `/search/` sont désormais exposés. Le service `VideoRAGService` a été intégré au workflow principal `AgenticRAGService`, permettant à l'assistant de répondre à des questions visuelles complexes en fouillant dans les timelines indexées. Le frontend `VideoLabPage` a été enrichi d'une interface de recherche temporelle active.
- **Vidéo-RAG (Intégration Industrielle) :** Finalisation du câblage de l'infrastructure Video-RAG. Enregistrement du `VideoRAGService` dans le conteneur DI et correction des tâches Celery pour une orchestration distribuée fluide. Implémentation d'une segmentation vidéo robuste par ré-encodage de frames via `imageio`, éliminant la corruption des fichiers par découpage brut d'octets.
- **Vidéo-RAG (Recherche Intra-Clip) :** Activation de l'extraction d'embeddings temporels via Qwen2-VL (résumés narratifs) et CLIP (vecteurs denses). Implémentation du service `VideoRAGService` gérant le découpage, l'analyse et l'indexation dans une collection ChromaDB `video_temporal`. Correction d'un bug de collision d'ID et fiabilisation de la recherche sémantique segmentée.
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
