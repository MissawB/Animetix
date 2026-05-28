# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées ont été purgées.

## Dette Technique & Architecture
- [ ] **Gestion des erreurs (Agents)** : Éliminer les blocs `except: pass` silencieux et structurer les logs dans les agents Critic et Judge.
- [ ] **Gestion des erreurs (Graph & Debate)** : Éliminer les erreurs silencieuses et structurer les logs dans le Graph Expert et le Debate Manager.
- [ ] **Adaptateurs** : Corriger et optimiser les priorités de fallback dans la sélection des adaptateurs (`FallbackInferenceAdapter`).
- [ ] **Refactoring** : Déconstruire `TransformersAdapter` (s'il reste des composants monolithiques) pour suivre le modèle de mixins déjà mis en place.

## Cybersécurité
- [ ] **Confidentialité & Fuites mémoire (ASGI)** : Refactoriser `UserTrackingMiddleware` et `UserTierMiddleware` pour utiliser `contextvars` au lieu de `threading.local()`, afin de prévenir les fuites de données inter-requêtes en environnement asynchrone.

## Fonctionnalités Créatives SOTA 2026
- [ ] **Transfert de style vidéo** : Implémenter FateZero / Video-to-Anime pour la cohérence visuelle.
- [ ] **Génération sonore** : Implémenter AudioLDM pour la création de paysages sonores basés sur des vidéos.
- [ ] **Clonage Vocal & S2S** : Implémenter Zero-shot RVC et les interactions natives Speech-to-Speech.
- [ ] **Recherche** : Implémenter le "Advanced Reranking" (potentiellement via ColBERTv2 comme spécifié dans la ROADMAP).

## Tests & MLOps
- [ ] **Tests automatisés** : Mettre à jour et étendre la suite de tests (`pytest`) pour couvrir les récents changements (Architecture hexagonale, SPA, containers DI modulaires).
