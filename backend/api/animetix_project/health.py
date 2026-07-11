"""Liveness endpoint backing the deploy smoke test (ci.yml deploy-to-prod).

Plain Django view by design: no DRF (the anon throttle must never 429 the
deploy gate), no auth, no DB query. Answering 200 proves the revision booted —
supervisord runs migrate before starting gunicorn, so a failed migration or a
missing secret never reaches this point. K_REVISION is set by Cloud Run and
lets the smoke test log which revision it actually hit.
"""

import os

from django.http import HttpRequest, JsonResponse


def healthz(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "revision": os.getenv("K_REVISION", "local")})
