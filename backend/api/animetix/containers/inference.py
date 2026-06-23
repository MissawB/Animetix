import os

from core.domain.exceptions import ConfigurationError
from core.utils.gemini_models import GEMINI_FLASH
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

if not is_testing:
    if not os.getenv("BRAIN_API_URL"):
        raise ConfigurationError("BRAIN_API_URL is not configured")


class InferenceContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    unified_inference_adapter = providers.Singleton(
        LazyClass(
            "adapters.inference.unified_inference_adapter", "UnifiedInferenceAdapter"
        ),
        api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        model_name=os.getenv("LLM_MODEL_NAME", "llama3"),
    )

    local_text_adapter = providers.Singleton(
        LazyClass("adapters.inference.local_text_adapter", "LocalTextAdapter"),
        model_id=os.getenv("LOCAL_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
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
        model_id=os.getenv("COMPACT_MODEL_ID", "WeiboAI/VibeThinker-3B"),
        use_4bit=True,
        usage_port=infrastructure.usage_port,
    )

    diffusers_adapter = providers.Singleton(
        LazyClass("adapters.inference.diffusers_adapter", "DiffusersAdapter"),
        model_id=os.getenv("LOCAL_DIFFUSION_MODEL", "black-forest-labs/FLUX.1-schnell"),
        use_fp16=True,
        usage_port=infrastructure.usage_port,
    )

    inference_engine = providers.Singleton(
        LazyClass("adapters.inference.fallback_adapter", "FallbackInferenceAdapter"),
        adapters=providers.List(
            unified_inference_adapter,  # 1. Local Ollama (FREE)
            compact_reasoning_adapter,  # 2. Compact Reasoning Core (NEW - 3B optimized)
            local_text_adapter,  # 3. Local Transformers (FREE fallback)
            brain_api_adapter,  # 4. Central Brain API (MANAGED)
            google_genai_adapter,  # 5. External Gemini (LAST RESORT)
            local_guardrail_adapter,
        ),
        obs_service=infrastructure.obs_service,
    )
