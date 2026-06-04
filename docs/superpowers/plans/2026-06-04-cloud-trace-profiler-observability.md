# GCP Cloud Trace & Profiler Observability Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up end-to-end distributed tracing using OpenTelemetry and GCP Cloud Trace, and continuous profiling using GCP Cloud Profiler across the Django web app and FastAPI Brain API.

**Architecture:** Create a unified `telemetry.py` module to initialize GCP Profiler and OpenTelemetry Cloud Trace exporters in production. Add custom Django and FastAPI HTTP middlewares for automatic incoming request instrumentation. Inject W3C trace context headers into asynchronous Tasks triggered via Cloud Tasks and extract them at execution to preserve trace history across service boundaries.

**Tech Stack:** Python, Django, FastAPI, OpenTelemetry API & SDK, GCP Cloud Trace Exporter, GCP Cloud Profiler, Pytest.

---

### Task 1: Add Telemetry Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Append GCP OpenTelemetry trace and profiler libraries to requirements.txt**

Add the following libraries at the end of the `requirements.txt` file:
```text
opentelemetry-exporter-gcp-trace==1.7.0
google-cloud-profiler==4.1.0
```

- [ ] **Step 2: Run pip install to install new requirements**

Run:
```bash
.venv\Scripts\pip install -r requirements.txt
```
Expected: Successfully installed.

---

### Task 2: Create Telemetry Helper Module

**Files:**
- Create: `backend/api/animetix/telemetry.py`

- [ ] **Step 1: Write telemetry initialization logic**

Create `backend/api/animetix/telemetry.py` with:
```python
import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger("animetix.telemetry")

def init_telemetry(service_name: str):
    """
    Initializes Google Cloud Profiler and OpenTelemetry tracing.
    """
    # 1. Start Google Cloud Profiler in production
    if os.getenv("DJANGO_ENV") == "production":
        try:
            import googlecloudprofiler
            googlecloudprofiler.start(
                service=service_name,
                verbose=2,
            )
            logger.info(f"✅ Google Cloud Profiler started for service: {service_name}")
        except Exception as e:
            logger.warning(f"Could not start Google Cloud Profiler: {e}")

    # 2. Setup OpenTelemetry Tracer Provider
    try:
        provider = TracerProvider(
            resource=Resource.create({"service.name": service_name})
        )
        trace.set_tracer_provider(provider)
        
        if os.getenv("DJANGO_ENV") == "production":
            from opentelemetry.exporter.gcp.trace import CloudTraceSpanExporter
            exporter = CloudTraceSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"✅ OpenTelemetry CloudTraceSpanExporter configured for: {service_name}")
        else:
            logger.info("ℹ️ Telemetry initialized in local dev mode (no exporter).")
            
    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}")

def inject_trace_context(headers: dict):
    """Injects current W3C trace context into target headers dictionary."""
    TraceContextTextMapPropagator().inject(headers)

def extract_trace_context(headers: dict):
    """Extracts W3C trace context from incoming request headers."""
    return TraceContextTextMapPropagator().extract(headers)
```

---

### Task 3: Instrument Django Application

**Files:**
- Modify: `backend/api/animetix/apps.py`
- Modify: `backend/api/animetix/middleware.py`
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Initialize telemetry on Django App Ready**

Modify `backend/api/animetix/apps.py` to invoke `init_telemetry`:
```python
# Target lines to replace:
    def ready(self):
        import animetix.signals  # noqa
```
With:
```python
    def ready(self):
        import animetix.signals  # noqa
        from animetix.telemetry import init_telemetry
        init_telemetry("animetix-web")
```

- [ ] **Step 2: Add TracingMiddleware to middleware.py**

Append the custom request tracing middleware at the end of `backend/api/animetix/middleware.py`:
```python
class TracingMiddleware:
    """
    Middleware that wraps incoming HTTP requests in an OpenTelemetry span.
    Propagates trace contexts if headers are present (e.g. from Cloud Tasks).
    """
    sync_capable = True
    async_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        from opentelemetry import trace
        self.tracer = trace.get_tracer("animetix.web.request")

    def __call__(self, request):
        from animetix.telemetry import extract_trace_context
        from opentelemetry.trace import Status, StatusCode
        
        # Convert request META headers to dictionary for extraction
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').lower()
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                headers[key.replace('_', '-').lower()] = value

        context = extract_trace_context(headers)
        span_name = f"HTTP {request.method} {request.path}"
        
        with self.tracer.start_as_current_span(span_name, context=context) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", request.build_absolute_uri())
            
            try:
                response = self.get_response(request)
                span.set_attribute("http.status_code", response.status_code)
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, description=f"HTTP {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))
                return response
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                raise e
```

- [ ] **Step 3: Register TracingMiddleware in settings.py**

Modify `backend/api/animetix_project/settings.py` around line 219 (just before `django_prometheus` or at the very top of `MIDDLEWARE`):
```python
MIDDLEWARE = [
    'animetix.middleware.TracingMiddleware',  # Tracing at the very beginning of the stack
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    ...
]
```

---

### Task 4: Propagate Traces in Cloud Tasks

**Files:**
- Modify: `backend/api/animetix/tasks_client.py`
- Modify: `backend/api/animetix/tasks_views.py`

- [ ] **Step 1: Inject trace headers in tasks_client.py**

Modify `backend/api/animetix/tasks_client.py` around line 50. Inject headers during task creation:
```python
    # Target lines to replace:
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": worker_url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode("utf-8"),
            "oidc_token": {"service_account_email": service_account},
        }
    }
```
With:
```python
    from animetix.telemetry import inject_trace_context
    task_headers = {"Content-Type": "application/json"}
    inject_trace_context(task_headers)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": worker_url,
            "headers": task_headers,
            "body": json.dumps(payload).encode("utf-8"),
            "oidc_token": {"service_account_email": service_account},
        }
    }
```

- [ ] **Step 2: Extract trace context during task execution in tasks_views.py**

Modify `backend/api/animetix/tasks_views.py` around line 45 (inside the `run_task` view):
```python
# Target lines to replace:
@csrf_exempt
@require_POST
def run_task(request):
    """
    Endpoint invoqué par Cloud Tasks pour exécuter une tâche.
    """
    # ...
    try:
        data = json.loads(request.body)
        task_name = data.get("task_name")
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})
        
        # Exécution de la tâche
        registry.execute(task_name, *args, **kwargs)
        return JsonResponse({"status": "ok"})
```
With:
```python
@csrf_exempt
@require_POST
def run_task(request):
    """
    Endpoint invoqué par Cloud Tasks pour exécuter une tâche.
    """
    from animetix.telemetry import extract_trace_context
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    
    # Extract trace context from request headers
    headers = {k.lower(): v for k, v in request.headers.items()}
    context = extract_trace_context(headers)
    
    tracer = trace.get_tracer("animetix.tasks.worker")
    
    # ...
    try:
        data = json.loads(request.body)
        task_name = data.get("task_name")
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})
        
        with tracer.start_as_current_span(f"Task {task_name}", context=context) as span:
            span.set_attribute("task.name", task_name)
            try:
                registry.execute(task_name, *args, **kwargs)
                span.set_status(Status(StatusCode.OK))
            except Exception as task_err:
                span.record_exception(task_err)
                span.set_status(Status(StatusCode.ERROR, description=str(task_err)))
                raise task_err
                
        return JsonResponse({"status": "ok"})
```

---

### Task 5: Instrument FastAPI (Brain API)

**Files:**
- Modify: `backend/adapters/inference/brain_api.py`

- [ ] **Step 1: Initialize telemetry and add middleware to brain_api.py**

Modify `backend/adapters/inference/brain_api.py` to configure OpenTelemetry.
Add imports at the top of the file:
```python
from animetix.telemetry import init_telemetry, extract_trace_context
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
```

Modify the lifespan function to call `init_telemetry`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing telemetry for brain-api...")
    init_telemetry("animetix-brain")
    logger.info(f"🧠 Brain API running with engine {model_name}")
    yield
```

Add HTTP middleware just before endpoints definition (around line 150):
```python
@app.middleware("http")
async def add_process_trace_context(request: Request, call_next):
    # Extract trace context from request headers
    headers = {k.lower(): v for k, v in request.headers.items()}
    context = extract_trace_context(headers)
    
    tracer = trace.get_tracer("animetix.brain.request")
    span_name = f"HTTP {request.method} {request.url.path}"
    
    with tracer.start_as_current_span(span_name, context=context) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        
        try:
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 400:
                span.set_status(Status(StatusCode.ERROR, description=f"HTTP {response.status_code}"))
            else:
                span.set_status(Status(StatusCode.OK))
            return response
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, description=str(e)))
            raise e
```

---

### Task 6: Create Unit Tests & Verification

**Files:**
- Create: `tests/backend/test_telemetry.py`

- [ ] **Step 1: Write test_telemetry.py unit test suite**

Create `tests/backend/test_telemetry.py` with:
```python
import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse
from animetix.telemetry import init_telemetry, inject_trace_context, extract_trace_context
from animetix.middleware import TracingMiddleware

@pytest.fixture
def rf():
    return RequestFactory()

def test_telemetry_inject_extract_context():
    from opentelemetry import trace
    tracer = trace.get_tracer("test-tracer")
    
    headers = {}
    with tracer.start_as_current_span("parent-span") as span:
        inject_trace_context(headers)
        
    assert "traceparent" in headers
    
    # Extract trace context
    extracted_context = extract_trace_context(headers)
    assert extracted_context is not None

def test_tracing_middleware_creates_span(rf):
    request = rf.get("/explore/")
    # Mock trace context
    request.META["HTTP_TRACEPARENT"] = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    
    middleware = TracingMiddleware(lambda req: HttpResponse("OK"))
    
    with patch("opentelemetry.trace.Tracer.start_as_current_span") as mock_start_span:
        mock_start_span.return_value.__enter__.return_value = MagicMock()
        middleware(request)
        mock_start_span.assert_called_once()
        # Verify it passed custom context from HTTP_TRACEPARENT
        call_kwargs = mock_start_span.call_args[1]
        assert "context" in call_kwargs
```

- [ ] **Step 2: Run verification tests**

Run:
```bash
.venv\Scripts\pytest tests/backend/test_telemetry.py -v
```
Expected: 2 passed.

- [ ] **Step 3: Commit all changes**

Run:
```bash
git add requirements.txt backend/api/animetix/telemetry.py backend/api/animetix/apps.py backend/api/animetix/middleware.py backend/api/animetix_project/settings.py backend/api/animetix/tasks_client.py backend/api/animetix/tasks_views.py backend/adapters/inference/brain_api.py tests/backend/test_telemetry.py docs/superpowers/plans/2026-06-04-cloud-trace-profiler-observability.md docs/superpowers/specs/2026-06-04-cloud-trace-profiler-observability-design.md docs/TODO.md
git commit -m "feat: implement GCP Cloud Trace OpenTelemetry and Cloud Profiler end-to-end telemetry instrumentation"
```
