# Liste des Tâches (TODO) - Animetix

Ce document centralise toutes les tâches techniques, d'architecture et de fonctionnalités qui restent à implémenter. Les tâches complétées sont cochées ou purgées pour être archivées dans `HISTORY.md`.

## 🛠️ Dette Technique & Architecture

*Aucune tâche pendante dans cette section.*

## 🚀 Intégrations & Pages Manquantes (Frontend)

- [ ] **Hub "Forge Créative" (Accessibilité)** : Bien que la route `/forge-hub/` existe, elle est orpheline dans l'UI. Ajouter des points d'entrée dans `LabHubPage.tsx` pour lier les laboratoires créatifs (Manga, Audio, Video, Spatial) au Singularity Lab.
- [ ] **Hub "Cognition" Unifié** : Créer une vue centrale fusionnant l'Archetype Nexus, la Gestion Neuro-Memory et le Counterfactual Simulator (actuellement éparpillés).
- [ ] **Universal Search Hub** : Unifier la recherche textuelle (`/search/`) et la recherche visuelle/temporelle (`/visual-nexus/`) dans une interface de recherche multimodale unique.
- [ ] **Exposition Publique des Outils Expert** : Créer des versions "Read-only" (publiques) du SOTA Benchmarking et du Graph Debugger pour les utilisateurs "Expert" (actuellement limités aux admins).
- [ ] **Live Ingestion Feed (Intelligence Data)** : Créer une page de monitoring temps-réel montrant l'enrichissement sémantique de la Lore (Neo4j/ChromaDB) par les scrapers et l'IA.

## 🧬 Innovations SOTA & Curation

- [x] **Expliquabilité Avancée (XAI)** : Développer le composant/dashboard frontend détaillant les scores de confiance, les logprobs, les poids sémantiques et les sources RAG pour chaque réponse de l'IA (le backend l'expose déjà).
- [ ] **Dashboard "Mon Empreinte IA" (Vecteurs de Préférence)** : Étendre la page Neuro-Memory pour inclure une visualisation spatiale des vecteurs de préférence (goûts utilisateur) déduits par l'IA.
- [x] **Modularisation du Singularity Lab** : Isoler les 5 modules (Quantum, Swarm, Plasticity, Compiler, Multiverse) dans des vues immersives distinctes pour améliorer l'UX.

## 🛡️ Sécurité & Résilience

- [ ] **Audit de Dépendances Continu** : Automatisation du scan des vulnérabilités (Snyk/GitHub Dependabot) pour maintenir le socle technique à jour après le passage à Django 5.2.14.
- [ ] **Protection contre les Injections de Prompts** (Priorité : HAUTE) : Remplacer l'approche par liste noire (Regex) dans `sanitize_for_prompt` (`backend/core/utils/security.py`) par des délimiteurs stricts (ex: balises XML) et un modèle de classification secondaire (Guardrail) pour une meilleure robustesse face aux LLMs.
- [ ] **Mitigation SSRF dans les Scrapers MLOps** (Priorité : CRITIQUE) : Remplacer l'utilisation directe de `urllib.request.urlopen()` par la fonction sécurisée interne `safe_http_request()` dans `fandom_lore_scraper.py` et autres scripts de la pipeline afin d'éviter toute faille SSRF si l'entrée d'URLs devient dynamique.

## ☁️ Déploiement & Intégration Google Cloud (GCP)

- [X] **Réseautage Direct VPC Egress** (Priorité : CRITIQUE) : Remplacer l'usage des connecteurs Serverless VPC Access (`animetix-vpc-conn`) par Direct VPC Egress pour éliminer les coûts fixes des VMs de connexion et réduire la latence réseau vers Cloud SQL/Redis.
- [X] **Tests & Validation Déploiement Google Cloud** (Priorité : HAUTE) : Mettre en place une suite de tests d'intégration complète pour valider les configurations GCP : connexion Cloud SQL (socket Unix & IAM), persistance des données (GCS), authentications secrètes (Secret Manager) et exécution des jobs planifiés (Cloud Scheduler/Cloud Run). Inclure des scénarios de failover et de persistance post-redeployment.
- [X] **Mise en cache du contexte (Vertex AI Context Caching)** (Priorité : HAUTE) : Implémenter le cache de contexte Vertex AI pour le RAG et les requêtes répétitives sur le Lore dans `google_genai_adapter.py`, permettant d'économiser jusqu'à 75% des coûts de tokens d'entrée et de réduire la latence.
- [X] **Protection Edge (Cloud Armor WAF LLM)** (Priorité : HAUTE) : Configurer les règles d'inspection et de WAF de Google Cloud Armor spécifiques aux LLMs pour filtrer les injections de prompts et atténuer les attaques par déni de service de tokens.
- [X] **Gemini Multimodal Live API** (Priorité : MOYENNE) : Évaluer et intégrer l'API Live bidirectionnelle sur WebSockets pour les interactions vocales temps réel, éliminant le besoin de faire tourner des modèles de TTS lourds (`coqui-tts`) sur serveurs GPU.
- [X] **AlloyDB AI & Vector Search (ScaNN)** (Priorité : MOYENNE) : Migrer de Cloud SQL Postgres vers AlloyDB pour exploiter l'indexation ScaNN d'AlloyDB AI (recherche vectorielle 100x plus rapide) et la vectorisation à la source via `google_ml_integration`.
- [X] **Plafonds budgétaires Cloud Run** (Priorité : BASSE) : Définir des limites de budget mensuel (Budget Caps) au niveau des services Cloud Run (notamment pour l'inférence GPU L4) afin de bloquer les dérives de facturation accidentelles ou malveillantes.
- [X] **Inférence ML Lourde sur Cloud Run GPU Serverless** (Priorité : BASSE) : Déployer la Brain API (FastAPI, modèles TTS/OCR) sur Cloud Run avec GPU Nvidia (L4) serverless pour un auto-scaling complet à 0.
- [X] **Migration ChromaDB vers pgvector (Cloud SQL)** (Priorité : CRITIQUE) : Déplacer le stockage d'embeddings local vers l'extension pgvector de l'instance PostgreSQL managée pour assurer la persistance RAG en environnement serverless stateless.
- [X] **Décommissionnement Celery Beat vers Cloud Run Jobs** (Priorité : HAUTE) : Migrer l'ensemble des tâches récurrentes planifiées (optimisation DPO, ingestion de données, maintenance MLOps) vers des Jobs Cloud Run éphémères configurés avec Cloud Scheduler.
- [X] **Migration de la file asynchrone vers Google Cloud Tasks** (Priorité : MOYENNE) : Remplacer l'architecture Celery Worker + Redis par une file HTTP gérée par Cloud Tasks pour exécuter de manière serverless les tâches utilisateur asynchrones (ex: génération d'images).
- [X] **Authentification IAM Directe PostgreSQL (Passwordless)** (Priorité : MOYENNE) : Configurer la connexion Django à Cloud SQL en s'authentifiant par jetons IAM associés au compte de service plutôt que par identifiants statiques.
