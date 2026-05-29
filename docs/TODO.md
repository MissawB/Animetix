# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées.

## 🛠️ Dette Technique & Architecture

- [x] **Intégration Réelle de la Recherche Web (DuckDuckGo)** : Remplacer l'adaptateur simulé `DuckDuckGoSearchAdapter` dans `backend/adapters/persistence/web_search_adapter.py` par une véritable recherche DuckDuckGo (API libre ou HTML parser résilient).
- [ ] **Gestion des erreurs (Adapteurs d'Inférence - pass silencieux)** : Éliminer les blocs `except: pass` silencieux et ajouter du logging structuré :
  - Dans `backend/adapters/inference/fallback_adapter.py`
  - Dans `backend/adapters/inference/qwen3_vl_adapter.py`
- [x] **Middleware (ASGI)** : Refactoriser ou adapter `UserTrackingMiddleware` et `UserTierMiddleware` dans `backend/api/animetix/middleware.py` pour garantir l'isolation totale via `contextvars` sur les connexions asynchrones (Django Channels / WebSockets).
- [ ] **Rigueur des Agents (Critic & Judge)** : Éliminer les comportements trop permissifs par défaut (ex: `relevance_score=1.0` sur Exception dans `critic.py`).
- [ ] **Gestion des erreurs (Graph & Debate)** : Éliminer les erreurs silencieuses et structurer les logs dans le Graph Expert et le Debate Manager.

## 🧬 Fonctionnalités Créatives SOTA 2026

- [ ] **Génération Structurée** : Passer du parsing JSON simple à une validation de schéma native plus robuste (via Instructor/Ollama).
- [ ] **Modération de contenu sémantique** : Étendre l'implémentation par mots-clés actuelle vers une approche sémantique (Llama Guard).
- [ ] **Diagnostics & Incertitude** : Implémenter `get_diagnostics` et `calculate_uncertainty` dans `InferencePort`.
- [ ] **Traduction Manga (SDXL Neuronal)** : Améliorer le pipeline manga pour charger et exploiter SDXL-Turbo dans `DiffusersAdapter` (en plus du fallback Pillow déjà mis en place).
- [ ] **Transfert de style vidéo** : Implémenter FateZero / Video-to-Anime pour la cohérence visuelle.
- [ ] **Génération sonore** : Implémenter AudioLDM pour la création de paysages sonores basés sur des vidéos.
- [ ] **Clonage Vocal & S2S** : Implémenter Zero-shot RVC et les interactions speech-to-speech natives.

## ✅ Tâches Récemment Complétées

- [x] **Maintenance des Tests (Imports)** : Résolution des incohérences d'importation (`adapters...` vs `backend.adapters...`) et fiabilisation du `pythonpath` dans `pytest.ini` sous Windows.
- [x] **Inférence (Simplification)** : Éradication de vLLM, GGUF et Transformers brut pour l'inférence texte. Standardisation sur BrainAPI (Cloud) et Ollama (Local).
- [x] **Injection DI Manga & Inpainting Résilient (Chantier D)** : Câblage de `FallbackInferenceAdapter` dans `MangaFlowService` et implémentation du fallback local Pillow en cas d'absence de GPU.
- [x] **Stabilisation des Mocks** : Correction des cibles de mock `src.adapters...` dans `test_manga_ocr_adapter.py` et `test_fallback_structured.py`.
