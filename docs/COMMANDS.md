# 📋 Guide des Commandes : Animetix (SOTA 2026)

Ce guide répertorie de manière exhaustive toutes les commandes nécessaires pour opérer, maintenir, évaluer, tester et déployer la plateforme Animetix. 

> [!IMPORTANT]
> - Pour les commandes Python (Backend, Pipeline, MLOps, Scripts), assurez-vous d'être à la racine du projet (`Double_scenario_Project/`) avec votre environnement virtuel activé (`.venv`).
> - Pour les commandes Node/Vite (Frontend), naviguez d'abord dans le répertoire `frontend/` (`cd frontend`).

---

## 🚀 1. Déploiement & Infrastructure (Docker)
Gestion de l'infrastructure globale de production/staging incluant PostgreSQL, Neo4j, Redis, ChromaDB et les serveurs d'inférence.

| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `python scripts/pre_flight_check.py` | Racine | **(CRITIQUE)** Lance la vérification de production (Variables d'environnement, connexions DB). À exécuter impérativement avant tout déploiement. |
| `docker-compose -f deploy/docker-compose.yml up -d --build` | Racine | Démarre toute l'infrastructure (DBs, Cache, Workers) en arrière-plan avec reconstruction des images. |
| `docker-compose -f deploy/docker-compose.yml stop` | Racine | Arrête proprement tous les conteneurs Docker sans détruire les volumes persistants. |
| `docker-compose -f deploy/docker-compose.yml down` | Racine | Arrête et supprime les conteneurs et les réseaux Docker associés. |
| `docker-compose -f deploy/docker-compose.yml logs -f web` | Racine | Affiche les logs applicatifs de Django en temps réel. |
| `docker-compose -f deploy/docker-compose.yml exec db psql -U postgres` | Racine | Ouvre une console PostgreSQL interactive dans le conteneur de base de données. |

---

## 🌐 2. Backend Django (API Headless & Administration)
Commandes pour administrer le serveur backend headless, appliquer les schémas de base de données et initialiser les données du catalogue.

| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `python backend/api/manage.py runserver` | Racine | Lance le serveur de développement API (port `8000`). |
| `python backend/api/manage.py makemigrations` | Racine | Prépare les nouvelles migrations suite à des modifications de modèles. |
| `python backend/api/manage.py migrate` | Racine | Applique les migrations à la base PostgreSQL (y compris la création des index HNSW vectoriels). |
| `python backend/api/manage.py createsuperuser` | Racine | Crée un compte super-administrateur pour l'interface Django Admin (`/admin`). |
| `python backend/api/manage.py seed_achievements` | Racine | Initialise la base de données avec les données prédéfinies de succès (Succès de jeu, défis). |
| `python backend/api/manage.py sync_catalog` | Racine | Synchronise le catalogue de médias en important les métadonnées SOTA depuis les APIs externes (TMDB, IGDB). |
| `python backend/api/manage.py show_urls` | Racine | Liste l'ensemble des routes d'API exposées (nécessite django-extensions). |
| `python backend/api/manage.py shell` | Racine | Démarre un interpréteur Python interactif avec le contexte Django chargé. |

---

## 💻 3. Frontend React SPA (Vite, TypeScript & Storybook)
Commandes pour le cycle de vie du frontend SPA moderne développé en React 19 et Vite.

> [!TIP]
> Toutes les commandes ci-dessous doivent être lancées après s'être positionné dans le dossier du frontend : `cd frontend`

| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `npm install` | `frontend/` | Installe les packages et dépendances Node.js requises. |
| `npm run dev` | `frontend/` | Démarre le serveur de développement local Vite (port `5173`). Configure un reverse-proxy pour transférer `/api` et `/ws` vers Django (port `8000`). |
| `npm run build` | `frontend/` | Compile le frontend React et génère le bundle de production optimisé dans le dossier `dist/`. |
| `npm run preview` | `frontend/` | Exécute un serveur local pour prévisualiser le bundle de production généré par Vite. |
| `npm run lint` | `frontend/` | Analyse le code via ESLint pour détecter les violations des standards de style ou d'accessibilité. |
| `npm run check-types` | `frontend/` | Valide les types TypeScript sur l'ensemble des fichiers sans générer de bundle (`tsc --noEmit`). |
| `npm run generate:api` | `frontend/` | Génère les définitions de types TypeScript d'API (`backend/types/api.d.ts`) à partir du schéma OpenAPI `schema.yaml` du projet. |
| `npm run storybook` | `frontend/` | Démarre Storybook en mode développement (port `6006`) pour concevoir et tester les composants isolés. |
| `npm run build-storybook` | `frontend/` | Compiles Storybook sous forme de site statique dans le dossier `storybook-static/` pour déploiement. |

---

## 🕸️ 4. Pipeline de Données & Knowledge Graph (Dagster & Graph)
Orchestration du pipeline ETL, de l'indexation multimodale et de la synchronisation avec le graphe de connaissances.

| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `dagster dev -f backend/pipeline/dagster_app.py` | Racine | Lance le serveur de développement Dagster pour orchestrer, visualiser et matérialiser les assets du pipeline. |
| `python backend/pipeline/neo4j_sync.py` | Racine | Exécute manuellement la synchronisation des entités et relations de PostgreSQL vers le Knowledge Graph Neo4j. |
| `python backend/pipeline/anime/vectorize_anime.py` | Racine | Déclenche la vectorisation (texte via Jina-v3 et images via SigLIP) et met à jour l'index vectoriel et le graphe. |
| `python scripts/test_graph_logic_isolated.py` | Racine | Exécute des validations isolées sur les requêtes Cypher complexes et la cohérence de la structure Neo4j. |

---

## 🧠 5. Intelligence Artificielle, RAG & MLOps
Entraînement des modèles, distillation SLM, auto-amélioration des agents (RLHF/DPO) et benchmarks.

### Évaluation RAG & Alignement (DPO / RL)
| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `python backend/scripts/mlops_rag_eval.py` | Racine | Lance l'évaluation automatique Ragas (Faithfulness, Answer Relevance) sur un échantillon pour détecter toute régression. |
| `python backend/pipeline/mlops/evaluation_metrics.py` | Racine | Calcule les scores globaux d'évaluation RAG (Hit Rate, MRR) sur le "Gold Dataset". |
| `python backend/pipeline/mlops/dpo_feedback_loop.py` | Racine | Récupère et structure les interactions et corrections utilisateur pour exporter un dataset DPO. |
| `python scripts/curate_dpo_dataset.py` | Racine | Filtre, nettoie et formate le dataset d'interactions pour le fine-tuning DPO final. |
| `python backend/scripts/run_self_play_debate.py` | Racine | Simule des débats synthétiques multi-agents pour générer des données de RAG de qualité supérieure ("Gold" data). |
| `python backend/scripts/train_akinetix_rl.py` | Racine | Entraîne l'agent Akinetix par Apprentissage par Renforcement (RL) dans son propre environnement simulé. |

### Fine-Tuning, Distillation & Embeddings
| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `python backend/scripts/distill_draft_model.py` | Racine | Lance la distillation : entraîne un Small Language Model (SLM) "Scout" en se basant sur les outputs de Llama 8B+. |
| `python backend/scripts/finetune_clip_lora.py` | Racine | Réalise le fine-tuning LoRA d'un encodeur d'image (CLIP/SigLIP) pour mieux appréhender les tropes visuels d'animes. |
| `python backend/scripts/seed_face_embeddings.py` | Racine | Génère et enregistre les embeddings faciaux de référence des personnages d'animes pour la recherche multimodale. |

### Benchmarks de Performance & Latence
| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `python scripts/benchmark_latency.py` | Racine | Évalue la latence de traitement des adaptateurs d'inférence (Ollama local, BrainAPI Cloud). |
| `python scripts/benchmark_quality_v2.py` | Racine | Benchmark de qualité comparative sur les tâches de génération structurée et de recherche. |
| `python backend/scripts/benchmark_long_context.py` | Racine | Mesure la performance et l'intégrité de la RAG sur des contextes extrêmement larges (aiguille dans une botte de foin). |
| `python backend/scripts/benchmark_multi_lora.py` | Racine | Mesure la surcharge et la latence lors de l'activation dynamique de multiples adaptateurs LoRA en simultané. |

---

## 🧪 6. Tests & Assurance Qualité (QA)
Exécution de la suite de tests unitaires, d'intégration, de régression visuelle et de bout en bout (E2E).

| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `pytest` | Racine | Démarre la suite complète de tests unitaires et d'intégration du Backend Django et de la logique de domaine. |
| `python scripts/setup_e2e.py` | Racine | Télécharge et configure les binaires de navigateurs (Playwright) indispensables pour exécuter les tests d'interface. |
| `pytest tests/e2e` | Racine | Lance les tests d'intégration End-to-End (E2E) sur le backend Django. |
| `npm run test` | `frontend/` | Exécute les tests unitaires et de composants du Frontend React via **Vitest**. |
| `npm run test:e2e` | `frontend/` | Exécute les tests End-to-End de l'application React complète à l'aide de **Playwright**. |
| `npm run test:vrt` | `frontend/` | Exécute les tests de non-régression visuelle (Visual Regression Testing) basés sur les captures d'écran Playwright. |
| `npm run test:vrt:update` | `frontend/` | Met à jour les captures d'écran de référence pour les tests de non-régression visuelle. |

---

## 🧹 7. Maintenance, Diagnostic & Workers
Scripts utilitaires pour assurer l'intégrité des données, la cohérence des environnements et le bon fonctionnement des workers de fond.

| Commande | Répertoire | Description |
| :--- | :--- | :--- |
| `pip install -r requirements.txt` | Racine | Installe et met à jour les bibliothèques Python requises pour le backend et les scripts. |
| `python scripts/reconcile_db.py` | Racine | **(CRITIQUE)** Analyse et résout les désalignements et incohérences de données entre PostgreSQL et Neo4j. |
| `python scripts/check_chroma_counts.py` | Racine | Inspecte et retourne le nombre de documents indexés dans l'instance vectorielle ChromaDB de fallback. |
| `python scripts/check_db_tables.py` | Racine | Permet une introspection rapide de l'état physique des tables PostgreSQL. |
| `python scripts/check_instantiation.py` | Racine | Instancie à froid l'ensemble des adaptateurs et ports pour valider le typage et l'injection de dépendances. |
| `python scripts/check_migrations_any_db.py` | Racine | Inspecte l'état d'avancement des migrations sur n'importe quelle base cible configurée. |
| `python scripts/compile_translations.py` | Racine | Compile les fichiers de traduction linguistiques `.po` du projet Django en formats binaires `.mo`. |
| `python scripts/generate_offline_db.py` | Racine | Génère et exporte une base de données SQLite statique allégée pour le fonctionnement offline du client. |
| `python scripts/detect_embedding_drift.py` | Racine | Détecte d'éventuelles dérives de représentation vectorielle suite à des mises à jour de modèles d'embeddings. |
| `python scripts/verify_brain_adapter.py` | Racine | Effectue un test de fumée (Smoke Test) sur l'adaptateur principal de l'API LLM (Brain API / FallbackInference). |
| `python scripts/rag_smoke_test.py` | Racine | Lance un test de fumée sur l'API de recherche RAG pour s'assurer du bon fonctionnement de la chaîne ChromaDB -> Rerank. |
| `python scripts/vision_quest_worker.py` | Racine | Démarre le worker autonome dédié au traitement asynchrone des tâches multimodales de Vision Quest. |
| `cd backend/api; celery -A animetix_project worker --loglevel=info` | Racine | Démarre les workers Celery pour la gestion asynchrone en arrière-plan (nettoyage de sessions, calculs de fond). |
