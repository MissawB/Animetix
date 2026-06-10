import os
from django.conf import settings
from dependency_injector import containers, providers

from adapters.inference.local_guardrail_adapter import LocalGuardrailAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter
from adapters.inference.google_genai_adapter import GoogleGenAIAdapter

class InferenceContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()



    google_genai_adapter = providers.Singleton(
        GoogleGenAIAdapter,
        api_key=os.getenv("GEMINI_API_KEY"),
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "animetix"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west9"),
        model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash"),
        usage_port=infrastructure.usage_port
    )

    unified_inference_adapter = providers.Singleton(
        UnifiedInferenceAdapter,
        api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        model_name=os.getenv("LLM_MODEL_NAME", "llama3")
    )

    local_guardrail_adapter = providers.Singleton(
        LocalGuardrailAdapter,
        inference_engine=unified_inference_adapter
    )

    brain_api_adapter = providers.Singleton(
        BrainAPIAdapter,
        api_url=os.getenv("BRAIN_API_URL", ""),
        api_key=settings.BRAIN_API_KEY
    )

    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            google_genai_adapter,
            brain_api_adapter,
            unified_inference_adapter,
            local_guardrail_adapter
        ),
        obs_service=infrastructure.obs_service
    )
