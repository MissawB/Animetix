import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.utils.lazy_import import lazy_import
from core.domain.exceptions import InferenceError

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference")

class MoondreamAdapter(InferencePort):
    def __init__(self, model_id: str = "vikhyatk/moondream2", usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.model = None
        self.tokenizer = None

    def _load_model(self):
        if self.model: return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True)
        except Exception as e:
            logger.error(f"Failed to load Moondream model {self.model_id}: {e}")
            raise InferenceError(f"Failed to load Moondream model: {e}")

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        raise InferenceNotImplementedError("MoondreamAdapter only supports visual tasks.")

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        raise InferenceNotImplementedError("MoondreamAdapter only supports visual tasks.")

    def generate_image_description(self, image_data: bytes, prompt: str = "Describe this image.") -> str:
        self._load_model()
        if not self.model: 
            raise InferenceError("Moondream model not loaded.")

        # Real VLM logic would go here
        # For now, if we don't have the weights/logic, we should raise NotImplemented or provide a real implementation
        # The audit said it was a stub.
        raise InferenceNotImplementedError("Moondream visual description logic not fully implemented.")

    def health_check(self) -> dict:
        return {"status": "online" if self.model else "offline", "engine": "Moondream-VLM"}
