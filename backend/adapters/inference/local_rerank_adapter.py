import logging
from typing import List, Optional

from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.components.rerank_component import RerankComponent
from adapters.inference.lazy_local_model_adapter import (
    LazyLocalModelAdapter,  # noqa: E402
)
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.local_models import RERANKER_MODEL

logger = logging.getLogger("animetix.inference.rerank")


class LocalRerankAdapter(LazyLocalModelAdapter):
    ENGINE_NAME = "local_rerank"

    def _is_ready(self) -> bool:
        return self._rerank.is_loaded

    def __init__(
        self, model_name: Optional[str] = None, usage_port: Optional[UsagePort] = None
    ):
        super().__init__(usage_port=usage_port)
        self.reranker_model_name = model_name or RERANKER_MODEL
        self.model_name = self.reranker_model_name
        # No LLM on this adapter: generate=None disables the component's
        # prompt-based fallback instead of tripping on a raising generate().
        self._rerank = RerankComponent(
            InferenceComponentContext(log_usage=self._log_usage, generate=None),
            reranker_model_name=self.reranker_model_name,
        )

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        return self._rerank.rerank_documents(query, documents)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        raise InferenceNotImplementedError(
            "Text generation not supported by LocalRerankAdapter"
        )

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        raise InferenceNotImplementedError(
            "Streaming generation not supported by LocalRerankAdapter"
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by LocalRerankAdapter"
        )
