# Google Cloud Tasks Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Celery Worker + Redis broker system with Google Cloud Tasks to execute background tasks asynchronously via HTTP POST requests in production, and synchronously in development mode.

**Architecture:** 
- A unified registry (`tasks_registry.py`) mapping task names to python functions.
- A HTTP client (`tasks_client.py`) pushing tasks to GCP Cloud Tasks in production or executing them immediately in development.
- A HTTP POST handler `/api/tasks/run/` (`tasks_views.py`) that executes requested tasks from Google Cloud Tasks.
- Preservation of task status polling via Django Cache backend (`task_result:<task_id>`).

**Tech Stack:** Django, google-cloud-tasks, google-auth, Django Cache (Redis/LocMem)

---

### Task 1: Add Tasks Registry

**Files:**
- Create: `backend/api/animetix/tasks_registry.py`
- Test: `tests/api/animetix/test_tasks_registry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/api/animetix/test_tasks_registry.py`:
```python
import pytest
from animetix.tasks_registry import get_registered_task, register_task

def test_registry_registration():
    @register_task("dummy_task")
    def dummy_func(x):
        return x * 2

    assert get_registered_task("dummy_task") == dummy_func
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/animetix/test_tasks_registry.py -v`
Expected: FAIL with Import Error / Registry module missing

- [ ] **Step 3: Write minimal registry implementation**

Create `backend/api/animetix/tasks_registry.py`:
```python
import functools

TASK_REGISTRY = {}

def register_task(name):
    def decorator(func):
        TASK_REGISTRY[name] = func
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_registered_task(name):
    return TASK_REGISTRY.get(name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/animetix/test_tasks_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add backend/api/animetix/tasks_registry.py tests/api/animetix/test_tasks_registry.py
git commit -m "feat: add task registry mapping strings to tasks"
```

---

### Task 2: Implement Task Client and Cache Storage

**Files:**
- Create: `backend/api/animetix/tasks_client.py`
- Test: `tests/api/animetix/test_tasks_client.py`

- [ ] **Step 1: Write the failing test**

Create `tests/api/animetix/test_tasks_client.py`:
```python
import pytest
from django.core.cache import cache
from animetix.tasks_client import enqueue_task
from animetix.tasks_registry import register_task

@pytest.fixture(autouse=True)
def cleanup_cache():
    cache.clear()

def test_enqueue_task_eager_local(settings):
    settings.IS_PRODUCTION = False
    
    @register_task("test_eager_task")
    def sample_task(x, y):
        return x + y

    task_id = enqueue_task("test_eager_task", 10, y=20)
    assert task_id is not None
    
    # Verify execution state saved in cache
    result = cache.get(f"task_result:{task_id}")
    assert result is not None
    assert result["ready"] is True
    assert result["result"] == 30
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/animetix/test_tasks_client.py -v`
Expected: FAIL (No tasks_client.py module)

- [ ] **Step 3: Write tasks client implementation**

Create `backend/api/animetix/tasks_client.py`:
```python
import uuid
import json
from django.conf import settings
from django.core.cache import cache
from animetix.logging_config import get_logger
from animetix.tasks_registry import get_registered_task

logger = get_logger("animetix." + __name__)

def enqueue_task(task_name, *args, **kwargs):
    task_id = str(uuid.uuid4())
    
    # Store initial state
    cache.set(f"task_result:{task_id}", {"ready": False, "result": None, "state": "PENDING"}, timeout=86400)
    
    is_prod = getattr(settings, 'IS_PRODUCTION', False)
    
    if not is_prod:
        # Run synchronously in development/test
        logger.info(f"Running task {task_name} eagerly (dev/test environment)")
        task_func = get_registered_task(task_name)
        if not task_func:
            error_msg = f"Task {task_name} not registered in TASK_REGISTRY"
            logger.error(error_msg)
            cache.set(f"task_result:{task_id}", {"ready": True, "result": {"error": error_msg}, "state": "FAILURE"}, timeout=86400)
            return task_id
            
        try:
            res = task_func(*args, **kwargs)
            cache.set(f"task_result:{task_id}", {"ready": True, "result": res, "state": "SUCCESS"}, timeout=86400)
        except Exception as e:
            logger.exception(f"Error executing task {task_name} eagerly")
            cache.set(f"task_result:{task_id}", {"ready": True, "result": {"error": str(e)}, "state": "FAILURE"}, timeout=86400)
        return task_id
        
    else:
        # Push to Google Cloud Tasks in production
        from google.cloud import tasks_v2
        
        project = settings.GCP_PROJECT_ID
        queue = settings.GCP_TASKS_QUEUE_NAME
        location = settings.GCP_TASKS_LOCATION
        url = settings.GCP_TASKS_WORKER_URL
        service_account = settings.GCP_TASKS_SERVICE_ACCOUNT
        
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        
        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs
        }
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": url,
                "headers": {"Content-type": "application/json"},
                "body": json.dumps(payload).encode("utf-8"),
                "oidc_token": {
                    "service_account_email": service_account,
                    "audience": url
                }
            }
        }
        
        logger.info(f"Enqueuing task {task_name} to Google Cloud Tasks queue {queue}")
        client.create_task(request={"parent": parent, "task": task})
        return task_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/animetix/test_tasks_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add backend/api/animetix/tasks_client.py tests/api/animetix/test_tasks_client.py
git commit -m "feat: implement tasks_client supporting local eager execution and production Cloud Tasks dispatcher"
```

---

### Task 3: Implement HTTP POST Worker Endpoint

**Files:**
- Create: `backend/api/animetix/tasks_views.py`
- Test: `tests/api/animetix/test_tasks_views.py`

- [ ] **Step 1: Write the failing test**

Create `tests/api/animetix/test_tasks_views.py`:
```python
import pytest
import json
from django.urls import reverse
from rest_framework import status
from django.core.cache import cache
from animetix.tasks_registry import register_task

@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()

@pytest.mark.django_db
def test_worker_run_task_endpoint_local(client, settings):
    settings.IS_PRODUCTION = False
    
    @register_task("endpoint_test_task")
    def sum_task(a, b):
        return a + b
        
    url = "/api/tasks/run/"
    payload = {
        "task_id": "test-task-123",
        "task_name": "endpoint_test_task",
        "args": [15, 25],
        "kwargs": {}
    }
    
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Check cache status
    cached = cache.get("task_result:test-task-123")
    assert cached["ready"] is True
    assert cached["result"] == 40
    assert cached["state"] == "SUCCESS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/animetix/test_tasks_views.py -v`
Expected: FAIL (URL or View not found)

- [ ] **Step 3: Implement the worker endpoint view**

Create `backend/api/animetix/tasks_views.py`:
```python
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from animetix.tasks_registry import get_registered_task
from animetix.logging_config import get_logger

logger = get_logger("animetix." + __name__)

@csrf_exempt
def run_task_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    # OIDC verification in production
    is_prod = getattr(settings, 'IS_PRODUCTION', False)
    if is_prod:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Missing or invalid authorization header"}, status=401)
        
        token = auth_header.split(" ")[1]
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests
            # Verify the token against Google
            audience = settings.GCP_TASKS_WORKER_URL
            id_token.verify_oauth2_token(token, requests.Request(), audience=audience)
        except Exception as e:
            logger.error(f"OIDC token verification failed: {e}")
            return JsonResponse({"error": "Invalid OIDC token"}, status=403)

    try:
        data = json.loads(request.body)
        task_id = data.get("task_id")
        task_name = data.get("task_name")
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})
    except Exception as parse_err:
        logger.error(f"Failed to parse task payload: {parse_err}")
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    if not task_id or not task_name:
        return JsonResponse({"error": "task_id and task_name are required"}, status=400)

    task_func = get_registered_task(task_name)
    if not task_func:
        error_msg = f"Task {task_name} is not registered in the system."
        logger.error(error_msg)
        cache.set(f"task_result:{task_id}", {"ready": True, "result": {"error": error_msg}, "state": "FAILURE"}, timeout=86400)
        return JsonResponse({"error": error_msg}, status=400)

    logger.info(f"Running task {task_name} (ID: {task_id}) via worker endpoint.")
    cache.set(f"task_result:{task_id}", {"ready": False, "result": None, "state": "RUNNING"}, timeout=86400)

    try:
        res = task_func(*args, **kwargs)
        cache.set(f"task_result:{task_id}", {"ready": True, "result": res, "state": "SUCCESS"}, timeout=86400)
        return JsonResponse({"status": "success", "task_id": task_id})
    except Exception as run_err:
        logger.exception(f"Error running task {task_name} (ID: {task_id})")
        cache.set(f"task_result:{task_id}", {"ready": True, "result": {"error": str(run_err)}, "state": "FAILURE"}, timeout=86400)
        # Return 500 so Google Cloud Tasks knows to retry
        return JsonResponse({"error": str(run_err)}, status=500)
```

- [ ] **Step 4: Configure URLs to include `/api/tasks/run/`**

Modify `backend/api/animetix_project/urls.py` by adding the route mapping to `run_task_view`:
```python
from animetix.tasks_views import run_task_view
# Add in urlpatterns:
# path('api/tasks/run/', run_task_view, name='run_task_view'),
```

- [ ] **Step 5: Run tests to verify all passes**

Run: `pytest tests/api/animetix/test_tasks_views.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

Run:
```bash
git add backend/api/animetix/tasks_views.py tests/api/animetix/test_tasks_views.py backend/api/animetix_project/urls.py
git commit -m "feat: implement /api/tasks/run/ HTTP POST worker endpoint with OIDC verification"
```

---

### Task 4: Register Tasks and Update Callsites

**Files:**
- Modify: `backend/api/animetix/tasks/__init__.py`
- Modify: `backend/api/animetix/creative_tasks.py`
- Modify: `backend/api/animetix/views/api.py`
- Modify: `backend/api/animetix/api/games/archetypist.py`

- [ ] **Step 1: Register existing Celery tasks**

Add `@register_task` decorators to all async functions in `backend/api/animetix/tasks/__init__.py` and `backend/api/animetix/creative_tasks.py`.
Import `@register_task` from `animetix.tasks_registry` at the top of these files.

- [ ] **Step 2: Replace `.delay(...)` calls and AsyncResult checks**

Modify `backend/api/animetix/api/games/archetypist.py`:
- Replace `task = chain(...).delay()` with a series of calls or map chain execution. Since Cloud Tasks doesn't natively support celery chains, we will create a composite task/workflow name or execute them sequentially.
- Let's register a composite task `generate_fusion_flow_task(media_type, item1, item2, language, chaos_level, universe_balance, art_style)` which does:
  ```python
  scenario = generate_fusion_scenario_task(media_type, item1, item2, language, chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style)
  result = generate_fusion_image_task(scenario, item1, item2, art_style=art_style)
  return result
  ```
  This is much cleaner than celery chaining!
- Replace the dispatch logic:
  ```python
  from animetix.tasks_client import enqueue_task
  task_id = enqueue_task(
      "generate_fusion_flow_task",
      media_type, item1, item2, language,
      chaos_level=chaos_level, universe_balance=universe_balance, art_style=art_style
  )
  ```
- In `ArchetypistTaskStatusView` check status from cache:
  ```python
  from django.core.cache import cache
  task_data = cache.get(f"task_result:{task_id}")
  # If task_data is not None:
  # task_ready = task_data.get("ready")
  # task_result = task_data.get("result")
  ```

Modify `backend/api/animetix/views/api.py`:
- In `get_task_status`, replace `AsyncResult` with Cache lookup:
  ```python
  task_data = cache.get(f"task_result:{task_id}")
  # If task_data and task_data.get("ready"):
  # result = task_data.get("result")
  ```

Modify callsites:
- `backend/core/domain/services/star_reasoner_service.py` line 63: replace `.delay()` with `enqueue_task("run_star_training_cycle_task")`
- `backend/api/animetix/signals.py` line 99: replace `.delay(...)` with `enqueue_task("sync_media_item_task", ...)`
- `backend/api/animetix/tasks/pipeline_tasks.py` line 283: replace `.delay()` with `enqueue_task("run_star_training_cycle_task")`
- `backend/adapters/mlops_adapter.py` line 10: replace `.delay(...)` with `enqueue_task("log_dpo_preference_task", ...)`
- `backend/api/animetix/api/social.py` line 97: replace `.delay(...)` with `enqueue_task("trigger_club_event", ...)`

- [ ] **Step 3: Run pytest to verify execution flow**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 4: Commit**

Run:
```bash
git add -u
git commit -m "refactor: replace Celery delay and status calls with task client and cache lookups"
```

---

### Task 5: Settings Cleanup

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Comment/Remove Celery Beat and Redis Broker configs**

Update configuration variables:
- Add Google Cloud Tasks configuration settings block:
```python
GCP_PROJECT_ID = env('GOOGLE_CLOUD_PROJECT', default='animetix')
GCP_TASKS_QUEUE_NAME = env('GCP_TASKS_QUEUE_NAME', default='animetix-queue')
GCP_TASKS_LOCATION = env('GCP_TASKS_LOCATION', default='europe-west1')
GCP_TASKS_WORKER_URL = env('GCP_TASKS_WORKER_URL', default='https://missawb-animetix-web.hf.space/api/tasks/run/')
GCP_TASKS_SERVICE_ACCOUNT = env('GCP_TASKS_SERVICE_ACCOUNT', default='animetix-tasks-invoker@animetix.iam.gserviceaccount.com')
```
- Remove Celery default imports or integrations if no longer used.

- [ ] **Step 2: Commit changes**

Run:
```bash
git add backend/api/animetix_project/settings.py
git commit -m "config: configure Google Cloud Tasks variables and clean up Celery configs"
```
