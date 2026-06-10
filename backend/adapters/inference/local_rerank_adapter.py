import logging
import os
from typing import List, Optional
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.domain.entities.ai_schemas import InferenceResponse

from adapters.inference.rerank_mixin import RerankMixin

logger = logging.getLogger("animetix.inference.rerank")

class LocalRerankAdapter(RerankMixin, InferencePort):
    def __init__(self, model_name: Optional[str] = None, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.reranker_model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.model_name = self.reranker_model_name
        self._cross_encoder = None

    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False, 
        include_logprobs: bool = False,
        **kwargs
    ) -> InferenceResponse:
        raise InferenceNotImplementedError("Text generation not supported by LocalRerankAdapter")

    def stream_generate(
        self, 
        prompt: str, 
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.", 
        thinking_budget: int = 0, 
        thinking_mode: bool = False, 
        include_logprobs: bool = False,
        **kwargs
    ):
        raise InferenceNotImplementedError("Streaming generation not supported by LocalRerankAdapter")

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError("Text embedding not supported by LocalRerankAdapter")

    def health_check(self) -> dict:
        return {"status": "online" if self._cross_encoder else "offline", "engine": "local_rerank"}
