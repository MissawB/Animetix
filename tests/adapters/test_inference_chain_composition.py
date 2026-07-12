"""The fallback chain must never route production traffic to a local-weight adapter.

Regression cover for the prod 503 of 2026-07-12: the web container (4 GiB) tried
Ollama on localhost, then loaded WeiboAI/VibeThinker-3B through `from_pretrained`
mid-request, exceeded the memory limit and was OOM-killed -- Cloud Run turned the
dead instance into a 503. The managed Brain API sat behind those adapters in the
chain and was never reached.
"""

import pytest
from animetix.containers.inference import build_inference_chain
from core.utils.inference_config import local_inference_enabled

# Sentinels: the composition is about ORDER and MEMBERSHIP, not about the
# adapters themselves.
UNIFIED = "unified(ollama)"
COMPACT = "compact_reasoning(3B local)"
LOCAL_TEXT = "local_text(transformers)"
BRAIN = "brain_api(remote)"
GEMINI = "google_genai(remote)"
GUARDRAIL = "local_guardrail(ollama-backed)"

LOCAL_WEIGHT_ADAPTERS = {UNIFIED, COMPACT, LOCAL_TEXT, GUARDRAIL}


def _chain(local_enabled):
    return build_inference_chain(
        local_enabled=local_enabled,
        unified=UNIFIED,
        compact_reasoning=COMPACT,
        local_text=LOCAL_TEXT,
        brain_api=BRAIN,
        google_genai=GEMINI,
        local_guardrail=GUARDRAIL,
    )


# --- composition ---------------------------------------------------------


def test_production_chain_has_no_local_adapter():
    """THE regression: a local adapter in the web container = OOM = 503."""
    chain = _chain(local_enabled=False)

    assert not LOCAL_WEIGHT_ADAPTERS.intersection(chain), (
        "a local-weight adapter reached the production chain: it will OOM-kill "
        "the 4 GiB Cloud Run instance on the first generate()"
    )


def test_production_chain_reaches_the_managed_backends():
    chain = _chain(local_enabled=False)

    assert chain == [BRAIN, GEMINI]  # brain first, Gemini as last resort


def test_development_chain_keeps_local_adapters_first():
    """Locally, free local inference stays the preferred path."""
    chain = _chain(local_enabled=True)

    assert chain[0] == UNIFIED
    assert LOCAL_WEIGHT_ADAPTERS.issubset(chain)
    assert BRAIN in chain and GEMINI in chain


def test_remote_backends_are_present_in_both_modes():
    for local_enabled in (True, False):
        chain = _chain(local_enabled)
        assert BRAIN in chain, "the managed API must always be reachable"
        assert GEMINI in chain, "the last resort must always be reachable"


# --- policy --------------------------------------------------------------


def test_local_inference_is_off_in_production_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LOCAL_INFERENCE", raising=False)

    assert local_inference_enabled(is_production=True) is False
    assert local_inference_enabled(is_production=False) is True


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_env_override_can_force_local_inference_on(monkeypatch, value):
    """A prod-like host WITH the RAM/GPU budget can opt back in."""
    monkeypatch.setenv("ENABLE_LOCAL_INFERENCE", value)

    assert local_inference_enabled(is_production=True) is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off"])
def test_env_override_can_force_local_inference_off(monkeypatch, value):
    monkeypatch.setenv("ENABLE_LOCAL_INFERENCE", value)

    assert local_inference_enabled(is_production=False) is False


def test_blank_override_falls_back_to_the_environment_default(monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_INFERENCE", "   ")

    assert local_inference_enabled(is_production=True) is False
