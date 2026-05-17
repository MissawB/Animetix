from typing import Generator, Optional
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager

class ResponseSynthesizer:
    """Agent responsable de la génération de la réponse finale."""
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager

    def synthesize_stream(self, query: str, context: str, thinking_budget: int = 0, thinking_mode: bool = False, correction_feedback: Optional[str] = None) -> Generator[str, None, None]:
        prompt_key = "synthesizer_correction" if correction_feedback else "synthesizer_final"
        syn_prompt, syn_sys = self.prompt_manager.get_prompt(prompt_key, query=query, context=context, feedback=correction_feedback)
        
        yield from self.inference_engine.stream_generate(
            syn_prompt, 
            syn_sys, 
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode
        )
