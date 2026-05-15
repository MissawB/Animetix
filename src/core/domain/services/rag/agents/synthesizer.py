from typing import Generator
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager

class ResponseSynthesizer:
    """Agent responsable de la génération de la réponse finale."""
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def synthesize_stream(self, query: str, context: str, thinking_budget: int = 0) -> Generator[str, None, None]:
        syn_prompt, syn_sys = self.prompt_manager.get_prompt("synthesizer_final", query=query, context=context)
        
        yield from self.inference_engine.stream_generate(
            syn_prompt, 
            syn_sys, 
            thinking_budget=thinking_budget
        )
