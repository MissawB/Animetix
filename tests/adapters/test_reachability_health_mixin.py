"""Unit tests for the shared ReachabilityHealthCheckMixin.

API-backed inference adapters report *reachability* (can the remote service be
reached?) rather than *readiness* (is a local model loaded?). This mixin
factors the standardized status payload and the single-endpoint HTTP probe out
of BrainAPIAdapter / GoogleGenAIAdapter / UnifiedInferenceAdapter.

The probe is driven by a caller-supplied ``requester`` so each adapter keeps
its own HTTP client (``httpx.get`` vs the SSRF-guarded ``safe_http_request``)
and its existing patch targets — the mixin never imports a transport itself.
"""

from unittest.mock import MagicMock

from adapters.inference.reachability_health_mixin import ReachabilityHealthCheckMixin


class _Dummy(ReachabilityHealthCheckMixin):
    pass


def _resp(status=200, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload or {}
    return r


# --- _health_status: standardized payload builder ----------------------------


def test_health_status_builds_status_plus_fields():
    out = _Dummy()._health_status("online", engine="X", model="m")
    assert out == {"status": "online", "engine": "X", "model": "m"}


def test_health_status_status_only():
    assert _Dummy()._health_status("offline") == {"status": "offline"}


# --- _http_ping_health: online / degraded / offline --------------------------


def test_ping_online_on_200():
    req = MagicMock(return_value=_resp(200))
    out = _Dummy()._http_ping_health(req, "http://svc/health", engine="Svc")
    assert out == {"status": "online", "engine": "Svc"}
    assert req.call_args.args[0] == "http://svc/health"


def test_ping_degraded_on_non_200():
    req = MagicMock(return_value=_resp(503))
    out = _Dummy()._http_ping_health(req, "http://svc/health", engine="Svc")
    assert out["status"] == "degraded"
    assert out["engine"] == "Svc"


def test_ping_offline_on_exception():
    req = MagicMock(side_effect=ConnectionError("refused"))
    out = _Dummy()._http_ping_health(req, "http://svc/health", engine="Svc")
    assert out == {"status": "offline", "engine": "Svc"}


def test_ping_with_latency_included_when_requested():
    req = MagicMock(return_value=_resp(200))
    out = _Dummy()._http_ping_health(
        req, "http://svc/health", engine="Svc", with_latency=True
    )
    assert out["status"] == "online"
    assert isinstance(out["latency_ms"], float)


def test_ping_offline_omits_latency_even_when_requested():
    req = MagicMock(side_effect=TimeoutError())
    out = _Dummy()._http_ping_health(
        req, "http://svc/health", engine="Svc", with_latency=True
    )
    assert out == {"status": "offline", "engine": "Svc"}


def test_ping_forwards_positional_and_keyword_args_to_requester():
    # Mirrors the UnifiedInferenceAdapter call: ("GET", url, timeout=..., allow_internal=...).
    req = MagicMock(return_value=_resp(200))
    _Dummy()._http_ping_health(
        req, "GET", "http://svc/api/tags", engine="Svc", timeout=5, allow_internal=True
    )
    assert req.call_args.args == ("GET", "http://svc/api/tags")
    assert req.call_args.kwargs == {"timeout": 5, "allow_internal": True}


def test_ping_ok_extra_enriches_only_online_payload():
    req = MagicMock(return_value=_resp(200, {"models": [{"name": "qwen"}]}))
    out = _Dummy()._http_ping_health(
        req,
        "http://svc/api/tags",
        engine="Svc",
        ok_extra=lambda res: {"models": res.json().get("models", [])},
    )
    assert out == {"status": "online", "engine": "Svc", "models": [{"name": "qwen"}]}


def test_ping_ok_extra_skipped_on_degraded():
    req = MagicMock(return_value=_resp(503, {"models": [{"name": "qwen"}]}))
    out = _Dummy()._http_ping_health(
        req,
        "http://svc/api/tags",
        engine="Svc",
        ok_extra=lambda res: {"models": res.json().get("models", [])},
    )
    assert "models" not in out
    assert out["status"] == "degraded"


def test_ping_ok_extra_failure_keeps_online_status():
    # A reachable service answers 200 but with an unparseable body, so ok_extra
    # raises. Enrichment is best-effort: a 200 must still report online, never
    # be downgraded to offline by an enrichment failure.
    req = MagicMock(return_value=_resp(200))

    def boom(_res):
        raise ValueError("malformed body")

    out = _Dummy()._http_ping_health(
        req, "http://svc/api/tags", engine="Svc", ok_extra=boom
    )
    assert out == {"status": "online", "engine": "Svc"}
