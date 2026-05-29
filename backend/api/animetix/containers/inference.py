import os
from django.conf import settings
from dependency_injector import containers, providers

from adapters.inference.gguf_adapter import GgufAdapter
from adapters.inference.moondream_adapter import MoondreamAdapter
from adapters.inference.manga_ocr_adapter import MangaOCRAdapter
from adapters.inference.local_text_adapter import LocalTextAdapter
from adapters.inference.local_rerank_adapter import LocalRerankAdapter
from adapters.inference.local_guardrail_adapter import LocalGuardrailAdapter
from adapters.inference.vision_transformers_adapter import VisionTransformersAdapter
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter
from adapters.inference.speculative_inference import SpeculativeDecodingInferenceAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.vllm_adapter import VllmAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter

class InferenceContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    gguf_adapter = providers.Singleton(
        GgufAdapter,
        model_path=os.path.join(settings.MODELS_DIR, "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"),
        clip_model_path=os.path.join(settings.MODELS_DIR, "llava-v1.5-7b-mmproj-Q4_0.gguf")
    )

    moondream_adapter = providers.Singleton(MoondreamAdapter)

    manga_ocr_adapter = providers.Singleton(MangaOCRAdapter)

    local_text_adapter = providers.Singleton(
        LocalTextAdapter,
        model_id="Qwen/Qwen2.5-1.5B-Instruct",
        use_4bit=True
    )

    local_rerank_adapter = providers.Singleton(LocalRerankAdapter)

    local_guardrail_adapter = providers.Singleton(LocalGuardrailAdapter)

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

    speculative_decoding_adapter = providers.Singleton(
        SpeculativeDecodingInferenceAdapter,
        verifier_engine=providers.Singleton(
            LocalTextAdapter,
            model_id="meta-llama/Meta-Llama-3-8B-Instruct",
            use_4bit=True
        ),
        draft_engine=providers.Singleton(
            LocalTextAdapter,
            model_id="HuggingFaceTB/SmolLM3-1.7B-Instruct",
            use_4bit=True
        )
    )

    unified_inference_adapter = providers.Singleton(
        UnifiedInferenceAdapter,
        api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        model_name=os.getenv("LLM_MODEL_NAME", "llama3")
    )

    inference_engine = providers.Singleton(
        FallbackInferenceAdapter,
        adapters=providers.List(
            manga_ocr_adapter,
            speculative_decoding_adapter,
            unified_inference_adapter,
            local_text_adapter,
            local_rerank_adapter,
            local_guardrail_adapter,
            gguf_adapter,
            diffusers_adapter,
            vision_transformers_adapter,
            audio_transformers_adapter,
            moondream_adapter,
            providers.Factory(
                VllmAdapter,
                api_base=os.getenv("VLLM_API_BASE", "http://vllm:8000/v1"),
                model_name="meta-llama/Llama-3-8B-Instruct"
            ),
            providers.Factory(
                BrainAPIAdapter,
                brain_api_url=os.getenv("BRAIN_API_URL", "")
            )
        ),
        obs_service=infrastructure.obs_service
    )
