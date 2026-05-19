# 🏗️ Architecture & Fonctionnalités : Animetix

Ce document détaille les choix de conception et l'implémentation technique du projet **Animetix**.

## 1. Architecture du Système IA (RAG 2.0)

Animetix utilise une approche agentique pour la découverte de média, articulée autour de trois piliers :

### A. Persistance Unifiée & Recherche Vectorielle
*   **UnifiedRepositoryAdapter** : Gère la persistance hybride. Utilise **PgVector (PostgreSQL)** avec index **HNSW** comme moteur primaire pour une performance sub-seconde sur 100k+ items. **ChromaDB** sert de fallback local et de stockage de synchronisation, garantissant la résilience des données vectorielles.
*   **Embeddings de Texte** : **Jina-v3** (1024 dims). SOTA 2026 gérant 32k tokens de contexte et optimisé pour les langues asiatiques/multilingues.
*   **Embeddings Multimodaux** : **SigLIP-SO400M** (1152 dims). Unifie l'espace latent entre images et textes.
*   **Reranking** : **BGE-Reranker-v2-Gemma**. Précision chirurgicale sur le top 10 des résultats.
*   **Optimisation Matryoshka (MRL)** : Recherche vectorielle en deux phases (128/256 dims pour le filtrage rapide, 1024 dims pour le raffinement). Gain de performance de 80%.

### B. Couche de Raisonnement (Agentic RAG 2.0)
*   **Architecture Scout** : Utilisation d'un modèle ultra-léger (SLM) comme "éclaireur" pour distiller le contexte brut et traverser le graphe Neo4j en millisecondes.
*   **Multi-Agent Orchestration** : Découplage en **Searcher**, **Critic** et **Synthesizer**.
*   **Test-Time Compute** : Allocation dynamique de tokens de réflexion (Thinking Mode) via **DeepSeek-R1** ou **Qwen-Thinking**.

### C. Graphe de Connaissances (Neo4j)
*   **GraphRAG Avancé** : Raisonnement "Multi-Hop" et synthèses de communautés globales.
*   **Automatisation** : Synchronisation incrémentale via le pipeline Dagster.

## 3. Optimisations & Scalabilité SOTA

*   **Matryoshka Dynamic Slicing** : Recherche vectorielle en deux phases (128 dims pour le filtrage, 1024 dims pour le reranking). Gain de performance de 80%.
*   **Quantisation 2.0 (BitNet 1.58b)** : Support des modèles à un bit pour faire tourner des architectures de 30B+ sur du matériel grand public.

## 2. Modes de Jeu & Innovation

### Solo
*   **Classic** : Recherche par similarité sémantique pure.
*   **Emoji Decode** : Identification d'œuvres via des suites d'emojis générées par LLM.
*   **Akinetix** : Algorithme Bayesien classique optimisé pour deviner les personnages.
*   **Paradox Quest** : Utilisation d'IA Neuro-Symbolique (Z3 Solver) pour détecter les anomalies thématiques.
*   **Vision Quest** : Reconnaissance visuelle interactive via CLIP.

### Social & Créatif
*   **Duels 1vs1** : Compétition temps réel via WebSockets (Django Channels).
*   **La Forge** : Fusion d'univers générant des synopsis et des visuels via Stable Diffusion/Flux.

## 3. Standards Techniques & Observabilité

### Architecture Atomique & Hexagonale
Le projet respecte une séparation stricte et une structure atomique :
- **Atomicité** : Les composants doivent être petits, à usage unique et facilement interchangeables.
- **Domain** : Logique pure (`core/`), typage strict (`Pydantic`), prompts externalisés (`YAML`).
- **Infrastructure** : Adaptateurs interchangeables via le **FallbackInferenceAdapter**. Celui-ci orchestre une cascade de moteurs d'inférence (Transformers local 4-bit, vLLM, GGUF via llama.cpp, et Brain API) pour garantir une disponibilité maximale.

### Injection de Dépendances & Lazy Loading
Le projet utilise un **Conteneur de Dépendances** personnalisé (`src/backend/animetix/containers.py`) pour orchestrer l'instanciation des services.
- **Lazy Loading** : Les services ne sont instanciés qu'au moment de leur première utilisation, réduisant le temps de démarrage du serveur et la consommation mémoire initiale.
- **Découplage** : Centralise la configuration des adaptateurs et des services, facilitant les tests unitaires via l'injection de mocks.

### État d'Avancement & Priorités
- **Terminé : Modularisation de la Logique UI** : Découpage de `views.py` en modules spécialisés dans `src/backend/animetix/views/`, éliminant le "God Object".
- **Haute Priorité : Découplage des Utils** : Migration des fonctions utilitaires globales vers des services de domaine pour maximiser la réutilisabilité.
- **Haute Priorité : Renforcement de la Gestion des Erreurs** : Standardisation des exceptions et propagation propre via les adaptateurs de fallback.

### MLOps & Sécurité
- **Boucle DPO** : Collecte de feedback *Chosen/Rejected* validé pour l'alignement continu des modèles.
- **Observabilité** : Monitoring des coûts LLM (token tracking) et évaluation systématique via **Ragas**.
- **Sécurité IA** : Protection contre les injections XSS via sanitisation des outputs LLM (Bleach).

## 4. Documentation API
- **Swagger UI** : `/api/docs/`
- **Redoc** : `/api/redoc/`

---
*Version 3.0 - Focus Scalabilité, Sécurité et Inférence Streaming*
