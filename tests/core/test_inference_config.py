"""Unit tests for core.utils.inference_config (coherence-only guard-rails).

Pure functions: no network, no DNS. `validate_inference_config()` reads the
environment, so env is cleared per-test via monkeypatch and each test sets only
what it asserts on.
"""

import pytest
from core.domain.exceptions import ConfigurationError
from core.utils.inference_config import (
    check_brain_config,
    check_google_genai_config,
    check_unified_config,
    validate_inference_config,
)

INFERENCE_ENV = (
    "BRAIN_API_URL",
    "LLM_API_BASE",
    "GEMINI_API_KEY",
)


@pytest.fixture(autouse=True)
def _clean_inference_env(monkeypatch):
    # The repo .env may leak any of these; clear so validate_inference_config()
    # sees exactly what each test sets.
    for var in INFERENCE_ENV:
        monkeypatch.delenv(var, raising=False)


# --- check_brain_config: REQUIRED -------------------------------------------


@pytest.mark.parametrize("missing", [None, "", "   "])
def test_check_brain_config_required_when_missing(missing):
    assert check_brain_config(missing) == "BRAIN_API_URL is not configured"


def test_check_brain_config_malformed():
    msg = check_brain_config("not-a-url")
    assert msg is not None
    assert "BRAIN_API_URL" in msg and "malformed" in msg


def test_check_brain_config_ok():
    assert check_brain_config("https://brain.internal/api") is None


# --- check_unified_config: coherence-only -----------------------------------


@pytest.mark.parametrize("absent", [None, "", "   "])
def test_check_unified_config_absent_is_ok(absent):
    # Absent/blank -> the adapter falls back to the localhost default: OK.
    assert check_unified_config(absent) is None


def test_check_unified_config_default_localhost_ok():
    assert check_unified_config("http://localhost:11434/v1") is None


def test_check_unified_config_malformed_raises_message():
    msg = check_unified_config("ftp://nope")
    assert msg is not None and "LLM_API_BASE" in msg


def test_check_unified_config_no_netloc():
    assert check_unified_config("http://") is not None


# --- check_google_genai_config: coherence-only ------------------------------


def test_check_google_genai_config_absent_is_ok():
    # None -> Vertex / degraded path: OK.
    assert check_google_genai_config(None) is None


def test_check_google_genai_config_present_ok():
    assert check_google_genai_config("a-real-key") is None


@pytest.mark.parametrize("blank", ["", "   "])
def test_check_google_genai_config_blank_raises(blank):
    msg = check_google_genai_config(blank)
    assert msg is not None and "GEMINI_API_KEY" in msg


# --- validate_inference_config: aggregation ---------------------------------


def test_validate_ok_when_brain_set(monkeypatch):
    monkeypatch.setenv("BRAIN_API_URL", "https://brain.internal/api")
    # unified/google_genai absent -> degraded, OK. Should not raise.
    validate_inference_config()


def test_validate_aggregates_all_problems(monkeypatch):
    # BRAIN missing + LLM_API_BASE malformed + GEMINI blank -> ONE error, 3 lines.
    monkeypatch.setenv("LLM_API_BASE", "not-a-url")
    monkeypatch.setenv("GEMINI_API_KEY", "  ")
    with pytest.raises(ConfigurationError) as exc:
        validate_inference_config()
    text = str(exc.value)
    assert "BRAIN_API_URL is not configured" in text
    assert "LLM_API_BASE" in text
    assert "GEMINI_API_KEY" in text
