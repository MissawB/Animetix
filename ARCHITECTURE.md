# 🏗️ Architecture & Fonctionnalités : Animetix

Ce document détaille les choix de conception et l'implémentation technique du projet **Animetix**.

## 1. Architecture du Système IA

Animetix repose sur une architecture **RAG 2.0 (Retrieval-Augmented Generation)** avancée, divisée en trois couches :

### A. Couche de Représentation (Embeddings)
*   **Modèle** : `paraphrase-multilingual-mpnet-base-v2` quantifié en **INT8**.
*   **Espace Latent** : Les œuvres sont projetées dans un espace à 768 dimensions. La quantification dynamique réduit l'empreinte RAM de 450 Mo à ~120 Mo sans perte de précision.
*   **Vector Database** : **ChromaDB** avec indexation HNSW pour des recherches de similarité en millisecondes.

### B. Couche de Raisonnement (Agentic AI)
*   **Pattern ReAct** : L'IA ne génère pas simplement du texte, elle utilise une boucle *Thought -> Action -> Observation*.
*   **Tooling** : L'agent a accès à ChromaDB (mémoire sémantique), Neo4j (mémoire logique) et à la base JSON (faits bruts).
*   **Reranking** : Utilisation de `BGE-Reranker-Base` pour affiner le top 10 des résultats de recherche et garantir un score de 100% indiscutable.

### C. Couche Relationnelle (Knowledge Graph)
*   **Neo4j** : Stocke les relations entre les œuvres, les studios, les auteurs et les micro-tags générés par LLM.
*   **Utilité** : Permet à l'IA d'expliquer *pourquoi* deux œuvres se ressemblent (ex: "Même studio de production").

## 2. Modes de Jeu & Innovation

### Solo
1.  **Animetix Classic** : Recherche sémantique pure. Score de 0 à 100 basé sur la distance cosinus.
2.  **Emoji Decode** : L'IA traduit un synopsis en une série de 5 emojis complexes.
3.  **Animinator (Oracle)** : L'utilisateur pose des questions à l'IA. L'IA utilise son système d'agent pour vérifier ses connaissances avant de répondre.
4.  **Akinetix (Devin)** : L'inverse. L'IA pose des questions stratégiques pour réduire le cercle des candidats dans ChromaDB.
5.  **Le Paradoxe** : Test de logique. Trouver l'intrus parmi 3 titres grâce à l'analyse thématique du LLM.

### Social (Multijoueur)
*   **WebSockets** : Utilisation de **Django Channels** pour des salons de jeux instantanés.
*   **Undercover Online** : L'IA trouve deux termes sémantiquement proches pour tromper les joueurs.

### Créativité
*   **La Forge de l'Imaginaire** : Fusion de deux univers. Utilise un LLM pour le scénario et le modèle **Flux.1-schnell** pour générer une illustration unique.

## 3. Flux de Données & Intégration

L'architecture est conçue pour être "data-driven" avec une boucle de rétroaction continue entre l'utilisateur et les modèles d'IA.

### A. Cycle d'Ingestion (Data Pipeline)
1.  **Ingestion** : Dagster exécute des scripts d'ingestion (AniList/Jikan) stockant les données brutes dans `data/raw`.
2.  **Raffinement & Filtrage** : Les données sont nettoyées et filtrées selon des critères de popularité/qualité.
3.  **Vectorisation** : Les entités (animes, mangas, personnages) sont transformées en embeddings et stockées dans **ChromaDB**.
4.  **Génération de Graphe** : Les relations sont injectées dans **Neo4j** pour permettre le raisonnement logique.

### B. Boucle de Rétroaction RLHF (Backend -> ML)
Cette boucle permet d'améliorer l'IA en fonction des interactions réelles :
1.  **Collecte (Backend)** : Django enregistre les feedbacks via `AIFeedback` et les sessions de jeu via `GameplaySession`.
2.  **Export (Port/Adapter)** : La commande Django `export_rlhf_data` (appelée par Dagster) transforme ces entrées SQL en fichiers JSON.
3.  **Préparation TRL** : L'asset Dagster `trl_ready_dataset` convertit les feedbacks en paires *Chosen/Rejected* (DPO format).
4.  **Fine-Tuning** : Les modèles sont ré-entraînés sur ces nouvelles données pour affiner leur comportement "Otaku".

### C. Inférence & Consommation (Brain API)
- Le backend communique avec la **Brain API** pour toutes les tâches de génération.
- La Brain API utilise les index ChromaDB et Neo4j mis à jour par le pipeline Dagster pour ses recherches RAG.

## 4. Organisation du Projet

Le projet suit une structure organisée pour respecter les principes de l'**Architecture Hexagonale** et faciliter la maintenance :

- **`core/`** : Le **Domaine**. Contient la logique métier pure et l'intelligence centrale (`brain.py`). Ce dossier est indépendant des frameworks externes.
- **`backend/`** : L'**Adapteur Driving**. Application Django gérant l'interface utilisateur, les APIs et la logique de jeu.
- **`pipeline/`** : L'**Adapteur Infrastructure**. Orchestration Dagster pour l'ingestion et le traitement des données.
- **`infra/`** : Configurations système et déploiement (`supervisord`, `prometheus`, `docker`).
- **`scripts/`** : Utilitaires de lancement, de maintenance et d'entraînement.
- **`data/`** : Stockage des données à différents stades (brut, processe, modèles, vecteurs).
- **`logs/`** : Centralisation des journaux d'exécution.

## 5. Infrastructure & MLOps

*   **Pipeline de Données** : Orchestrée par **Dagster**. Gère l'ingestion incrémentale (AniList, IGDB, TMDB).
*   **MLOps & RLHF** : Collecte des feedbacks utilisateurs (AIFeedback) pour créer des datasets d'entraînement futurs.
*   **Automatisation Asynchrone** : **Celery + Redis** déportent les calculs lourds (génération d'images) hors du cycle de requête HTTP.
*   **Observabilité** : 
    *   **Prometheus** : Collecte des métriques de performance.
    *   **Grafana** : Tableaux de bord de santé du système.
    *   **Sentry** : Monitoring des erreurs en temps réel.

## 4. Interprétabilité
*   **Visualisation 3D** : Utilisation de **UMAP** pour projeter l'espace latent en 3 dimensions. Cela permet de visualiser les clusters thématiques (ex: le groupe des animes de sport vs les romances).

---
*Document produit pour Animetix - Architecture Version 2.0*
