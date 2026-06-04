# Personalization Middleware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Intercept JSON responses for authenticated users to inject "Visual Meta" (archetype drift configuration) into the response.

**Architecture:** Transition `animetix.middleware` to a package structure. Create a specialized middleware that uses dependency injection to fetch user personalization data and injects it into API responses.

**Tech Stack:** Django, Python Dependency Injector, Pydantic.

---

### Task 1: Restructure animetix.middleware

**Files:**
- Create: `backend/api/animetix/middleware/__init__.py`
- Modify: `backend/api/animetix/middleware.py` (Delete)

- [ ] **Step 1: Create the middleware directory**
Run: `mkdir backend/api/animetix/middleware`

- [ ] **Step 2: Move existing middleware to __init__.py**
Run: `mv backend/api/animetix/middleware.py backend/api/animetix/middleware/__init__.py`

- [ ] **Step 3: Verify existing tests still pass**
Run: `pytest tests/backend/api/test_middleware.py` (Assuming this test exists, or check `tests/`)

---

### Task 2: Implement Failing Tests for PersonalizationMiddleware

**Files:**
- Create: `backend/api/animetix/tests/test_personalization_middleware.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import pytest
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.http import JsonResponse
from unittest.mock import MagicMock, patch
from ..middleware.personalization_middleware import PersonalizationMiddleware

@pytest.mark.django_db
def test_personalization_middleware_injects_config():
    # Setup
    user = User.objects.create_user(username='testuser')
    factory = RequestFactory()
    request = factory.get('/api/any/')
    request.user = user
    
    response = JsonResponse({"data": "test"})
    
    # Mock service
    mock_config = MagicMock()
    mock_config.model_dump.return_value = {"archetype_id": "test_archetype"}
    mock_service = MagicMock()
    mock_service.calculate_drift.return_value = mock_config
    
    # Initialize middleware with mock service
    middleware = PersonalizationMiddleware(lambda r: response)
    
    # Execute with patching Provide
    with patch('dependency_injector.wiring.Provide', return_value=mock_service):
        processed_response = middleware.process_response(request, response, drift_service=mock_service)
    
    # Verify
    data = json.loads(processed_response.content)
    assert "meta" in data
    assert data["meta"]["visual_config"] == {"archetype_id": "test_archetype"}

def test_personalization_middleware_ignores_anonymous():
    from django.contrib.auth.models import AnonymousUser
    factory = RequestFactory()
    request = factory.get('/api/any/')
    request.user = AnonymousUser()
    
    response = JsonResponse({"data": "test"})
    middleware = PersonalizationMiddleware(lambda r: response)
    
    processed_response = middleware.process_response(request, response, drift_service=MagicMock())
    
    data = json.loads(processed_response.content)
    assert "meta" not in data
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest backend/api/animetix/tests/test_personalization_middleware.py`
Expected: FAIL (ImportError or AttributeError)

---

### Task 3: Implement PersonalizationMiddleware

**Files:**
- Create: `backend/api/animetix/middleware/personalization_middleware.py`

- [ ] **Step 1: Write implementation**

```python
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from dependency_injector.wiring import inject, Provide
from ..containers import Container

logger = logging.getLogger('animetix.middleware.personalization')

class PersonalizationMiddleware(MiddlewareMixin):
    @inject
    def process_response(self, request, response, drift_service=Provide[Container.core.archetype_drift_service]):
        if response.has_header('Content-Type') and 'application/json' in response['Content-Type']:
            if hasattr(request, 'user') and request.user.is_authenticated:
                try:
                    config = drift_service.calculate_drift(request.user.id)
                    data = json.loads(response.content)
                    if isinstance(data, dict):
                        data['meta'] = data.get('meta', {})
                        # config is a Pydantic model (VisualConfig)
                        data['meta']['visual_config'] = config.model_dump()
                        response.content = json.dumps(data)
                except Exception as e:
                    logger.error(f"PersonalizationMiddleware error: {e}")
                    pass
        return response
```

- [ ] **Step 2: Run tests to verify they pass**
Run: `pytest backend/api/animetix/tests/test_personalization_middleware.py`
Expected: PASS

---

### Task 4: Enable Middleware in Settings

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Update settings.py**

Find `MIDDLEWARE` list and add the new middleware.

```python
MIDDLEWARE = [
    ...
    'animetix.middleware.UserTrackingMiddleware',
    'animetix.middleware.personalization_middleware.PersonalizationMiddleware',
    ...
]
```

- [ ] **Step 2: Verify application still starts**
Run: `python backend/api/manage.py check`

---

### Task 5: Commit Changes

- [ ] **Step 1: Commit**
Run:
```bash
git add backend/api/animetix/middleware/
git add backend/api/animetix/tests/test_personalization_middleware.py
git add backend/api/animetix_project/settings.py
git commit -m "feat(personalization): add PersonalizationMiddleware and restructure middleware package"
```
