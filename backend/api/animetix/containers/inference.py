import os
from django.conf import settings
from dependency_injector import containers, providers

from adapters.inference.moondream_adapter import MoondreamAdapter
from adapters.inference.manga_ocr_adapter import MangaOCRAdapter
from adapters.inference.local_rerank_adapter import LocalRerankAdapter
from adapters.inference.local_guardrail_adapter import LocalGuardrailAdapter
from adapters.inference.vision_transformers_adapter import VisionTransformersAdapter
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter

class InferenceContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    moondream_adapter = providers.Singleton(MoondreamAdapter)

    manga_ocr_adapter = providers.Singleton(MangaOCRAdapter)

    local_rerank_adapter = providers.Singleton(LocalRerankAdapter)

    vision_transformers_adapter = providers.Singleton(
        VisionTransformersAdapter,
        use_4bit=True
    )

    diffusers_adapter = providers.Singleton(
        DiffusersAdapter,
        model_id="stabilityai/sdxl-turbo",
        use_fp16=True,
        usage_port=infrastructure.usage_port
    )

    audio_transformers_adapter = providers.Singleton(
        AudioTransformersAdapter,
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
        brain_api_url=os.getenv("BRAIN_API_URL", ""),
        brain_api_key=settings.BRAIN_API_KEY
    )

    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            brain_api_adapter,
            unified_inference_adapter,
            manga_ocr_adapter,
            local_rerank_adapter,
            local_guardrail_adapter,
            diffusers_adapter,
            vision_transformers_adapter,
            audio_transformers_adapter,
            moondream_adapter
        ),
        obs_service=infrastructure.obs_service
    )
