import logging
from typing import Any, List, Optional

from adapters.inference.lazy_local_model_adapter import LazyLocalModelAdapter
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.exceptions import InferenceError
from core.ports.inference_port import InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.lazy_import import lazy_import
from core.utils.model_registry import resolve_trust_remote_code, trusted_revision

torch = lazy_import("torch")
transformers = lazy_import("transformers")
PIL = lazy_import("PIL.Image")

logger = logging.getLogger("animetix.inference.moondream")


class MoondreamAdapter(LazyLocalModelAdapter):
    ENGINE_NAME = "SmolVLM"

    def __init__(
        self,
        model_id: str = "HuggingFaceTB/SmolVLM-Instruct",
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.model: Any = None
        self.processor: Any = None

    def _load_model_impl(self) -> None:
        import torch as _torch  # noqa: E402
        from transformers import (
            AutoModelForVision2Seq,  # noqa: E402
            AutoProcessor,
        )

        self.model = AutoModelForVision2Seq.from_pretrained(
            self.model_id,
            revision=trusted_revision(self.model_id) or "main",
            trust_remote_code=resolve_trust_remote_code(self.model_id),
            device_map="auto",
            torch_dtype=(
                _torch.bfloat16 if _torch.cuda.is_available() else _torch.float32
            ),
        )
        self.processor = AutoProcessor.from_pretrained(
            self.model_id, revision=trusted_revision(self.model_id) or "main"
        )

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
            "Pure text generation not supported by MoondreamAdapter"
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
            "Streaming generation not supported by MoondreamAdapter"
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by MoondreamAdapter"
        )

    def generate_image_description(
        self,
        image_data: bytes,
        prompt: str = "Décris cette image d'anime de manière très détaillée.",
    ) -> str:
        self._load_model()
        try:
            import io  # noqa: E402

            from PIL import Image  # noqa: E402

            image = Image.open(io.BytesIO(image_data)).convert("RGB")

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "image"}, {"type": "text", "text": prompt}],
                }
            ]

            text = self.processor.apply_chat_template(
                messages, add_generation_prompt=True
            )
            inputs = self.processor(text=text, images=[image], return_tensors="pt").to(
                self.model.device
            )

            generated_ids = self.model.generate(**inputs, max_new_tokens=512)
            description = self.processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

            # Clean up potential template artifacts
            if "Assistant:" in description:
                description = description.split("Assistant:")[-1].strip()

            self._log_usage(engine="local:smolvlm", units=1)
            return description
        except Exception as e:
            logger.error(f"SmolVLM visual description failed: {e}")
            raise InferenceError(f"SmolVLM visual description failed: {e}")
