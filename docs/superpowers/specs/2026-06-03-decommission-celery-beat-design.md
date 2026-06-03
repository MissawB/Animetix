# Design Document: Decommissioning Celery Beat to Cloud Run Jobs

**Date:** 2026-06-03
**Topic:** Decommissioning Celery Beat scheduler and migrating all periodic tasks to Google Cloud Run Jobs + Cloud Scheduler.

## 1. Architecture Overview

To transition our periodic/scheduled tasks from a stateful container-based Celery Beat model to a modern serverless model, we will:
1.  **Decommission Celery Beat:** Remove Celery Beat from local development (`docker-compose.yml`) and production supervisord configuration (`supervisord.conf`).
2.  **Expose Tasks as Django Commands:** Implement a unified Django management command (`run_scheduled_task`) to run any of the scheduled task workflows from the command line.
3.  **Deploy Cloud Run Jobs:** Define a job for each task on Google Cloud Run.
4.  **Schedule Jobs:** Wire up Google Cloud Scheduler to trigger each Cloud Run Job using POST requests at the designated cron schedules.

This guarantees:
-   **No Duplicate Runs:** Multiple web container instances will not result in multiple scheduler processes triggering duplicate tasks.
-   **Scale to Zero:** Compute resources are allocated only during execution of the specific task, saving costs.
-   **Console Visibility:** Standardized and detailed job logs, execution histories, and alerts in the Google Cloud Console.

## 2. Component Design

### 2.1. Django Management Command
A new Django management command will be added at `backend/api/animetix/management/commands/run_scheduled_task.py`.
It will take a positional argument `task_key` (e.g., `daily-data-ingestion`) and invoke the corresponding pipeline function or Celery task logic synchronously:
-   `dpo-optimization-daily` -> `scheduled_dpo_optimization()`
-   `daily-data-ingestion` -> `run_daily_ingestion_workflow()`
-   `daily-maintenance-mlops` -> `run_daily_maintenance_workflow()`
-   `hourly-health-monitoring` -> `run_hourly_monitoring_workflow()`
-   `gold-dataset-lora-sensor` -> `check_gold_dataset_sensor_task()`
-   `gold-dataset-dpo-sensor` -> `check_dpo_feedback_sensor_task()`

### 2.2. DPO Task Re-implementation
The DPO task `scheduled_dpo_optimization` will be re-added to `backend/api/animetix/tasks/meta_tasks.py` to identify negative sitemaps or low-performing prompts, optimize them via the DPO feedback loop using DSPy, and persist improvements.

### 2.3. Celery Beat Cleanup
We will:
-   Remove `celery_beat` program from `deploy/supervisord.conf`.
-   Remove `celery_beat` service from `deploy/docker-compose.yml`.
-   Comment out `CELERY_BEAT_SCHEDULE` in `backend/api/animetix_project/settings.py` with documentation pointing to the new Cloud Run Jobs architecture.

### 2.4. Refactoring `deploy_jobs.py`
The deployment automation script `scripts/deploy/deploy_jobs.py` will be modified to define a list of scheduled jobs, their configurations, memory limits, and schedules:
-   `animetix-sync-catalog` (`0 2 * * *`)
-   `animetix-dpo-optimization` (`0 3 * * *`)
-   `animetix-data-ingestion` (`0 3 * * *`)
-   `animetix-maintenance-mlops` (`0 5 * * *`)
-   `animetix-health-monitoring` (`0 * * * *`)
-   `animetix-lora-sensor` (`*/10 * * * *`)
-   `animetix-dpo-sensor` (`*/10 * * * *`)

The script will idempotently create/update each Cloud Run Job and its corresponding Cloud Scheduler HTTP trigger.

## 3. Data Flow

1.  **Cloud Scheduler Trigger:** Fires HTTP POST request -> Cloud Run `:run` API (authenticated via Service Account OIDC token).
2.  **Cloud Run Job Execution:** Launches container -> runs `python backend/api/manage.py run_scheduled_task <task_key>`.
3.  **Database Connection:** Connects to PostgreSQL (pgvector) via Cloud SQL Auth Proxy / Unix socket.
4.  **Completion/Logging:** Container exits -> logs output to Cloud Logging -> status reported back to Scheduler history.

## 4. Testing Strategy

-   **Manual Command Verification:** Run `python manage.py run_scheduled_task <key>` locally to ensure execution logic works correctly without Celery.
-   **Unit Tests:** Implement unit tests for the `run_scheduled_task` command to verify correct dispatch and error handling.
-   **Deployment Dry-run:** Validate `deploy_jobs.py` runs cleanly and prints the corresponding gcloud commands.

## 5. Success Criteria

-   Celery Beat scheduler process is deleted from development/production.
-   All 7 recurring tasks are registered as Cloud Run Jobs.
-   Corresponding Cloud Scheduler cron jobs trigger the executions.
