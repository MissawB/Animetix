import logging
from typing import Optional, List
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.domain.entities.ai_schemas import InferenceResponse
from adapters.inference.audio_mixin import AudioMixin

logger = logging.getLogger("animetix.inference.audio")


class AudioTransformersAdapter(AudioMixin, InferencePort):
    """
    Dedicated audio adapter using local models via AudioMixin.
    """

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

    def health_check(self) -> dict:
        return {
            "status": "online"
            if self._tts_model or self._audioldm_pipeline or self._moshi_model
            else "offline",
            "engine": "audio_transformers",
        }
