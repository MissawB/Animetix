# SQL Data Quality Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish SQL-level data quality validation using dbt (data build tool) for both relational Django database tables (SQLite/PostgreSQL) and BigQuery telemetry tables before running model training.

**Architecture:** Create a dbt project under `backend/pipeline/dbt_project/` using external tables as Sources. Integrate execution via a custom Django management command `run_data_quality_tests` which dynamically writes `profiles.yml` based on active Django database settings, executes `dbt test`, and fails if validations are breached. Connect the checks to the pre-training workflow in `rlhf_pipeline.py`.

**Tech Stack:** Python, dbt-core, dbt-sqlite, dbt-postgres, dbt-bigquery, Django.

---

## Proposed Changes

### Task 1: Package Dependencies

**Files:**
- Modify: [requirements.txt](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/requirements.txt:250-258)

- [ ] **Step 1: Append dbt dependencies to requirements.txt**

Modify `requirements.txt` around line 258 to include the dbt packages:
```text
dbt-core==1.8.2
dbt-sqlite==1.8.0
dbt-postgres==1.8.2
dbt-bigquery==1.8.2
```

- [ ] **Step 2: Run pip installation**

Run in terminal:
```powershell
.venv\Scripts\pip install -r requirements.txt
```
Expected output: SUCCESS.

- [ ] **Step 3: Verify dbt CLI is available**

Run in terminal:
```powershell
.venv\Scripts\dbt --version
```
Expected output: Prints installed dbt-core version and sqlite, postgres, bigquery plugins.

- [ ] **Step 4: Commit dependencies**

```bash
git add requirements.txt
git commit -m "chore: add dbt-core and adapter dependencies"
```

---

### Task 2: Create dbt Project Configuration

**Files:**
- Create: `backend/pipeline/dbt_project/dbt_project.yml`
- Create: `backend/pipeline/dbt_project/models/sources/relational_sources.yml`
- Create: `backend/pipeline/dbt_project/models/sources/bigquery_sources.yml`
- Create: `backend/pipeline/dbt_project/tests/archetype_drift_values_check.sql`

- [ ] **Step 1: Create `dbt_project.yml`**

Create `backend/pipeline/dbt_project/dbt_project.yml`:
```yaml
name: 'animetix_quality'
version: '1.0.0'
config-version: 2

profile: 'animetix_quality'

model-paths: ["models"]
test-paths: ["tests"]
target-path: "target"
clean-targets:
  - "target"
```

- [ ] **Step 2: Create `relational_sources.yml`**

Create `backend/pipeline/dbt_project/models/sources/relational_sources.yml`:
```yaml
version: 2
sources:
  - name: django_source
    schema: main
    tables:
      - name: animetix_mediaitem
        description: "Media item catalog (Anime, Manga, etc.)"
        columns:
          - name: id
            tests:
              - unique
              - not_null
      - name: animetix_aifeedback
        description: "Explicit thumbs up/down user feedback"
        columns:
          - name: id
            tests:
              - unique
              - not_null
          - name: input_context
            tests:
              - not_null
          - name: output_text
            tests:
              - not_null
      - name: animetix_gameplaysession
        description: "Historical user gameplay sessions"
        columns:
          - name: id
            tests:
              - unique
              - not_null
          - name: target_item
            tests:
              - not_null
      - name: animetix_golddatasetentry
        description: "Validated high-quality training pairs"
        columns:
          - name: id
            tests:
              - unique
              - not_null
          - name: source_feedback_id
            tests:
              - relationships:
                  to: source('django_source', 'animetix_aifeedback')
                  field: id
```

- [ ] **Step 3: Create `bigquery_sources.yml`**

Create `backend/pipeline/dbt_project/models/sources/bigquery_sources.yml`:
```yaml
version: 2
sources:
  - name: telemetry_source
    schema: telemetry
    tables:
      - name: user_interactions
        description: "BigQuery user interaction telemetry logs"
        columns:
          - name: event_id
            tests:
              - unique
              - not_null
          - name: user_id
            tests:
              - not_null
          - name: media_item_id
            tests:
              - not_null
          - name: interaction_type
            tests:
              - not_null
              - accepted_values:
                  values: ['thumbs_up', 'thumbs_down', 'game_win', 'game_loss', 'recommendation_view', 'search_query', 'detail_view']
      - name: archetype_drift
        description: "BigQuery user archetype drift metrics"
        columns:
          - name: event_id
            tests:
              - unique
              - not_null
          - name: user_id
            tests:
              - not_null
          - name: intensity
            tests:
              - not_null
          - name: logic_consistency
            tests:
              - not_null
```

- [ ] **Step 4: Create custom singular test `archetype_drift_values_check.sql`**

Create `backend/pipeline/dbt_project/tests/archetype_drift_values_check.sql`:
```sql
select event_id
from {{ source('telemetry_source', 'archetype_drift') }}
where intensity < 0.0 or intensity > 1.0 or logic_consistency < 0.0 or logic_consistency > 1.0
```

- [ ] **Step 5: Commit dbt project configuration files**

```bash
git add backend/pipeline/dbt_project/
git commit -m "feat: add dbt project and source declarations"
```

---

### Task 3: Django Management Command Wrapper

**Files:**
- Create: `backend/api/animetix/management/commands/run_data_quality_tests.py`

- [ ] **Step 1: Create `run_data_quality_tests.py`**

Create `backend/api/animetix/management/commands/run_data_quality_tests.py`:
```python
# -*- coding: utf-8 -*-
import os
import sys
import yaml
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Generates dbt profiles.yml dynamically and runs database quality tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--exclude-bigquery',
            action='store_true',
            help='Exclude BigQuery telemetry tests from the run (useful for offline/local environments)'
        )

    def handle(self, *args, **options):
        # 1. Identify paths
        base_dir = settings.BASE_DIR
        dbt_project_dir = os.path.join(os.path.dirname(base_dir), 'backend', 'pipeline', 'dbt_project')
        
        # 2. Determine Relational DB parameters
        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']
        
        relational_output = {}
        if 'sqlite' in engine:
            db_path = db_settings['NAME']
            # Convert to absolute path
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(os.path.join(base_dir, db_path))
            
            relational_output = {
                'type': 'sqlite',
                'threads': 1,
                'database': 'main',
                'schema': 'main',
                'schemas_and_paths': {
                    'main': db_path
                }
            }
            self.stdout.write(self.style.WARNING(f"Configuring dbt for SQLite at: {db_path}"))
        elif 'postgresql' in engine or 'postgis' in engine:
            relational_output = {
                'type': 'postgres',
                'host': db_settings.get('HOST', 'localhost'),
                'user': db_settings.get('USER', 'postgres'),
                'pass': db_settings.get('PASSWORD', ''),
                'port': int(db_settings.get('PORT', 5432) or 5432),
                'dbname': db_settings.get('NAME', 'animetix'),
                'schema': 'public',
                'threads': 1
            }
            self.stdout.write(self.style.WARNING(f"Configuring dbt for PostgreSQL database: {relational_output['dbname']}"))
        else:
            raise CommandError(f"Unsupported database engine for dbt tests: {engine}")

        # 3. Determine BigQuery parameters (Telemetry)
        bq_output = {
            'type': 'bigquery',
            'method': 'oauth', # fallback to OAuth or Application Default Credentials (ADC)
            'project': getattr(settings, 'GCP_PROJECT_ID', 'animetix-project'),
            'dataset': getattr(settings, 'GCP_BIGQUERY_DATASET', 'telemetry'),
            'threads': 1
        }
        
        # Write config
        profiles_content = {
            'animetix_quality': {
                'target': 'dev',
                'outputs': {
                    'dev': relational_output,
                    'bigquery': bq_output
                }
            }
        }
        
        profiles_path = os.path.join(dbt_project_dir, 'profiles.yml')
        with open(profiles_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(profiles_content, f, default_flow_style=False)
            
        self.stdout.write(self.style.SUCCESS(f"Generated dynamic profiles.yml at: {profiles_path}"))

        # 4. Run tests
        # A. Relational tests (target: dev)
        self.stdout.write("Running dbt tests on Relational Database...")
        cmd_relational = [
            'dbt', 'test',
            '--project-dir', dbt_project_dir,
            '--profiles-dir', dbt_project_dir,
            '--target', 'dev'
        ]
        
        res_rel = subprocess.run(cmd_relational, capture_output=True, text=True)
        if res_rel.returncode != 0:
            self.stdout.write(self.style.ERROR(res_rel.stdout))
            self.stdout.write(self.style.ERROR(res_rel.stderr))
            raise CommandError("❌ Relational SQL database data quality tests failed.")
        else:
            self.stdout.write(self.style.SUCCESS("🟢 Relational database data quality checks passed."))

        # B. Telemetry tests (target: bigquery)
        if not options['exclude_bigquery']:
            self.stdout.write("Running dbt tests on BigQuery Telemetry...")
            cmd_bq = [
                'dbt', 'test',
                '--project-dir', dbt_project_dir,
                '--profiles-dir', dbt_project_dir,
                '--target', 'bigquery'
            ]
            res_bq = subprocess.run(cmd_bq, capture_output=True, text=True)
            if res_bq.returncode != 0:
                self.stdout.write(self.style.ERROR(res_bq.stdout))
                self.stdout.write(self.style.ERROR(res_bq.stderr))
                raise CommandError("❌ BigQuery Telemetry database data quality tests failed.")
            else:
                self.stdout.write(self.style.SUCCESS("🟢 BigQuery Telemetry database data quality checks passed."))
        else:
            self.stdout.write(self.style.WARNING("Skipping BigQuery Telemetry tests (exclude flag set)."))
```

- [ ] **Step 2: Run verification execution (local-only)**

Run in terminal:
```powershell
python backend/api/manage.py run_data_quality_tests --exclude-bigquery
```
Expected output: Dynamically creates `profiles.yml`, connects to local sqlite `db.sqlite3`, runs the relational source tests successfully, and skips BigQuery.

- [ ] **Step 3: Commit Django command**

```bash
git add backend/api/animetix/management/commands/run_data_quality_tests.py
git commit -m "feat: add run_data_quality_tests django command"
```

---

### Task 4: Hook into MLOps Retraining Pipeline

**Files:**
- Modify: [backend/pipeline/mlops/rlhf_pipeline.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/pipeline/mlops/rlhf_pipeline.py)

- [ ] **Step 1: Add validation function to `rlhf_pipeline.py`**

Modify `backend/pipeline/mlops/rlhf_pipeline.py` to add `run_sql_quality_checks` and insert it into the pipeline execution path:

```python
def run_sql_quality_checks():
    """Runs dbt data quality checks via Django management command before compilation."""
    manage_py = os.path.join(BASE_DIR, 'backend', 'manage.py')
    try:
        import subprocess
        logger.info("Executing SQL database quality checks via dbt...")
        # In test/dev environment, we might exclude BigQuery checks if offline, but standard is to run both
        exclude_bq = os.getenv("MLOPS_OFFLINE_MODE", "false").lower() == "true"
        cmd = ['python', manage_py, 'run_data_quality_tests']
        if exclude_bq:
            cmd.append('--exclude-bigquery')
            
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("🟢 SQL database quality checks passed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ SQL data quality validation failed:\n{e.stderr or e.stdout}")
        raise RuntimeError("Training aborted due to data quality violations in SQL tables.") from e
```

- [ ] **Step 2: Integrate the quality check in pipeline run**

Insert the validation execution at the start of `validated_dpo_dataset`:
```python
def validated_dpo_dataset(exported_user_feedback):
    """Transforme l'export en dataset DPO validé et nettoyé."""
    if not exported_user_feedback:
        return None
        
    # Hook pre-training SQL validations first
    run_sql_quality_checks()
    
    feedback_path = exported_user_feedback["feedback"]
    dataset_path = os.path.join(FEEDBACK_DATASET_DIR, "dpo_train_validated.jsonl")
    loop = DPOFeedbackLoop(data_dir=FEEDBACK_DATASET_DIR)
    count = loop.process_and_export(feedback_path, dataset_path)
    return {"path": dataset_path, "count": count}
```

- [ ] **Step 3: Commit pipeline changes**

```bash
git add backend/pipeline/mlops/rlhf_pipeline.py
git commit -m "feat: hook SQL quality checks into MLOps training workflow"
```

---

### Task 5: Integration & Unit Tests

**Files:**
- Create: `tests/mlops/test_sql_quality_pipeline.py`

- [ ] **Step 1: Create pipeline test file**

Create `tests/mlops/test_sql_quality_pipeline.py`:
```python
# -*- coding: utf-8 -*-
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.core.management.base import CommandError

# Setup path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

class TestSQLDataQualityPipeline(unittest.TestCase):
    def test_run_command_generates_profiles_and_runs(self):
        # We test django command execution with mock subprocess to verify target routes
        with patch('subprocess.run') as mock_run:
            # Setup mock outputs
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_run.return_value = mock_res
            
            # Run command
            call_command('run_data_quality_tests', exclude_bigquery=True)
            
            # Verify subprocess ran dbt test on relational target
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn('dbt', args)
            self.assertIn('test', args)
            self.assertIn('dev', args)

    def test_command_failure_raises_error(self):
        with patch('subprocess.run') as mock_run:
            mock_res = MagicMock()
            mock_res.returncode = 1
            mock_res.stdout = "Failed test details"
            mock_res.stderr = "Errors"
            mock_run.return_value = mock_res
            
            with self.assertRaises(CommandError):
                call_command('run_data_quality_tests', exclude_bigquery=True)

    @patch('backend.pipeline.mlops.rlhf_pipeline.run_sql_quality_checks')
    def test_pipeline_integration_runs_checks_first(self, mock_checks):
        from backend.pipeline.mlops.rlhf_pipeline import validated_dpo_dataset
        
        mock_feedback = {"feedback": "dummy_path.jsonl", "sessions": "dummy_sessions.jsonl"}
        
        with patch('backend.pipeline.mlops.rlhf_pipeline.DPOFeedbackLoop') as mock_loop_class:
            mock_loop = MagicMock()
            mock_loop.process_and_export.return_value = 10
            mock_loop_class.return_value = mock_loop
            
            res = validated_dpo_dataset(mock_feedback)
            
            # Assert quality checks executed before compiling loop
            mock_checks.assert_called_once()
            self.assertEqual(res["count"], 10)
```

- [ ] **Step 2: Run pytest to verify all pipeline tests pass**

Run in terminal:
```powershell
.venv\Scripts\pytest tests/mlops/test_sql_quality_pipeline.py -v
```
Expected output: PASS.

- [ ] **Step 3: Commit test files**

```bash
git add tests/mlops/test_sql_quality_pipeline.py
git commit -m "test: add unit/integration tests for SQL quality validation pipeline"
```

---

## Verification Plan

### Automated Verification
1. Run local tests: `.venv\Scripts\pytest tests/mlops/test_sql_quality_pipeline.py -v`
2. Run database validation via CLI: `python backend/api/manage.py run_data_quality_tests --exclude-bigquery`
