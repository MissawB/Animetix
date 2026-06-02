# Plan: Standardize Python Logging

Standardize Python logging across `backend/pipeline` and `backend/adapters` to stabilize the codebase and improve observability.

## Context
Phase 1, Task 1 of the refactoring effort.

## Strategy
1. For each file, add `import logging` if missing.
2. Instantiate logger: `logger = logging.getLogger("animetix." + __name__)`.
3. Replace all `print(...)` with `logger.info(...)`, `logger.warning(...)`, or `logger.error(...)` based on content.

## Tasks

### Batch 1: Evaluation and Games
- [x] backend/pipeline/evaluation/compare_models_wandb.py
- [ ] backend/pipeline/evaluation/drift_detection.py
- [ ] backend/pipeline/evaluation/eval_ragas.py
- [ ] backend/pipeline/evaluation/regression_benchmark.py
- [ ] backend/pipeline/evaluation/synthetic_gold_generator.py
- [ ] backend/pipeline/games/filter_games.py
- [ ] backend/pipeline/games/ingest_games.py
- [ ] backend/pipeline/games/vectorize_games.py

### Batch 2: Manga
- [ ] backend/pipeline/manga/fetch_covers.py
- [ ] backend/pipeline/manga/filter_manga.py
- [ ] backend/pipeline/manga/ingest_manga.py
- [ ] backend/pipeline/manga/train_vibe_manga.py
- [ ] backend/pipeline/manga/vectorize_manga.py

### Batch 3: MLOps
- [ ] backend/pipeline/mlops/continuous_pretraining.py
- [ ] backend/pipeline/mlops/distillation.py
- [ ] backend/pipeline/mlops/evaluation_metrics.py
- [ ] backend/pipeline/mlops/fandom_lore_scraper.py
- [ ] backend/pipeline/mlops/finetuning_dataset.py
- [ ] backend/pipeline/mlops/graph_healer.py
- [ ] backend/pipeline/mlops/index_otaku_knowledge.py
- [ ] backend/pipeline/mlops/latent_space_viz.py
- [ ] backend/pipeline/mlops/merge_lora_weights.py
- [ ] backend/pipeline/mlops/remote_train_expert.py
- [ ] backend/pipeline/mlops/rlhf_pipeline.py
- [ ] backend/pipeline/mlops/test_expert_model.py
- [ ] backend/pipeline/mlops/train_expert_model.py

### Batch 4: Movies, Pipeline Root and Others
- [ ] backend/pipeline/movies/1_ingest_movies.py
- [ ] backend/pipeline/movies/3_filter_movies.py
- [ ] backend/pipeline/movies/5_vectorize_movies.py
- [ ] backend/pipeline/movies/6_cross_media_mapping.py
- [ ] backend/pipeline/jikan_enrichment.py
- [ ] backend/pipeline/characters/ingest_characters.py
- [ ] backend/pipeline/enrich_db_scraper.py
- [ ] backend/pipeline/specialized_scrapers.py
- [ ] backend/pipeline/neo4j_sync.py
- [ ] backend/pipeline/data_intelligence.py
