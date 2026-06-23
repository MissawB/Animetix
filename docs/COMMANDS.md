# 📋 Commands Guide: Animetix (SOTA 2026)

This guide lists all the commands needed to run, maintain, evaluate, test, and deploy the Animetix platform.

> [!IMPORTANT]
> - For Python commands (Backend, Pipeline, MLOps, Scripts), ensure you are in the project root directory (`Double_scenario_Project/`) with your virtual environment active (`.venv`).
> - For Node/Vite commands (Frontend), navigate to the `frontend/` directory first (`cd frontend`).

---

## 🚀 1. Deployment & Infrastructure (Docker)
Manages the global production/staging infrastructure, including PostgreSQL (pgvector), Neo4j, Redis, and inference containers.

| Command | Directory | Description |
| :--- | :--- | :--- |
| `python scripts/pre_flight_check.py` | Root | **(CRITICAL)** Runs production check (Environment variables, database connections). Must be executed before any deployment. |
| `docker-compose -f deploy/docker-compose.yml up -d --build` | Root | Starts the entire infrastructure stack (Databases, Cache, Workers) in the background with image rebuild. |
| `docker-compose -f deploy/docker-compose.yml stop` | Root | Safely stops all containers without destroying persistent volumes. |
| `docker-compose -f deploy/docker-compose.yml down` | Root | Stops and removes containers and their associated networks. |
| `docker-compose -f deploy/docker-compose.yml logs -f web` | Root | Follows Django application logs in real-time. |
| `docker-compose -f deploy/docker-compose.yml exec db psql -U postgres` | Root | Opens an interactive PostgreSQL shell in the database container. |

---

## 🌐 2. Django Backend (Headless API & Administration)
Commands to manage the headless API server, apply migrations, and seed the catalog databases.

| Command | Directory | Description |
| :--- | :--- | :--- |
| `daphne backend/api/animetix_project/asgi.py` | Root | Launches the local API development server with Django Channels (port `8000`). |
| `python backend/api/manage.py makemigrations` | Root | Prepares new migration files following database model changes. |
| `python backend/api/manage.py migrate` | Root | Applies migrations to PostgreSQL (including creating HNSW vector indexes). |
| `python backend/api/manage.py createsuperuser` | Root | Creates a superuser account for the Django Admin dashboard (`/admin`). |
| `python backend/api/manage.py seed_achievements` | Root | Populates the database with default game achievements and challenge milestones. |
| `python backend/api/manage.py sync_catalog` | Root | Synchronizes media catalogs, importing metadata from external APIs (TMDB, IGDB). |
| `python backend/api/manage.py show_urls` | Root | Lists all exposed API routes (requires django-extensions). |
| `python backend/api/manage.py shell` | Root | Launches an interactive Python shell with the Django context loaded. |
| `python backend/api/manage.py export_rlhf_data` | Root | Exports RLHF data for model fine-tuning. |
| `python backend/api/manage.py restore_brain_service` | Root | Restores the brain service from a backup. |
| `python backend/api/manage.py run_red_teaming` | Root | Executes red teaming exercises against the AI models. |
| `python backend/api/manage.py run_scheduled_task` | Root | Manually triggers a specific scheduled background task. |
| `python backend/api/manage.py run_scheduled_task manga-updates-check` | Root | Checks favorited mangas for new chapters (via Suwayomi) and pushes WebSocket notifications. In prod this runs every 6 h via the `animetix-manga-updates` Cloud Run Job + Scheduler (see `scripts/deploy/deploy_jobs.py`). |
| `python backend/api/manage.py sync_bigquery_recommendations` | Root | Synchronizes recommendations with BigQuery. |
| `python backend/api/manage.py check` | Root | Checks the entire Django project for potential problems. |
| `python backend/api/manage.py dumpdata` | Root | Dumps database contents to a fixture file (e.g., JSON). |
| `python backend/api/manage.py loaddata` | Root | Loads data from a fixture file into the database. |
| `python backend/api/manage.py test` | Root | Runs all tests for the installed applications. |
| `python backend/api/manage.py spectacular --file schema.yaml` | Root | Generates the OpenAPI schema (YAML) for the API. |
| `python backend/api/manage.py compilemessages` | Root | Compiles .po files into .mo files for internationalization. |

---

## 💻 3. React SPA Frontend (Vite, TypeScript & Storybook)
Commands for the development cycle of the React 19 SPA client application.

> [!TIP]
> All commands below must be executed from within the frontend directory: `cd frontend`

| Command | Directory | Description |
| :--- | :--- | :--- |
| `npm install` | `frontend/` | Installs required Node.js packages and dependencies. |
| `npm run dev` | `frontend/` | Starts the local Vite development server (port `5173`). Vite proxies `/api` and `/ws` to Django (port `8000`). |
| `npm run build` | `frontend/` | Compiles the React application, generating the optimized production bundle under `dist/`. |
| `npm run preview` | `frontend/` | Runs a local server to preview the production bundle compiled by Vite. |
| `npm run lint` | `frontend/` | Lints the codebase using ESLint to check for style or accessibility violations. |
| `npm run check-types` | `frontend/` | Validates TypeScript types across the codebase without building (`tsc --noEmit`). |
| `npm run generate:api` | `frontend/` | Generates TypeScript API typings (`backend/types/api.d.ts`) based on the OpenAPI `schema.yaml` schema. |
| `npm run storybook` | `frontend/` | Starts Storybook in development mode (port `6006`) to build and test isolated UI components. |
| `npm run build-storybook` | `frontend/` | Compiles Storybook into a static site under `storybook-static/` for deployment. |

---

## 🕸️ 4. Data Ingestion & Knowledge Graph (Sync & Graph)
ETL pipelines, multimodal indexing, and Neo4j graph synchronizations.

| Command | Directory | Description |
| :--- | :--- | :--- |
| `python backend/pipeline/neo4j_sync.py` | Root | Runs the entity and relationship synchronization from PostgreSQL to the Neo4j Knowledge Graph. |
| `python backend/pipeline/anime/vectorize_anime.py` | Root | Triggers document vectorization (text via Jina-v3 and images via SigLIP) and updates the vector search index and graph. |
| `python scripts/test_graph_logic_isolated.py` | Root | Executes isolated tests validating Cypher queries and Neo4j database consistency. |

---

## 🧠 5. Artificial Intelligence, RAG & MLOps
Model training, distillation, agent alignment (RLHF/DPO), and benchmarks.

### RAG Evaluation & Alignment (DPO / RL)
| Command | Directory | Description |
| :--- | :--- | :--- |
| `python backend/api/manage.py run_rag_ablation --source curated` | Root | Runs the RAG pipeline with cognitive boosters ON vs OFF over a query set and reports RAGAS deltas (faithfulness / relevancy / context precision). Use `--source gold` for the Gold Dataset questions. Requires a live judge LLM. |
| `python backend/scripts/mlops_rag_eval.py` | Root | Runs automated Ragas evaluations (Faithfulness, Answer Relevance) on samples to check for regressions. |
| `python backend/pipeline/mlops/evaluation_metrics.py` | Root | Calculates global evaluation metrics (Hit Rate, MRR) against the "Gold Dataset". |
| `python backend/pipeline/mlops/dpo_feedback_loop.py` | Root | Collects user interactions and corrections to compile a local DPO dataset. |
| `python scripts/curate_dpo_dataset.py` | Root | Filters and cleans the interaction database to export formatted DPO fine-tuning datasets. |
| `python backend/scripts/run_self_play_debate.py` | Root | Simulates multi-agent debates to generate high-quality synthetic "Gold" data. |
| `python backend/scripts/train_akinetix_rl.py` | Root | Trains the Akinetix RL agent inside its custom simulated environment. |

### Fine-Tuning, Distillation & Embeddings
| Command | Directory | Description |
| :--- | :--- | :--- |
| `python backend/scripts/distill_draft_model.py` | Root | Runs model distillation: trains a "Scout" Small Language Model (SLM) based on outputs from Llama 8B+. |
| `python backend/scripts/finetune_clip_lora.py` | Root | Runs LoRA fine-tuning on a vision encoder (CLIP/SigLIP) to better capture anime tropes. |
| `python backend/scripts/seed_face_embeddings.py` | Root | Computes and saves reference facial embeddings of characters for multimodal queries. |

### Quality & Latency Benchmarks
| Command | Directory | Description |
| :--- | :--- | :--- |
| `python scripts/benchmark_latency.py` | Root | Measures response latencies across inference adapters (local Ollama, Cloud BrainAPI). |
| `python scripts/benchmark_quality_v2.py` | Root | Evaluates structured generation and search qualities. |
| `python backend/scripts/benchmark_long_context.py` | Root | Measures retrieval accuracy on extremely long contexts (needle-in-a-haystack test). |
| `python backend/scripts/benchmark_multi_lora.py` | Root | Measures overhead and latencies when dynamically switching multiple LoRA adapters. |

---

## 🧪 6. Testing & Quality Assurance (QA)
Unit tests, integration tests, visual regression tests, and end-to-end suites.

| Command | Directory | Description |
| :--- | :--- | :--- |
| `pytest` | Root | Runs the backend Django test suite and domain logic validations. |
| `python scripts/setup_e2e.py` | Root | Downloads and installs browser binaries (Playwright) required for integration testing. |
| `pytest tests/e2e` | Root | Runs Playwright end-to-end user journey tests on the API and database. |
| `npm run test` | `frontend/` | Runs Vitest unit and component tests for the React application. |
| `npm run test:e2e` | `frontend/` | Runs Playwright end-to-end integration tests on the complete React frontend. |
| `npm run test:vrt` | `frontend/` | Runs Visual Regression Testing (VRT) using Playwright screenshots. |
| `npm run test:vrt:update` | `frontend/` | Updates baseline reference screenshots for VRT. |

---

## 🧹 7. Maintenance, Diagnostics & Workers
Maintenance scripts, database reconciliation, and background worker pools.

| Command | Directory | Description |
| :--- | :--- | :--- |
| `pip install -r requirements.txt` | Root | Installs and updates required Python libraries. |
| `python scripts/reconcile_db.py` | Root | **(CRITICAL)** Analyzes and resolves sync discrepancies between PostgreSQL and Neo4j. |
| `python scripts/check_vector_counts.py` | Root | Inspects document counts in the pgvector vector store. |
| `python scripts/check_db_tables.py` | Root | Provides a quick inspection of PostgreSQL physical table statuses. |
| `python scripts/check_instantiation.py` | Root | Dry-runs adapter instantiations to validate bindings and type signatures. |
| `python scripts/check_migrations_any_db.py` | Root | Inspects migration status on any target database. |
| `python scripts/generate_offline_db.py` | Root | Compiles a lightweight SQLite database for offline catalog search capability. |
| `python scripts/detect_embedding_drift.py` | Root | Detects vector semantic shifts following embedding model updates. |
| `python scripts/verify_brain_adapter.py` | Root | Performs a smoke test on the primary cloud inference adapter. |
| `python scripts/rag_smoke_test.py` | Root | Runs a basic verification check on the RAG pipeline (Vector Search -> Rerank). |
| `python scripts/vision_quest_worker.py` | Root | Starts the background worker processing vision queue tasks. |
| `cd backend/api; celery -A animetix_project worker --loglevel=info` | `backend/api` | Starts Celery workers to handle background tasks (session cleanup, telemetry loops). |
