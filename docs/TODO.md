# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

*Aucune tâche pendante dans cette section.*

## 🚀 Intégrations & Pages Manquantes (Frontend)

- [ ] **Hub "Forge Créative"** : Centraliser l'accès aux laboratoires de médias (Manga Lab, Audio Lab, Spatial Lab, Video Lab, Visual Nexus) orphelins.
- [ ] **Hub "Cognition & Social"** : Regrouper l'Archetype Nexus, la Gestion Neuro-Memory et le Counterfactual Simulator dans une vue unifiée.
- [ ] **Exposition Publique des Outils Expert** : Créer des versions "Read-only" du SOTA Benchmarking et du Graph Debugger pour les utilisateurs avancés.

## 🧬 Innovations SOTA & Curation

- [ ] **Expliquabilité Avancée (XAI)** : Tableau de bord détaillant les scores de confiance, les poids sémantiques et les sources RAG pour chaque réponse de l'IA (Modularisation complète).
- [ ] **Dashboard "Mon Empreinte IA"** : Interface permettant à l'utilisateur de visualiser les règles logiques (Z3) et les vecteurs de préférence qui définissent son profil.
- [ ] **Modularisation du Singularity Lab** : Isoler les 5 modules (Quantum, Swarm, Plasticity, Compiler, Multiverse) dans des vues immersives distinctes pour améliorer l'UX.

## 🛡️ Sécurité & Résilience

- [x] **Suppression des Secrets par Défaut** (CRITIQUE) : Retirer les fallbacks en dur pour les clés API (ex: `dev-secret-key` dans `BrainAPIAdapter`) et lever une `ImproperlyConfigured` si absentes.
- [ ] **Isolation Réseau des Services** (HAUTE) : Supprimer l'exposition des ports PostgreSQL, Redis, Neo4j et ChromaDB sur l'hôte dans `docker-compose.yml` (utiliser uniquement le réseau interne Docker).
- [ ] **Durcissement SSRF Interne** (MOYENNE) : Restreindre `allow_internal=True` dans `safe_http_request` aux seuls noms de services Docker autorisés.
- [ ] **Audit Humain Dataset STaR** (MOYENNE) : Implémenter un système de validation humaine pour les entrées `GoldDataset` afin de prévenir l'empoisonnement du modèle IA.
- [ ] **Audit de Dépendances Continu** : Automatisation du scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
