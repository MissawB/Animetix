# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées ont été purgées.

## Dette Technique & Architecture
- [ ] **Gestion des erreurs (Adapteurs d'Inférence)** : Éliminer les blocs `except: pass` silencieux dans `unified_inference_adapter.py`, `brain_api_adapter.py`, `fallback_adapter.py` et `qwen3_vl_adapter.py`. Ajouter du logging structuré.
- [ ] **Gestion des erreurs (Agents)** : Éliminer les blocs `except: pass` silencieux et structurer les logs dans les agents Critic et Judge.
- [ ] **Gestion des erreurs (Graph & Debate)** : Éliminer les erreurs silencieuses et structurer les logs dans le Graph Expert et le Debate Manager.
- [ ] **Adaptateurs** : Corriger et optimiser les priorités de fallback dans la sélection des adaptateurs (`FallbackInferenceAdapter`) basées sur la latence et les types d'erreurs.
- [ ] **Refactoring** : Déconstruire `TransformersAdapter` (s'il reste des composants monolithiques) pour suivre le modèle de mixins déjà mis en place.
- [ ] **Middleware (ASGI)** : Finaliser la refactorisation de `UserTrackingMiddleware` et `UserTierMiddleware` dans `backend/api/animetix/middleware.py` pour garantir l'isolation totale via `contextvars`.

## Fonctionnalités Créatives SOTA 2026
- [ ] **Génération Structurée (GGUF)** : Passer du parsing JSON simple à une validation de schéma native plus robuste.
- [ ] **Modération de contenu** : Étendre l'implémentation par mots-clés actuelle vers une approche sémantique (Llama Guard).
- [ ] **Diagnostics & Incertitude** : Implémenter `get_diagnostics` et `calculate_uncertainty` dans `InferencePort`.
- [ ] **Traduction Manga** : Implémenter `translate_manga_page` (orchestration OCR -> LLM Translation -> Inpainting).
- [ ] **Transfert de style vidéo** : Implémenter FateZero / Video-to-Anime pour la cohérence visuelle.
- [ ] **Génération sonore** : Implémenter AudioLDM pour la création de paysages sonores basés sur des vidéos.
- [ ] **Clonage Vocal & S2S** : Implémenter Zero-shot RVC et les interactions natives Speech-to-Speech.
- [ ] **Recherche** : Implémenter le "Advanced Reranking" (potentiellement via ColBERTv2 comme spécifié dans la ROADMAP).

## Tests & MLOps
- [ ] **Tests automatisés** : Mettre à jour et étendre la suite de tests (`pytest`) pour couvrir les récents changements (Architecture hexagonale, SPA, containers DI modulaires).
