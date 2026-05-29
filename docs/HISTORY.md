# Animetix - Historique des Refactorisations et Succès

Ce document archive les étapes majeures de l'évolution technique du projet.

## 2026 - Restructuration Majeure
- **Fullstack Monorepo Restructuring :** Réorganisation radicale en `frontend/` (React SPA) et `backend/` (Python). Migration de Django vers `backend/api/`.
- **Pure SPA Transition :** Suppression totale de la couche de templates Django. Transition vers une API Headless.
- **Prompt Externalization :** Suppression des prompts codés en dur. Gestion centralisée via `PromptManager` et YAML.
- **State Decoupling :** Migration de la logique de jeu (`Akinetix`, `Paradox`, `CreativeFusion`) des vues Django vers des **Domain Services** purs.
- **Purge du Legacy :** Suppression des contrôleurs de vue HTML, configurations d'URL obsolètes et tests associés.
- **Manga Translation & DI Realignment :** Réalignement de l'injection du conteneur de dépendances (DI) dans `MangaFlowService` et développement d'un fallback algorithmique Pillow-only résilient en local 100% hors-ligne si SDXL-Turbo n'est pas opérationnel (GPU absent).
- **Test Suite Imports & Windows Stabilization :** Standardisation des namespaces d'importation sans le préfixe `backend.` dans les tests et correction de la configuration de `pytest.ini` pour utiliser un `pythonpath` multiligne multiplateforme robuste sous Windows, éliminant toutes les pannes de collecte.
- **Web Search Real Integration :** Remplacement de la recherche DuckDuckGo simulée par une intégration réelle via la bibliothèque `ddgs` (DuckDuckGo Search), fournissant une information temps réel fiable pour l'Agentic RAG avec gestion d'erreurs robuste.


## État de l'API d'Inférence (InferencePort)
Les capacités suivantes ont été stabilisées et intégrées via le système d'adaptateurs :
- **Optimisation Fallback :** Implémentation d'un ordonnancement dynamique basé sur la latence (EMA) et les taux d'erreur, garantissant que les moteurs les plus performants sont sollicités en priorité.
- **Robustesse :** Élimination des erreurs silencieuses dans les adaptateurs `Fallback` et `Qwen3VL`.
- **Compatibilité ASGI :** Refactorisation des middlewares pour un support asynchrone complet et isolation via `contextvars`.
- **Texte :** Génération simple, structurée et streaming via BrainAPI et Ollama. Support du Reranking (CrossEncoder).
- **Vision :** Génération d'images/sprites (Diffusers), description d'images (Moondream2), classification et embeddings multimédaux (CLIP). Détection d'objets (OWL-ViT), estimation de profondeur (DepthAnything), transformation Image-to-Anime (Img2Img) et génération de scènes 3D (Point Cloud). Support des interactions multimodales tardives via ColPali.
- **Vidéo :** Embeddings temporels, localisation d'actions et descriptions via Qwen2-VL. Support initial du Video-to-Anime (séquentiel).
- **Manga :** OCR de pages (TrOCR/MangaOCR) et inpainting de bulles de texte.

