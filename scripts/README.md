# Scripts Repository

This directory contains various utility scripts, benchmark tools, curation helpers, and deployment utilities used in the Animetix project.

## Directory Structure

```
scripts/
├── archive/        # One-off scripts archived to avoid cluttering curation/
├── benchmark/      # Latency, compiler, and ingestion quality benchmarking tools
├── curation/       # Active dataset curation, translations, and database tools
├── deploy/         # Cloudflare, GCP, and Hugging Face deployment scripts
├── verify/         # SSRF, API, and cloud environment validation scripts
└── root/           # Core command-line runners and drift detection scripts
```

## Description of Scripts

### Root Scripts

- **`detect_embedding_drift.py`**: Monitors and alerts on embedding drifts for vector index health.
- **`run_cmd.py`**: Cross-platform task runner used by Git pre-commit hooks to run linter/formatters.
- **`run_in_venv.py`**: Executes shell commands and scripts within the active poetry/pip virtual environment.
- **`sync_api.py`**: Synchronizes API schemas between backend code changes and frontend code generator outputs.

### curation/ (Active Curation)

- **`compare_translations.py`**: Asserts 100% key parity between English (`en.json`) and French (`fr.json`) i18n files.
- **`compile_translations.py`**: Utility to compile and aggregate translations.
- **`curate_dpo_dataset.py`**: Pipeline tool used in the DPO feedback loop to curate training pairs.
- **`vision_quest_worker.py`**: Active background worker that processes vision task queues.

### verify/ (Verification & Auditing)

- **`audit_combat_data.py` / `verify_combat_data.py`**: Auditing scripts to assert relational integrity of battle data.
- **`audit_dead_services.py`**: Detects and reports unused/obsolete service patterns or API handlers.
- **`check_completion.py`**: Validates task state and pipeline completion status.
- **`pre_flight_check.py`**: Multi-check runner executed prior to production deployments.
- **`rag_smoke_test.py`**: Verifies basic availability and response patterns of the agentic RAG stack.
- **`verify_brain_adapter.py`**: Sanity-tests communication channels with the remote Brain inference API.
- **`verify_cloud_env.py`**: Validates GCP secret strings, keys, environment variables, and SDK setups.
- **`verify_container_modularization.py`**: Verifies container boundary boundaries and configurations.
- **`verify_ssrf_hardening.py`**: Validates request filter behavior to protect internal endpoints against SSRF.

### benchmark/ (Performance Benchmarking)

- **`analyze_ingestion_quality.py`**: Measures precision and quality metrics of document ingestion steps.
- **`benchmark_compiler_numba.py`**: Validates speed gains from Numba-compiled math and vector helper functions.
- **`benchmark_latency.py` / `benchmark_quality_v2.py`**: Performance tools measuring API endpoint response times and query accuracy.
- **`large_function_scan.py`**: Static analysis helper that flags overly complex or long functions.

### deploy/ (Deployments)

- **`cloudflare/`**: Cloudflare proxy configurations (`wrangler.toml`, routing rules).
- **`gcp/`**: Deployments on Google Cloud (Cloud Run instance builders, CDN, Cloud Tasks setup, budget monitors).
- **`huggingface/`**: Hugging Face endpoint management, adapter/gold-dataset uploads, and model registry syncing.

### archive/ (Archived One-offs)

- **`add_prompt.py` / `fix_prompt.py`**: Used for one-off additions or structural fixes to registry prompt rows.
- **`fix_adapters_batch.py`**: Fixed properties/attributes across batched repository adaptors.
- **`merge_translation_fragments.py`**: Merged translation chunks during major i18n refactoring.
- **`migrate_gold_set.py`**: Migrated gold test sets to modern database storage schemas.
- **`find_duplicates.py`**: Ran static duplicates check across raw datasets.
- **`fix_gold_set.ps1`**: Ran a PowerShell one-off fix for local gold dataset files.
