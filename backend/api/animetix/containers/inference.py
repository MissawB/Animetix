import os
import sys

from core.utils.gemini_models import GEMINI_FLASH
from core.utils.inference_config import (
    local_inference_enabled,
    validate_inference_config,
)
from core.utils.local_models import (
    COMPACT_REASONING_MODEL,
    LLM_OLLAMA_MODEL,
    LOCAL_DIFFUSION_MODEL_ID,
    LOCAL_TEXT_MODEL,
)
from dependency_injector import containers, providers
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .lazy import LazyClass

try:
    is_testing = (
        settings.configured
        and settings.SETTINGS_MODULE == "animetix_project.test_settings"
    )
except ImproperlyConfigured:
    is_testing = False

# `collectstatic` runs at image-build time, where no inference backend is
# configured and none is needed; the startup guardrail must not fail the build.
is_collectstatic = "collectstatic" in sys.argv

if not is_testing and not is_collectstatic:
    validate_inference_config()

LOCAL_INFERENCE_ENABLED = local_inference_enabled(
    getattr(settings, "IS_PRODUCTION", False)
)


def build_inference_chain(
    *,
    local_enabled: bool,
    unified,
    compact_reasoning,
    local_text,
    brain_api,
    google_genai,
    local_guardrail,
):
    """Order the fallback chain for the host we are actually running on.

    In the web container the three local adapters cannot work -- there is no
    Ollama on localhost, and loading transformers weights OOM-kills the 4 GiB
    instance -- yet they sit AHEAD of the managed Brain API, so the process died
    before ever reaching a backend that works. Off-host, the chain is remote-only.
    """
    if not local_enabled:
        return [brain_api, google_genai]
    return [
        unified,  # 1. Local Ollama (FREE)
        compact_reasoning,  # 2. Compact Reasoning Core (3B optimized)
        local_text,  # 3. Local Transformers (FREE fallback)
        brain_api,  # 4. Central Brain API (MANAGED)
        google_genai,  # 5. External Gemini (LAST RESORT)
        local_guardrail,
    ]


class InferenceContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    unified_inference_adapter = providers.Singleton(
        LazyClass(
            "adapters.inference.unified_inference_adapter", "UnifiedInferenceAdapter"
        ),
        api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        model_name=LLM_OLLAMA_MODEL,
    )

    local_text_adapter = providers.Singleton(
        LazyClass("adapters.inference.local_text_adapter", "LocalTextAdapter"),
        model_id=LOCAL_TEXT_MODEL,
        use_4bit=True,
        usage_port=infrastructure.usage_port,
    )

    google_genai_adapter = providers.Singleton(
        LazyClass("adapters.inference.google_genai_adapter", "GoogleGenAIAdapter"),
        api_key=os.getenv("GEMINI_API_KEY"),
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "animetix"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west9"),
        model_name=GEMINI_FLASH,
        usage_port=infrastructure.usage_port,
    )

    local_guardrail_adapter = providers.Singleton(
        LazyClass(
            "adapters.inference.local_guardrail_adapter", "LocalGuardrailAdapter"
        ),
        inference_engine=unified_inference_adapter,
    )

    brain_api_adapter = providers.Singleton(
        LazyClass("adapters.inference.brain_api_adapter", "BrainAPIAdapter"),
        api_url=os.getenv("BRAIN_API_URL", ""),
        api_key=settings.BRAIN_API_KEY,
    )

    compact_reasoning_adapter = providers.Singleton(
        LazyClass(
            "adapters.inference.compact_reasoning_adapter", "CompactReasoningAdapter"
        ),
        model_id=COMPACT_REASONING_MODEL,
        use_4bit=True,
        usage_port=infrastructure.usage_port,
    )

    diffusers_adapter = providers.Singleton(
        LazyClass("adapters.inference.diffusers_adapter", "DiffusersAdapter"),
        model_id=LOCAL_DIFFUSION_MODEL_ID,
        use_fp16=True,
        usage_port=infrastructure.usage_port,
    )

    inference_engine = providers.Singleton(
        LazyClass("adapters.inference.fallback_adapter", "FallbackInferenceAdapter"),
        adapters=providers.List(
            *build_inference_chain(
                local_enabled=LOCAL_INFERENCE_ENABLED,
                unified=unified_inference_adapter,
                compact_reasoning=compact_reasoning_adapter,
                local_text=local_text_adapter,
                brain_api=brain_api_adapter,
                google_genai=google_genai_adapter,
                local_guardrail=local_guardrail_adapter,
            )
        ),
        obs_service=infrastructure.obs_service,
    )
