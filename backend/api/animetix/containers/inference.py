import os
from django.conf import settings
from dependency_injector import containers, providers

class LazyClass:
    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name
        self._class = None
    
    def __call__(self, *args, **kwargs):
        if self._class is None:
            import importlib
            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class(*args, **kwargs)









class InferenceContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    unified_inference_adapter = providers.Singleton(
        LazyClass("adapters.inference.unified_inference_adapter", "UnifiedInferenceAdapter"),
        api_base=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        model_name=os.getenv("LLM_MODEL_NAME", "llama3")
    )

    local_text_adapter = providers.Singleton(
        LazyClass("adapters.inference.local_text_adapter", "LocalTextAdapter"),
        model_id=os.getenv("LOCAL_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
        use_4bit=True,
        usage_port=infrastructure.usage_port
    )

    google_genai_adapter = providers.Singleton(
        LazyClass("adapters.inference.google_genai_adapter", "GoogleGenAIAdapter"),
        api_key=os.getenv("GEMINI_API_KEY"),
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "animetix"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west9"),
        model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
        usage_port=infrastructure.usage_port
    )

    local_guardrail_adapter = providers.Singleton(
        LazyClass("adapters.inference.local_guardrail_adapter", "LocalGuardrailAdapter"),
        inference_engine=unified_inference_adapter
    )

    brain_api_adapter = providers.Singleton(
        LazyClass("adapters.inference.brain_api_adapter", "BrainAPIAdapter"),
        api_url=os.getenv("BRAIN_API_URL", ""),
        api_key=settings.BRAIN_API_KEY
    )

    inference_engine = providers.Singleton(
        LazyClass("adapters.inference.fallback_adapter", "FallbackInferenceAdapter"),
        adapters=providers.List(
            unified_inference_adapter, # 1. Local Ollama (FREE)
            local_text_adapter,        # 2. Local Transformers (FREE fallback)
            brain_api_adapter,          # 3. Central Brain API (MANAGED)
            google_genai_adapter,       # 4. External Gemini (LAST RESORT)
            local_guardrail_adapter
        ),
        obs_service=infrastructure.obs_service
    )
