"""Shared *reachability* health-check helpers for API-backed inference adapters.

Local model adapters report *readiness* — is the model loaded into memory? API
adapters instead report *reachability* — can the remote service be reached right
now? This mixin factors out the two things those adapters were each duplicating:

1. the standardized status payload (``{"status": ..., "engine": ...}``), and
2. the single-endpoint HTTP probe (GET → classify by status code, catch → offline).

The probe never imports a transport. Callers pass their own ``requester``
(``httpx.get`` for BrainAPIAdapter, the SSRF-guarded ``safe_http_request`` for
UnifiedInferenceAdapter), so each adapter keeps its existing HTTP client *and*
its existing test patch targets — the function is resolved in the adapter's own
module namespace and handed in.
"""

import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("animetix.inference.health")


class ReachabilityHealthCheckMixin:
    """Reachability health-check helpers (status builder + HTTP ping)."""

    @staticmethod
    def _health_status(status: str, **fields: Any) -> Dict[str, Any]:
        """Build a standardized health payload: ``{"status": status, **fields}``."""
        return {"status": status, **fields}

    def _http_ping_health(
        self,
        requester: Callable[..., Any],
        *args: Any,
        engine: str,
        with_latency: bool = False,
        ok_extra: Optional[Callable[[Any], Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Probe one HTTP endpoint and classify the outcome.

        ``requester(*args, **kwargs)`` performs the GET. Returns ``online`` on
        HTTP 200, ``degraded`` on any other status (transport reached but
        unhealthy), and ``offline`` on a transport error. ``latency_ms`` is
        included on online/degraded results when ``with_latency`` is set;
        ``ok_extra`` may enrich the payload from the response, but only when
        the endpoint answered 200.
        """
        try:
            start = time.perf_counter()
            res = requester(*args, **kwargs)
            online = res.status_code == 200
            fields: Dict[str, Any] = {"engine": engine}
            if with_latency:
                fields["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            if online and ok_extra is not None:
                # Enrichment is best-effort: a 200 means the service is reachable,
                # so a failure parsing the body must never downgrade the result.
                try:
                    fields.update(ok_extra(res))
                except Exception:
                    logger.debug(
                        "Best-effort health enrichment failed for %s",
                        engine,
                        exc_info=True,
                    )
            return self._health_status("online" if online else "degraded", **fields)
        except Exception:
            return self._health_status("offline", engine=engine)
