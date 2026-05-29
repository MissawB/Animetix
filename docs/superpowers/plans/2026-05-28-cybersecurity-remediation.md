# Cybersecurity Audit & Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure the Animetix platform by fixing critical SSRF and RCE vulnerabilities and hardening global security configurations.

**Architecture:** This plan implements defense-in-depth by restricting CORS, adding security headers, validating proxy requests against internal IP ranges, and replacing dangerous dynamic code execution with safe templates.

**Tech Stack:** Django, Django REST Framework, django-ratelimit, urllib, socket.

---

### Task 1: Hardening Django Settings

**Files:**
- Modify: `backend/api/animetix_project/settings.py`

- [ ] **Step 1: Update CORS and Security Headers**

Modify `backend/api/animetix_project/settings.py` to restrict CORS and enable security headers.

```python
# Around line 70-80
if IS_PRODUCTION:
    SECRET_KEY = env('DJANGO_SECRET_KEY')
    DEBUG = env.bool('DJANGO_DEBUG', default=False)
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['missawb-animetix-web.hf.space'])
else:
    # Mode Développement Souple
    SECRET_KEY = 'django-insecure-dev-fallback-key-very-secret'
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Around line 200
# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://missawb-animetix-web.hf.space",
]

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY' # Overriding previous ALLOWALL for security
```

- [ ] **Step 2: Verify settings load without error**

Run: `python backend/api/manage.py check`
Expected: System check identified no issues (0 silenced).

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix_project/settings.py
git commit -m "security: harden CORS and security headers"
```

---

### Task 2: Fixing SSRF in Image Proxy

**Files:**
- Modify: `backend/api/animetix/api/core.py`
- Test: `tests/backend/test_security_proxy.py`

- [ ] **Step 1: Write failing SSRF test**

Create `tests/backend/test_security_proxy.py`.

```python
import pytest
import base64
from django.urls import reverse

@pytest.mark.django_db
def test_image_proxy_blocks_internal_ips(client):
    # Attempting to access an internal IP (e.g. metadata service or localhost)
    internal_url = "http://127.0.0.1:8000/admin/"
    encoded = base64.b64encode(internal_url.encode()).decode()
    url = reverse('api-fusions') # Just to get a base, then use the manual path
    # image_proxy_view is likely at /api/v1/proxy/ or similar, check urls
    proxy_url = f"/api/v1/proxy/?url={encoded}" # Adjust based on actual URL
    
    response = client.get(proxy_url)
    assert response.status_code == 400 or response.status_code == 403
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/backend/test_security_proxy.py`
Expected: FAIL (likely 404 if URL is wrong or 200/500 if it currently allows it)

- [ ] **Step 3: Implement SSRF protection in `image_proxy_view`**

Modify `backend/api/animetix/api/core.py`.

```python
import socket
from urllib.parse import urlparse
import ipaddress

def is_safe_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Resolve IP
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        # Check if private/loopback
        if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local:
            return False
            
        return True
    except Exception:
        return False

def image_proxy_view(request):
    encoded_url = request.GET.get('url')
    if not encoded_url: return HttpResponse(status=400)
    
    try:
        url = base64.b64decode(encoded_url).decode('utf-8')
    except Exception as e:
        return HttpResponse(status=400)

    if not is_safe_url(url):
        logger.warning(f"Blocked SSRF attempt to: {url}")
        return HttpResponse("Forbidden: Internal or unsafe URL", status=403)

    # ... rest of the existing logic ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/backend/test_security_proxy.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix/api/core.py tests/backend/test_security_proxy.py
git commit -m "security: fix SSRF in image_proxy_view"
```

---

### Task 3: Neutralizing RCE in Singularity Lab

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Modify: `backend/core/domain/services/self_evolving_compiler.py`

- [ ] **Step 1: Restrict code submission in `SingularityLabDataView`**

Modify `backend/api/animetix/api/labs.py`. Remove `slow_logic_code` handling or restrict it to predefined function names.

```python
# In SingularityLabDataView.post
        if action == 'compile':
            function_name = request.data.get('function_name', 'cosine_similarity').strip()
            # BLOCKED: slow_logic_code = request.data.get('slow_logic_code', '').strip()
            
            # Only allow a set of safe predefined functions
            ALLOWED_FUNCTIONS = ['cosine_similarity', 'euclidean_distance', 'vector_norm']
            if function_name not in ALLOWED_FUNCTIONS:
                return Response({'error': 'Invalid function name'}, status=400)
                
            try:
                # Use predefined safe logic instead of user input
                optimized_fn = container.self_evolving_compiler.analyze_and_optimize(function_name)
                # ... rest of the logic ...
```

- [ ] **Step 2: Update `SelfEvolvingCompiler` to use safe logic**

Modify `backend/core/domain/services/self_evolving_compiler.py`.

```python
class SelfEvolvingCompiler:
    SAFE_LOGIC = {
        'cosine_similarity': 'return dot(a, b) / (norm(a) * norm(b));',
        'euclidean_distance': 'return sqrt(sum((a - b)**2));'
    }

    def analyze_and_optimize(self, function_name: str, code_override: str = None):
        # Ignore code_override in production
        logic = self.SAFE_LOGIC.get(function_name)
        if not logic:
            raise ValueError("Unknown function")
        # ... logic to "compile" (e.g. return a pre-compiled cython or numba function) ...
```

- [ ] **Step 3: Verify with manual test request**

Use a script or `curl` to try and send `slow_logic_code`.

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/api/labs.py backend/core/domain/services/self_evolving_compiler.py
git commit -m "security: neutralize RCE in SingularityLabDataView by removing dynamic code submission"
```

---

### Task 4: Implementing Rate Limiting

**Files:**
- Modify: `backend/api/animetix/api/streams.py`
- Modify: `backend/api/animetix/api/games/akinetix.py` (and others if needed)

- [ ] **Step 1: Apply `@ratelimit` to AI endpoints**

Modify `backend/api/animetix/api/streams.py`.

```python
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='GET', block=True), name='get')
class AgenticRAGStreamView(APIView):
    # ... existing code ...
```

- [ ] **Step 2: Run verification**

Ensure `django-ratelimit` is working by making 6 requests in a minute.

- [ ] **Step 3: Commit**

```bash
git add backend/api/animetix/api/streams.py
git commit -m "security: add rate limiting to AI stream endpoints"
```
