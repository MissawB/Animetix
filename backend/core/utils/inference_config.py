"""Coherence-only configuration guard-rails for the inference adapters.

Pure helpers (no network, no DNS) so they are safe to run at container import
and trivially unit-testable. Policy:

- BRAIN_API_URL is REQUIRED (the managed central API has no sensible local
  default), so absence is an error.
- unified (Ollama) and google_genai are designed to DEGRADE GRACEFULLY in the
  fallback chain, so a totally absent config is fine; we only flag a config
  that is PRESENT BUT INVALID (a malformed LLM_API_BASE, a blank GEMINI_API_KEY).
"""

import os
from typing import List, Optional
from urllib.parse import urlparse

from core.domain.exceptions import ConfigurationError


def _is_blank(value: Optional[str]) -> bool:
    return value is None or not value.strip()


def _is_wellformed_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def check_brain_config(api_url: Optional[str]) -> Optional[str]:
    """BRAIN_API_URL is required; if present it must be a well-formed http(s) URL."""
    if _is_blank(api_url):
        return "BRAIN_API_URL is not configured"
    if not _is_wellformed_http_url(api_url):  # type: ignore[arg-type]
        return f"BRAIN_API_URL is malformed (expected http(s) URL): {api_url!r}"
    return None


def check_unified_config(api_base: Optional[str]) -> Optional[str]:
    """LLM_API_BASE is optional (defaults to localhost). Flag only a non-blank
    value that is not a well-formed http(s) URL."""
    if _is_blank(api_base):
        return None
    if not _is_wellformed_http_url(api_base):  # type: ignore[arg-type]
        return f"LLM_API_BASE is malformed (expected http(s) URL): {api_base!r}"
    return None


def check_google_genai_config(api_key: Optional[str]) -> Optional[str]:
    """GEMINI_API_KEY is optional (absence -> Vertex/degraded). Flag only a
    value that is present but blank/whitespace."""
    if api_key is not None and not api_key.strip():
        return "GEMINI_API_KEY is set but blank"
    return None


def local_inference_enabled(is_production: bool) -> bool:
    """Whether adapters that load model weights INTO THIS PROCESS may be used.

    The Cloud Run web container has a 4 GiB limit. A local text adapter pulls a
    3B causal LM through ``from_pretrained`` on the first ``generate()``, blows
    past the limit and gets the instance OOM-killed mid-request -- which Cloud
    Run surfaces to the client as a 503. Local weights therefore belong to
    development (and to the Brain service, which is sized for them), never to
    the web container.

    ``ENABLE_LOCAL_INFERENCE`` forces the answer either way, for a
    production-like host that does have the RAM/GPU budget.
    """
    override = os.getenv("ENABLE_LOCAL_INFERENCE")
    if not _is_blank(override):
        return override.strip().lower() in ("1", "true", "yes", "on")  # type: ignore[union-attr]
    return not is_production


def validate_inference_config() -> None:
    """Validate all inference env vars at once and raise a single aggregated
    ConfigurationError listing every problem (better DX than failing on the
    first missing one). Raises nothing when the config is coherent."""
    problems: List[Optional[str]] = [
        check_brain_config(os.getenv("BRAIN_API_URL")),
        check_unified_config(os.getenv("LLM_API_BASE")),
        check_google_genai_config(os.getenv("GEMINI_API_KEY")),
    ]
    errors = [p for p in problems if p is not None]
    if errors:
        raise ConfigurationError(
            "Invalid inference configuration:\n" + "\n".join(f"  - {e}" for e in errors)
        )
