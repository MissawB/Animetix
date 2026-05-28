# Design Spec: Cybersecurity Audit & Remediation

**Date:** 2026-05-28
**Topic:** Critical Security Fixes & System Hardening
**Status:** Approved (Research/Strategy)

## 1. Goal
Address critical security vulnerabilities identified during the audit to prevent unauthorized system access, data exfiltration, and resource abuse.

## 2. Identified Vulnerabilities
| Severity | Vulnerability | Location | Impact |
| :--- | :--- | :--- | :--- |
| **Critical** | SSRF (Server-Side Request Forgery) | `image_proxy_view` in `api/core.py` | Access to internal services (Redis, DB, etc.) |
| **Critical** | RCE (Remote Code Execution) | `SingularityLabDataView` in `api/labs.py` | Full system compromise via dynamic code compilation |
| **High** | Insecure CORS Configuration | `settings.py` (`CORS_ALLOW_ALL_ORIGINS`) | Cross-site data exfiltration |
| **Medium** | Missing Rate Limiting | AI Stream endpoints in `api/streams.py` | Potential DoS and AI cost exploitation |

## 3. Remediations

### 3.1. SSRF Mitigation in `image_proxy_view`
The proxy must be restricted to prevent accessing internal networks.
- **URL Validation:** Use `urllib.parse` to extract the hostname.
- **IP Blacklisting:** Resolve hostname to IP and block ranges `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- **Domain Allow-list:** Restrict to trusted domains if possible (e.g., `images.weserv.nl`, `huggingface.co`).
- **MIME Type Check:** Validate that `Content-Type` is an image before returning.

### 3.2. RCE Mitigation in `SingularityLabDataView`
The current "self-evolving" compilation logic is inherently dangerous.
- **Restriction:** Disable raw code submission from the frontend.
- **Template Approach:** Users can only choose from pre-defined optimization templates (e.g., `cosine_similarity`, `vector_addition`).
- **Sandbox (Optional):** If dynamic logic is strictly required, use a containerized execution environment or a highly restricted sandbox (e.g., `z3-solver` context or limited AST evaluation). *Recommendation: Stick to templates for now.*

### 3.3. Configuration Hardening
- **CORS:** Set `CORS_ALLOWED_ORIGINS` to only include Hugging Face Spaces and local development domains. Disable `CORS_ALLOW_ALL_ORIGINS`.
- **Rate Limiting:** Implement `django-ratelimit` on all `APIView` classes that trigger LLM calls.
- **Security Headers:**
    - `SECURE_BROWSER_XSS_FILTER = True`
    - `SECURE_CONTENT_TYPE_NOSNIFF = True`
    - `X_FRAME_OPTIONS = 'DENY'` (except where specifically needed for HF Embeds).

## 4. Architecture Changes
- **Middleware:** No major changes.
- **Adapters:** No changes.
- **API Layer:** Surgical updates to `api/core.py`, `api/labs.py`, and `api/streams.py`.
- **Project Config:** Updates to `settings.py`.

## 5. Testing & Validation
- **SSRF Test:** Script attempting to access `http://db:5432` and `http://redis:6379` via the proxy.
- **RCE Test:** Attempt to execute `os.system('id')` via the Singularity Lab.
- **Configuration Check:** Verify CORS headers in response to unauthorized origins.
- **Rate Limit Test:** Rapid fire requests to stream endpoints.

## 6. Implementation Order
1.  **Settings Hardening** (CORS, Headers)
2.  **SSRF Fix** in `image_proxy_view`
3.  **RCE Neutralization** in `SingularityLabDataView`
4.  **Rate Limiting** on AI endpoints
