import logging
from typing import List, Optional

from adapters.inference.image_gen_mixin import ImageGenMixin
from adapters.inference.lazy_local_model_adapter import (
    LazyLocalModelAdapter,  # noqa: E402
)
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.local_models import LOCAL_DIFFUSION_MODEL_ID

logger = logging.getLogger("animetix.inference.image")


class DiffusersAdapter(ImageGenMixin, LazyLocalModelAdapter):
    """
    Dedicated image generation adapter using local diffusion models via ImageGenMixin.
    """

    ENGINE_NAME = "diffusers"

    def _is_ready(self) -> bool:
        return bool(self.pipe or self._img2img_pipe or self._inpaint_pipe)

    def __init__(
        self,
        model_id: str = LOCAL_DIFFUSION_MODEL_ID,
        use_fp16: bool = True,
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.use_fp16 = use_fp16
        self.pipe = None
        self._img2img_pipe = None
        self._inpaint_pipe = None

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
            "Text generation not supported by DiffusersAdapter"
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
            "Streaming generation not supported by DiffusersAdapter"
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by DiffusersAdapter"
        )

    def health_check(self) -> dict:
        status = super().health_check()
        status["model"] = self.model_id
        return status
