import logging
from typing import List, Optional

from adapters.inference.audio_mixin import AudioMixin
from adapters.inference.lazy_local_model_adapter import (
    LazyLocalModelAdapter,  # noqa: E402
)
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferenceNotImplementedError
from core.ports.usage_port import UsagePort

logger = logging.getLogger("animetix.inference.audio")


class AudioTransformersAdapter(AudioMixin, LazyLocalModelAdapter):
    """
    Dedicated audio adapter using local models via AudioMixin.
    """

    ENGINE_NAME = "audio_transformers"

    def _is_ready(self) -> bool:
        return bool(self._tts_model or self._audioldm_pipeline or self._moshi_model)

    def __init__(
        self,
        xtts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.xtts_model_name = xtts_model_name
        self._tts_model = None
        self._audioldm_pipeline = None
        self._moshi_model = None

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
            "Text generation not supported by AudioTransformersAdapter"
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
            "Streaming generation not supported by AudioTransformersAdapter"
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by AudioTransformersAdapter"
        )
