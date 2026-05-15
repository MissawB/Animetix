# 📋 Guide des Commandes : Animetix (SOTA 2026)

Ce guide répertorie toutes les commandes nécessaires pour opérer, maintenir, évaluer et déployer la plateforme Animetix. Assurez-vous d'être à la racine du projet avec votre environnement virtuel activé (`.venv`).

---

## 🚀 1. Déploiement & Infrastructure (Docker)
Gestion de l'infrastructure globale incluant PostgreSQL, Neo4j, Redis, ChromaDB et les serveurs d'inférence (vLLM).

| Commande | Description |
| :--- | :--- |
| `python scripts/pre_flight_check.py` | **(CRITIQUE)** Lance la vérification de production (Variables d'environnement, connexions DB, extensions). À lancer avant tout déploiement. |
| `docker-compose -f deploy/docker-compose.yml up -d --build` | Lance toute l'infrastructure en arrière-plan. |
| `docker-compose -f deploy/docker-compose.yml stop` | Arrête tous les services sans supprimer les données. |
| `docker-compose -f deploy/docker-compose.yml logs -f web` | Affiche les logs en temps réel de l'application Django. |

---

## 🌐 2. Backend Django (Serveur Web)
Commandes pour gérer la base de données relationnelle et le serveur web.

| Commande | Description |
| :--- | :--- |
| `python src/backend/manage.py runserver` | Lance le serveur de développement interactif (port 8000). |
| `python src/backend/manage.py makemigrations` | Prépare les changements de structure (ex: nouvelles dimensions vectorielles). |
| `python src/backend/manage.py migrate` | Applique les migrations à PostgreSQL (incluant les index HNSW pgvector). |
| `python src/backend/manage.py createsuperuser` | Crée un compte administrateur pour l'interface de gestion `/admin`. |

---

## 🕸️ 3. Pipeline de Données & Knowledge Graph (Dagster)
Orchestration de l'ingestion, de la vectorisation multimodale et de la synchronisation Neo4j.

| Commande | Description |
| :--- | :--- |
| `dagster dev -f src/pipeline/dagster_app.py` | Lance l'interface UI de Dagster pour orchestrer et monitorer le pipeline de données. |
| `python src/pipeline/neo4j_sync.py` | Lance manuellement la synchronisation de la base PostgreSQL vers le Knowledge Graph Neo4j. |
| `python src/pipeline/anime/vectorize_anime.py` | Lance la vectorisation SOTA (Jina-v3 texte + SigLIP vision) et la synchronisation incrémentale du graphe. |

---

## 🧠 4. Intelligence Artificielle & MLOps
Commandes avancées pour l'entraînement, l'évaluation et l'auto-amélioration des modèles (Self-Evolving Agents).

### Évaluation Continue (LooP)
| Commande | Description |
| :--- | :--- |
| `python src/scripts/mlops_rag_eval.py` | Lance l'évaluation automatique Ragas (Fidélité, Pertinence) sur un échantillon pour détecter les régressions. |
| `python src/pipeline/mlops/evaluation_metrics.py` | Calcule les scores Hit Rate et MRR globaux sur le "Gold Dataset". |

### Alignement & Métacognition (RLHF / DPO)
| Commande | Description |
| :--- | :--- |
| `python src/pipeline/mlops/dpo_feedback_loop.py` | Analyse les feedbacks utilisateurs et génère un dataset DPO nettoyé pour le fine-tuning. |
| `python src/scripts/run_self_play_debate.py` | Lance le système de débat entre agents pour générer des données synthétiques "Gold" (SOTA 2026). |
| `python src/scripts/train_akinetix_rl.py` | Lance l'entraînement par Renforcement (RL) de l'agent Akinetix sur son propre environnement. |

### Distillation & Optmimisation SLM
| Commande | Description |
| :--- | :--- |
| `python src/scripts/distill_draft_model.py` | Lance le pipeline de distillation : entraîne le modèle "Scout" SLM à partir des données générées par le modèle principal (Llama 8B+). |

---

## 🛠 5. Services & Workers Asynchrones
Pour le traitement des événements et des tâches de fond.

| Commande | Description |
| :--- | :--- |
| `cd src/backend; celery -A animetix_project worker --loglevel=info` | Démarre le worker Celery pour gérer les tâches asynchrones (nettoyage WebSockets, calculs lourds). |

---

## 🧹 6. Maintenance
Commandes de routine.

| Commande | Description |
| :--- | :--- |
| `pip install -r requirements.txt` | Installe ou met à jour toutes les dépendances Python du projet (incluant `bleach`, `pydantic`). |
| `python scripts/check_chroma_counts.py` | Vérifie le nombre d'éléments indexés dans les bases vectorielles locales de fallback. |
