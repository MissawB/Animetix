import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference")

class MoondreamAdapter(InferencePort):
    def __init__(self, model_id: str = "vikhyatk/moondream2"):
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

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        # Moondream est principalement visuel, mais peut générer du texte
        mode_str = " (Thinking Mode ON)" if thinking_mode else ""
        return f"Moondream Text Response{mode_str} (Simulated)"

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    def generate_image_description(self, image_data: bytes, prompt: str = "Describe this image.") -> str:
        self._load_model()
        if not self.model: return "Erreur: Moondream non chargé."
        # ... logic VLM ...
        return "Description Moondream (Simulated)"

    def health_check(self) -> dict:
        return {"status": "online" if self.model else "offline", "engine": "Moondream-VLM"}
