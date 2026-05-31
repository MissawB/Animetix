import logging
from typing import Optional, Dict, Any
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from adapters.inference.audio_mixin import AudioMixin

logger = logging.getLogger("animetix.inference.audio_transformers")

class AudioTransformersAdapter(AudioMixin, InferencePort):
    """
    Dedicated audio adapter using local models via AudioMixin.
    """
    def __init__(
        self, 
        xtts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        usage_port: Optional[UsagePort] = None
    ):
        super().__init__(usage_port=usage_port)
        self.xtts_model_name = xtts_model_name
        self._tts_model = None
        self._audioldm_pipeline = None
        self._moshi_model = None

    def health_check(self) -> dict: 
        return {
            "status": "online" if self._tts_model or self._audioldm_pipeline or self._moshi_model else "offline", 
            "engine": "audio_transformers"
        }
