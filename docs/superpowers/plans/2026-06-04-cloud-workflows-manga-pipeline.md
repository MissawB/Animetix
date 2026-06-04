# Cloud Workflows Manga-Voice Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Google Cloud Workflows serverless pipeline that orchestrates Manga OCR, LLM Translation, and XTTS voice synthesis, uploading the resulting audio to GCS and returning the results to Django asynchronoulsy.

**Architecture:** A client triggers a GCP Workflow execution. A Cloud Task polls the execution status and updates the Django cache. Local development falls back to synchronous mock/local execution.

**Tech Stack:** Python, Django, FastAPI, google-cloud-workflows, Google Cloud Tasks, GCS, Pytest.

---

### Task 1: Django Settings Configuration

**Files:**
- Modify: `backend/api/animetix_project/settings.py`
- Test: `tests/backend/test_settings.py`

- [ ] **Step 1: Write a failing test for settings configuration**

Create `tests/backend/test_settings.py`:
```python
from django.conf import settings

def test_gcp_workflows_settings():
    assert hasattr(settings, 'GCP_WORKFLOW_ID')
    assert settings.GCP_WORKFLOW_ID == 'manga-voice-pipeline'
    assert hasattr(settings, 'GCP_LOCATION')
    assert settings.GCP_LOCATION == 'europe-west1'
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_settings.py -v
```
Expected: Fail with `AssertionError` or `AttributeError`.

- [ ] **Step 3: Add configuration to settings.py**

Modify `backend/api/animetix_project/settings.py` by adding the following settings:
```python
# GCP Workflows configuration
GCP_WORKFLOW_ID = env('GCP_WORKFLOW_ID', default='manga-voice-pipeline')
GCP_LOCATION = env('GCP_LOCATION', default='europe-west1')
GCS_MEDIA_BUCKET = env('GCS_MEDIA_BUCKET', default='animetix-media-bucket')
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_settings.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix_project/settings.py tests/backend/test_settings.py
git commit -m "feat: configure GCP Workflows Django settings"
```

---

### Task 2: Implement GCPWorkflowsClient

**Files:**
- Create: `backend/adapters/inference/workflows_client.py`
- Test: `tests/core/test_workflows_client.py`

- [ ] **Step 1: Write a test mocking GCP Workflows execution client**

Create `tests/core/test_workflows_client.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from adapters.inference.workflows_client import GCPWorkflowsClient

@patch('adapters.inference.workflows_client.ExecutionsClient')
def test_workflows_client_trigger_and_status(mock_executions_client):
    mock_instance = MagicMock()
    mock_executions_client.return_value = mock_instance
    
    mock_exec_response = MagicMock()
    mock_exec_response.name = "projects/test-proj/locations/test-loc/workflows/test-wf/executions/exec-123"
    mock_instance.create_execution.return_value = mock_exec_response
    
    mock_status_response = MagicMock()
    mock_status_response.state = 2 # SUCCEEDED
    mock_status_response.result = '{"status": "success", "translated_text": "Bonjour", "audio_url": "http://gcs/audio.wav"}'
    mock_status_response.error = None
    mock_instance.get_execution.return_value = mock_status_response

    client = GCPWorkflowsClient()
    client.project_id = "test-proj"
    client.parent = "projects/test-proj/locations/europe-west1/workflows/manga-voice-pipeline"
    
    exec_name = client.trigger_pipeline("img_b64", "audio_b64", "French", "out.wav")
    assert exec_name == "projects/test-proj/locations/test-loc/workflows/test-wf/executions/exec-123"
    
    status = client.get_execution_status(exec_name)
    assert status["state"] == "SUCCEEDED"
    assert status["result"]["translated_text"] == "Bonjour"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
.venv\Scripts\pytest tests/core/test_workflows_client.py -v
```
Expected: Fail with `ModuleNotFoundError` for `adapters.inference.workflows_client`.

- [ ] **Step 3: Implement workflows_client.py**

Create `backend/adapters/inference/workflows_client.py`:
```python
import os
import json
import logging
from google.cloud.workflows.executions_v1 import ExecutionsClient
from google.cloud.workflows.executions_v1.types import Execution

logger = logging.getLogger("animetix.workflows")

class GCPWorkflowsClient:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "animetix-prod")
        self.location = os.getenv("GCP_LOCATION", "europe-west1")
        self.workflow_id = os.getenv("GCP_WORKFLOW_ID", "manga-voice-pipeline")
        
        self.client = ExecutionsClient()
        self.parent = f"projects/{self.project_id}/locations/{self.location}/workflows/{self.workflow_id}"

    def trigger_pipeline(self, image_b64: str, reference_audio_b64: str, target_lang: str, filename: str) -> str:
        arguments = {
            "brain_url": os.getenv("BRAIN_API_URL", "http://localhost:7861"),
            "api_key": os.getenv("BRAIN_API_KEY", "dev-insecure-key-animetix-2026"),
            "image": image_b64,
            "reference_audio": reference_audio_b64,
            "target_lang": target_lang,
            "gcs_bucket": os.getenv("GCS_MEDIA_BUCKET", "animetix-media-bucket"),
            "filename": filename
        }

        execution = Execution(argument=json.dumps(arguments))
        response = self.client.create_execution(parent=self.parent, execution=execution)
        logger.info(f"Triggered GCP workflow execution: {response.name}")
        return response.name

    def get_execution_status(self, execution_name: str) -> dict:
        execution = self.client.get_execution(name=execution_name)
        
        state_map = {
            1: "ACTIVE",
            2: "SUCCEEDED",
            3: "FAILED",
            4: "CANCELLED"
        }
        
        status_info = {
            "state": state_map.get(execution.state, "UNKNOWN"),
            "error": execution.error.message if execution.error else None,
            "result": None
        }

        if execution.state == 2:  # SUCCEEDED
            status_info["result"] = json.loads(execution.result)

        return status_info
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/core/test_workflows_client.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/workflows_client.py tests/core/test_workflows_client.py
git commit -m "feat: implement GCPWorkflowsClient to execute and poll pipelines"
```

---

### Task 3: Create Workflow YAML Definition

**Files:**
- Create: `deploy/workflows/manga_voice_pipeline.yaml`

- [ ] **Step 1: Write the YAML pipeline definition**

Create `deploy/workflows/manga_voice_pipeline.yaml`:
```yaml
main:
  params: [args]
  steps:
    - init:
        assign:
          - brain_url: ${args.brain_url}
          - api_key: ${args.api_key}
          - target_lang: ${default(map.get(args, "target_lang"), "French")}
          - gcs_bucket: ${args.gcs_bucket}
          - filename: ${args.filename}

    - run_ocr:
        call: http.post
        args:
          url: ${brain_url + "/vision/manga/process"}
          headers:
            X-API-Key: ${api_key}
            Content-Type: "application/json"
          body:
            image: ${args.image}
        result: ocr_response

    - extract_text:
        assign:
          - extracted_text: ${ocr_response.body.text}

    - check_text:
        switch:
          - condition: ${len(extracted_text) == 0}
            next: return_empty

    - run_translation:
        call: http.post
        args:
          url: ${brain_url + "/generate"}
          headers:
            X-API-Key: ${api_key}
            Content-Type: "application/json"
          body:
            prompt: ${"Translate the following text from manga bubbles to " + target_lang + ": " + extracted_text}
            system_prompt: "You are a professional manga translator. Output only the translated text."
        result: translation_response

    - run_tts:
        call: http.post
        args:
          url: ${brain_url + "/audio/clone-voice"}
          headers:
            X-API-Key: ${api_key}
            Content-Type: "application/json"
          body:
            text: ${translation_response.body.text}
            reference_audio: ${args.reference_audio}
            language: "fr"
        result: tts_response

    - upload_to_gcs:
        call: googleapis.storage.v1.objects.insert
        args:
          bucket: ${gcs_bucket}
          name: ${filename}
          body: ${tts_response.body.audio_b64}
        result: gcs_response

    - return_result:
        return:
          status: "success"
          extracted_text: ${extracted_text}
          translated_text: ${translation_response.body.text}
          audio_url: ${"https://storage.googleapis.com/" + gcs_bucket + "/" + filename}

    - return_empty:
        return:
          status: "empty"
          extracted_text: ""
          translated_text: ""
          audio_url: ""
```

- [ ] **Step 2: Commit**

```bash
git add deploy/workflows/manga_voice_pipeline.yaml
git commit -m "deploy: add manga voice workflow pipeline YAML definition"
```

---

### Task 4: Implement Polling Endpoint in Django Views

**Files:**
- Modify: `backend/api/animetix/tasks_views.py`
- Modify: `backend/api/animetix_project/urls.py`
- Test: `tests/backend/test_tasks_views.py`

- [ ] **Step 1: Write a failing test for workflow polling endpoint**

Create `tests/backend/test_tasks_views.py`:
```python
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
@patch('api.animetix.tasks_views.GCPWorkflowsClient')
def test_poll_workflow_endpoint(mock_client_class, client):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Test ACTIVE state returns 503 Service Unavailable
    mock_client.get_execution_status.return_value = {"state": "ACTIVE", "error": None, "result": None}
    
    url = reverse('poll-workflow')
    response = client.post(url, {"execution_name": "exec-123", "task_id": "t-123"}, content_type="application/json")
    assert response.status_code == 503
    
    # Test SUCCEEDED state returns 200 and stores in cache
    mock_client.get_execution_status.return_value = {
        "state": "SUCCEEDED",
        "error": None,
        "result": {
            "translated_text": "Bonjour",
            "audio_url": "http://gcs/audio.wav"
        }
    }
    response = client.post(url, {"execution_name": "exec-123", "task_id": "t-123"}, content_type="application/json")
    assert response.status_code == 200
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_tasks_views.py -v
```
Expected: Fail with `NoReverseMatch` for url `poll-workflow`.

- [ ] **Step 3: Implement `/api/tasks/poll-workflow/` view**

Modify `backend/api/animetix/tasks_views.py` (append the view):
```python
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from adapters.inference.workflows_client import GCPWorkflowsClient

@csrf_exempt
def poll_workflow_view(request):
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
        
    try:
        data = json.loads(request.body)
        execution_name = data.get('execution_name')
        task_id = data.get('task_id')
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid payload"}, status=400)
        
    if not execution_name or not task_id:
        return JsonResponse({"error": "Missing execution_name or task_id"}, status=400)
        
    client = GCPWorkflowsClient()
    status = client.get_execution_status(execution_name)
    
    state = status.get("state")
    if state == "ACTIVE":
        # Cloud Tasks will retry automatically upon receiving 503
        return HttpResponse("Workflow is still active", status=503)
        
    elif state == "SUCCEEDED":
        result = status.get("result", {})
        cache.set(f"task_result:{task_id}", {
            "status": "success",
            "result": {
                "translated_text": result.get("translated_text", ""),
                "audio_url": result.get("audio_url", "")
            }
        }, timeout=3600)
        return JsonResponse({"status": "completed"})
        
    else:
        # FAILED or CANCELLED
        cache.set(f"task_result:{task_id}", {
            "status": "failed",
            "error": status.get("error", "Workflow execution failed")
        }, timeout=3600)
        return JsonResponse({"status": "failed"})
```

Modify `backend/api/animetix_project/urls.py` to route `/api/tasks/poll-workflow/` to `poll_workflow_view` (using namespace/names correctly):
```python
# Add this import at the top of backend/api/animetix_project/urls.py:
from api.animetix.tasks_views import poll_workflow_view

# In urlpatterns, add:
path('api/tasks/poll-workflow/', poll_workflow_view, name='poll-workflow'),
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_tasks_views.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/tasks_views.py backend/api/animetix_project/urls.py tests/backend/test_tasks_views.py
git commit -m "feat: add workflow polling task view with HTTP 503 retry hook"
```

---

### Task 5: Implement `/api/labs/manga-voice/` API View

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Modify: `backend/api/animetix_project/urls.py`
- Test: `tests/backend/test_labs_views.py`

- [ ] **Step 1: Write a failing test for `/api/labs/manga-voice/` view**

Create `tests/backend/test_labs_views.py`:
```python
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
@patch('api.animetix.api.labs.GCPWorkflowsClient')
@patch('api.animetix.api.labs.enqueue_task')
def test_manga_voice_endpoint_production(mock_enqueue, mock_workflows_client_class, client, settings):
    settings.IS_PRODUCTION = True
    mock_client = MagicMock()
    mock_workflows_client_class.return_value = mock_client
    mock_client.trigger_pipeline.return_value = "projects/test/locations/europe-west1/workflows/wf/executions/ex-123"
    
    url = reverse('manga-voice')
    response = client.post(url, {
        "image": "b64_image_content",
        "reference_audio": "b64_audio_content",
        "target_lang": "French"
    }, content_type="application/json")
    
    assert response.status_code == 202
    assert "task_id" in response.json()
    assert mock_enqueue.called
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_labs_views.py -v
```
Expected: Fail with `NoReverseMatch` for url `manga-voice`.

- [ ] **Step 3: Implement `/api/labs/manga-voice/` view and register url**

Modify `backend/api/animetix/api/labs.py` by adding the following view function:
```python
import uuid
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from adapters.inference.workflows_client import GCPWorkflowsClient
from api.animetix.tasks_client import enqueue_task

@csrf_exempt
def manga_voice_view(request):
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
        
    try:
        data = json.loads(request.body)
        image = data.get('image')
        reference_audio = data.get('reference_audio')
        target_lang = data.get('target_lang', 'French')
    except (ValueError, KeyError):
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        
    if not image or not reference_audio:
        return JsonResponse({"error": "Missing image or reference_audio in payload"}, status=400)
        
    task_id = str(uuid.uuid4())
    filename = f"manga_voice_{task_id}.wav"
    
    # Initialize cache status
    cache.set(f"task_result:{task_id}", {"status": "pending"}, timeout=3600)
    
    if getattr(settings, 'IS_PRODUCTION', False):
        try:
            client = GCPWorkflowsClient()
            execution_name = client.trigger_pipeline(image, reference_audio, target_lang, filename)
            
            # Queue a Cloud Task to poll the workflow execution status
            enqueue_task("poll_workflow_task", {
                "execution_name": execution_name,
                "task_id": task_id
            })
            return JsonResponse({"task_id": task_id}, status=202)
        except Exception as e:
            cache.set(f"task_result:{task_id}", {"status": "failed", "error": str(e)}, timeout=3600)
            return JsonResponse({"error": f"Failed to start workflow: {str(e)}"}, status=500)
    else:
        # Fallback local development: run synchronously and store success directly in cache
        # Mocking or running direct execution using dummy result to avoid GCP dependency
        cache.set(f"task_result:{task_id}", {
            "status": "success",
            "result": {
                "translated_text": "[Local Dev Fallback] Traduction simulée.",
                "audio_url": f"http://localhost:8000/media/mock_{filename}"
            }
        }, timeout=3600)
        return JsonResponse({"task_id": task_id}, status=202)
```

Modify `backend/api/animetix_project/urls.py`:
```python
# Add this import at the top of backend/api/animetix_project/urls.py:
from api.animetix.api.labs import manga_voice_view

# In urlpatterns, add:
path('api/labs/manga-voice/', manga_voice_view, name='manga-voice'),
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_labs_views.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/labs.py backend/api/animetix_project/urls.py tests/backend/test_labs_views.py
git commit -m "feat: implement /api/labs/manga-voice/ endpoint with local dev fallback"
```
