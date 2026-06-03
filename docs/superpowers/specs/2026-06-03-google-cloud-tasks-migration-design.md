# Design Document: Migration from Celery/Redis to Google Cloud Tasks

**Date:** 2026-06-03
**Topic:** Migrating the asynchronous task queue from Celery and Redis to Google Cloud Tasks.

## 1. Goal Description

Transition the background task architecture of Animetix from a stateful Celery Worker + Redis broker system to a serverless, HTTP-triggered system powered by Google Cloud Tasks. 

This saves server resources (scale worker nodes to zero when idle) and aligns with a stateless serverless architecture on Google Cloud Run.

## 2. User Review Required

> [!IMPORTANT]
> - **Local Development:** When `IS_PRODUCTION = False`, tasks are executed immediately and synchronously in the same thread. This simplifies development and unit testing (no need for a running local worker or queue).
> - **Security:** In production, Cloud Tasks triggers the worker endpoint `/api/tasks/run/` using an OIDC token matching the application's service account. Django will verify this token using Google API client libraries.

## 3. Proposed Changes

We will introduce a simple, lightweight tasks framework to replace Celery's task dispatcher and status checking.

### Task Dispatcher & Registry

#### [NEW] [tasks_client.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/tasks_client.py)
This module acts as the entry point for scheduling tasks:
- `enqueue_task(task_name, *args, **kwargs)`: Pushes a task to Google Cloud Tasks in production or executes it synchronously in development.
- Tracks task execution state by updating cache backend (`task_result:<task_id>`) to preserve status polling compatibility for the frontend.

#### [NEW] [tasks_registry.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/tasks_registry.py)
A registry that maps string names to python functions for execution:
- Replaces `@shared_task` decorator with simple registration or maps existing task functions to string identifiers.

### Worker Endpoint

#### [NEW] [tasks_views.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/tasks_views.py)
Declares the HTTP POST endpoint `/api/tasks/run/`:
- Parses `task_name`, `args`, and `kwargs`.
- Validates the Google OIDC token in the `Authorization` header in production.
- Executes the task and returns a success status.
- Handles retries by returning HTTP 500 when exceptions occur, letting Cloud Tasks handle exponential backoffs.

### Views & Setting Updates

#### [MODIFY] [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py)
- Deprecate Celery configuration variables.
- Add Google Cloud Tasks configuration (Queue name, GCP Project ID, Worker Endpoint URL, Service Account email for OIDC).

#### [MODIFY] [urls.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/urls.py)
- Wire up the new `/api/tasks/run/` endpoint.

#### [MODIFY] [views/api.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/views/api.py) and [archetypist.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/api/games/archetypist.py)
- Replace `AsyncResult` logic with reading from Django Cache (`task_result:<task_id>`).
- Replace `.delay(...)` calls with `enqueue_task(...)` or task object methods.

## 4. Verification Plan

### Automated Tests
- Implement unit tests mocking Google Cloud Tasks client and verifying tasks run synchronously in development mode.
- Test endpoint OIDC verification logic and task payload parsing.

### Manual Verification
- Trigger Creative Fusion from the frontend in local development, ensuring image and scenario are generated successfully.
