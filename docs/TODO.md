# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

- [ ] **Diagnostics & Incertitude Avancés** : Migrer les calculs d'incertitude (entropie, perplexité) basés sur le texte vers une exploitation réelle des `logprobs` si exposés par les adaptateurs (BrainAPI/Ollama).
- [ ] **Nettoyage des Bouchons (UnifiedInferenceAdapter)** : Finaliser le remplacement de toutes les méthodes levant encore `InferenceNotImplementedError` par de véritables délégations vers les mixins de vision ou d'audio.
- [ ] **Modération de contenu (Guardrails)** : Étendre la modération sémantique native à tous les adaptateurs de texte pour garantir une sécurité homogène sur tout le cluster.
## 🚀 Intégrations & Pages Manquantes (Frontend)

Les fonctionnalités suivantes sont implémentées (ou partiellement implémentées) dans les modèles backend (`models.py`) mais ne disposent actuellement d'aucune route ni page dédiée dans l'application React :

- [ ] **Détails des Événements de Clubs** : Créer une vue détaillée pour un événement de club spécifique (ex: `/clubs/:id/events/:eventId`) affichant le modèle `ClubEvent` (description, participants, etc.).
- [ ] **Gestion des Amis / Hub Social Personnel** : Ajouter une interface dédiée à la consultation de ses abonnés/abonnements (modèle `Friendship`) et à la gestion des requêtes d'amis.
- [ ] **Historique des Feedbacks IA (Utilisateur)** : Fournir à l'utilisateur un historique de ses propres requêtes et feedbacks (modèle `AIFeedback`), potentiellement dans son tableau de bord personnel.

## 🛡️ Sécurité & Résilience

- [ ] **Audit de Dépendances Continu** : Automatiser le scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
