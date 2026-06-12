# SQL-Level Data Quality Testing Design Specification

This specification designs the integration of SQL-level data quality testing using a unified `dbt` project. The tests will validate relational tables (SQLite/PostgreSQL) and telemetry tables (BigQuery) before compiling datasets for model training.

## 1. Objectives

1. Ensure the training data does not contain duplicates, orphaned records, or format anomalies at the database level.
2. Automate schema checks, uniqueness constraints, and referential integrity validations.
3. Keep database credentials out of source control using a dynamic profile generator in a Django management command.
4. Block model retraining in the MLOps pipeline (`rlhf_pipeline.py`) if database tests fail.

---

## 2. Directory Structure & Dependencies

### Dependencies
The following dependencies will be installed in the project's virtual environment:
* `dbt-core` (dbt framework)
* `dbt-sqlite` (SQLite database adapter)
* `dbt-postgres` (PostgreSQL/AlloyDB database adapter)
* `dbt-bigquery` (BigQuery database adapter)

### Files to Create
All dbt-related assets will reside in:
```
backend/pipeline/dbt_project/
├── dbt_project.yml
├── profiles.yml (Generated dynamically; ignored in .gitignore)
└── models/
    └── sources/
        ├── relational_sources.yml
        └── bigquery_sources.yml
```

---

## 3. Test Definitions

### 3.1 Relational Database (`relational_sources.yml`)
Tests targets:
* **`animetix_mediaitem`**:
  * `id`: Must be `unique` and `not_null`.
* **`animetix_aifeedback`**:
  * `id`: Must be `unique` and `not_null`.
  * `input_context`: Must be `not_null` and not blank.
  * `output_text`: Must be `not_null` and not blank.
* **`animetix_gameplaysession`**:
  * `id`: Must be `unique` and `not_null`.
  * `target_item`: Must be `not_null`.
* **`animetix_golddatasetentry`**:
  * `id`: Must be `unique` and `not_null`.
  * `source_feedback_id`: Referential integrity relationship pointing to `animetix_aifeedback.id`.

### 3.2 BigQuery Telemetry (`bigquery_sources.yml`)
Tests targets:
* **`user_interactions`**:
  * `event_id`: Must be `unique` and `not_null`.
  * `user_id`: Must be `not_null`.
  * `media_item_id`: Must be `not_null`.
  * `interaction_type`: Must be one of `thumbs_up`, `thumbs_down`, `game_win`, `game_loss`.
* **`archetype_drift`**:
  * `event_id`: Must be `unique` and `not_null`.
  * `user_id`: Must be `not_null`.
  * `intensity` & `logic_consistency`: Must be `not_null` and within `0.0` to `1.0` (validated using a custom SQL test).

---

## 4. Execution Workflow

### 4.1 Django Management Command
A custom command `run_data_quality_tests` will:
1. Inspect the default Django connection settings to identify the active database engine (SQLite or PostgreSQL).
2. Generate a `profiles.yml` file matching the settings dynamically.
3. Configure the BigQuery credentials based on Application Default Credentials (ADC) or environmental secrets.
4. Execute `dbt test` programmatically.
5. Exit with status `0` on success or exit with `1` and print failures if tests fail.

### 4.2 Pipeline Hook
In `backend/pipeline/mlops/rlhf_pipeline.py`, a pre-flight hook will call the Django command before compilation. If execution fails, retraining is aborted.

---

## 5. Verification Plan

### Automated Verification
* Run Django management command: `python backend/api/manage.py run_data_quality_tests`.
* Run MLOps pipeline validation step: `pytest tests/mlops/test_sql_quality_pipeline.py`.
* Force duplicate / null anomalies in a test database and verify the command fails.
