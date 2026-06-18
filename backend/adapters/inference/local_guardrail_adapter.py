import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from pydantic import BaseModel, Field
from core.domain.entities.ai_schemas import InferenceResponse

logger = logging.getLogger("animetix.inference.guardrail")


class ModerationResult(BaseModel):
    is_safe: bool = Field(
        ...,
        description="True si le texte ne contient aucun contenu inapproprié, offensant ou spoiler.",
    )
    detected_categories: List[str] = Field(
        ...,
        description="Liste des catégories inappropriées détectées (ex: 'nsfw', 'violence', 'spoiler', 'hate_speech').",
    )
    reason: str = Field(
        ..., description="Explication concise de la décision de modération."
    )


class LocalGuardrailAdapter(InferencePort):
    def __init__(self, inference_engine: Optional[Any] = None):
        super().__init__()
        self.inference_engine = inference_engine

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
            "Text generation not supported by LocalGuardrailAdapter"
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
            "Streaming generation not supported by LocalGuardrailAdapter"
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by LocalGuardrailAdapter"
        )

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        if self.inference_engine:
            try:
                return self.inference_engine.moderate_content(text, categories)
            except Exception as e:
                logger.warning(
                    f"Failed calling moderate_content on inference_engine, falling back: {e}"
                )

        return super().moderate_content(text, categories)

    def health_check(self) -> dict:
        return {"status": "online", "engine": "local_guardrail"}
