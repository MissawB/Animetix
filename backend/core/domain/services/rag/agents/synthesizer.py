from typing import Generator, Optional

from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager


class ResponseSynthesizer:
    """Agent responsable de la génération de la réponse finale."""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def synthesize_stream(
        self,
        query: str,
        context: str,
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        use_slm: bool = False,
        correction_feedback: Optional[str] = None,
        language: str = "Français",
        xai_collector=None,
    ) -> Generator[InferenceResponse, None, None]:
        prompt_key = (
            "synthesizer_correction" if correction_feedback else "synthesizer_final"
        )
        syn_prompt, syn_sys = self.prompt_manager.get_prompt(
            prompt_key,
            query=query,
            context=context,
            feedback=correction_feedback,
            language=language,
        )

        if xai_collector:
            xai_collector.log_agent_thought(
                "Synthesizer", f"Génération de la réponse finale ({language})"
            )

        yield from self.llm_service.stream_generate(
            syn_prompt,
            syn_sys,
            use_slm=use_slm,
            thinking_budget=thinking_budget,
            thinking_mode=thinking_mode,
        )
