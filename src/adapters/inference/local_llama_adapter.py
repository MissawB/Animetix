import os
import requests
import logging
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
transformers = lazy_import('transformers')
AutoModelForCausalLM = transformers.AutoModelForCausalLM
AutoTokenizer = transformers.AutoTokenizer
BitsAndBytesConfig = transformers.BitsAndBytesConfig

from core.ports.usage_port import UsagePort

logger = logging.getLogger("animetix.inference")

class LocalLlamaAdapter(InferencePort):
    def __init__(self, model_path: str, hf_token: Optional[str] = None, use_4bit: bool = True, draft_model_path: Optional[str] = None, usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        # Lazy loading of model to avoid overhead
        
    def _load_model(self):
        if self.model: return
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path, device_map="auto", load_in_4bit=True)
        except Exception as e:
            logger.error(f"Failed to load local Llama model from {self.model_path}: {e}")

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        self._load_model()
        if not self.model: return "Erreur: Modèle local non chargé."
        
        # Simulation d'un support des flags
        mode_str = " (Thinking Mode ON)" if thinking_mode else ""
        budget_str = f" (Budget: {thinking_budget})" if thinking_budget > 0 else ""
        
        result = f"Réponse du modèle local{mode_str}{budget_str} pour: {prompt[:20]}..."
        
        self._log_usage(
            engine=f"llama:{self.model_path}",
            input_tokens=len(prompt) // 4,
            output_tokens=len(result) // 4
        )
        
        return result


    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    def health_check(self) -> dict:
        return {"status": "online", "engine": "Local-Llama" if self.model else "HF-API"}
