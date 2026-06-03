# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

*Aucune tâche pendante dans cette section.*

## 🚀 Intégrations & Pages Manquantes (Frontend)

- [ ] **Hub "Forge Créative" (Routing)** : La page `ForgeHubPage.tsx` a été développée mais est orpheline. Il faut l'ajouter au routeur (ex: `LabRoutes.tsx` ou `AppRouter.tsx`) pour centraliser l'accès aux laboratoires de médias.
- [ ] **Hub "Cognition & Social"** : Créer une vue unifiée pour regrouper l'Archetype Nexus, la Gestion Neuro-Memory et le Counterfactual Simulator (actuellement éparpillés entre `SocialRoutes` et `SearchRoutes`).
- [ ] **Exposition Publique des Outils Expert** : Créer des versions "Read-only" (publiques) du SOTA Benchmarking et du Graph Debugger pour les utilisateurs avancés (actuellement limités aux routes `/admin/`).

## 🧬 Innovations SOTA & Curation

- [x] **Expliquabilité Avancée (XAI)** : Développer le composant/dashboard frontend détaillant les scores de confiance, les logprobs, les poids sémantiques et les sources RAG pour chaque réponse de l'IA (le backend l'expose déjà).
- [ ] **Dashboard "Mon Empreinte IA"** : Créer une interface unifiée permettant à l'utilisateur de visualiser les règles logiques (Z3) et les vecteurs de préférence qui définissent son profil.
- [x] **Modularisation du Singularity Lab** : Isoler les 5 modules (Quantum, Swarm, Plasticity, Compiler, Multiverse) dans des vues immersives distinctes pour améliorer l'UX.

## 🛡️ Sécurité & Résilience

- [ ] **Audit de Dépendances Continu** : Automatisation du scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
- [ ] **Protection contre les Injections de Prompts** (Priorité : HAUTE) : Remplacer l'approche par liste noire (Regex) dans `sanitize_for_prompt` (`backend/core/utils/security.py`) par des délimiteurs stricts (ex: balises XML) et un modèle de classification secondaire (Guardrail) pour une meilleure robustesse face aux LLMs.
- [ ] **Mitigation SSRF dans les Scrapers MLOps** (Priorité : CRITIQUE) : Remplacer l'utilisation directe de `urllib.request.urlopen()` par la fonction sécurisée interne `safe_http_request()` dans `fandom_lore_scraper.py` et autres scripts de la pipeline afin d'éviter toute faille SSRF si l'entrée d'URLs devient dynamique.

## ☁️ Déploiement & Intégration Google Cloud (GCP)
- [x] **Migration ChromaDB vers pgvector (Cloud SQL)** (Priorité : CRITIQUE) : Déplacer le stockage d'embeddings local vers l'extension pgvector de l'instance PostgreSQL managée pour assurer la persistance RAG en environnement serverless stateless.
- [ ] **Décommissionnement Celery Beat vers Cloud Run Jobs** (Priorité : HAUTE) : Migrer l'ensemble des tâches récurrentes planifiées (optimisation DPO, ingestion de données, maintenance MLOps) vers des Jobs Cloud Run éphémères configurés avec Cloud Scheduler.
- [ ] **Migration de la file asynchrone vers Google Cloud Tasks** (Priorité : MOYENNE) : Remplacer l'architecture Celery Worker + Redis par une file HTTP gérée par Cloud Tasks pour exécuter de manière serverless les tâches utilisateur asynchrones (ex: génération d'images).
- [ ] **Authentification IAM Directe PostgreSQL (Passwordless)** (Priorité : MOYENNE) : Configurer la connexion Django à Cloud SQL en s'authentifiant par jetons IAM associés au compte de service plutôt que par identifiants statiques.
- [ ] **Inférence ML Lourde sur Cloud Run GPU Serverless** (Priorité : BASSE) : Déployer la Brain API (FastAPI, modèles TTS/OCR) sur Cloud Run avec GPU Nvidia (L4) serverless pour un auto-scaling complet à 0.