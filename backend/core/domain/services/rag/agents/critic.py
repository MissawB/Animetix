import logging

from core.domain.entities.ai_schemas import CritiqueResult
from core.domain.exceptions import InferenceError, InfrastructureError
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.critic")


class ResponseCritic:
    """Agent responsable de l'évaluation de la pertinence du contexte récupéré."""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def evaluate(
        self,
        query: str,
        context: str,
        thinking_budget: int = 0,
        thinking_mode: bool = False,
    ) -> CritiqueResult:
        crit_prompt, crit_sys = self.prompt_manager.get_prompt(
            "critic_evaluation", query=query, context=context
        )

        try:
            crit_raw = self.llm_service.generate(
                crit_prompt,
                crit_sys,
                use_slm=True,
                thinking_budget=thinking_budget,
                thinking_mode=thinking_mode,
            )

            import orjson  # noqa: E402

            if "{" in crit_raw and "}" in crit_raw:
                data = orjson.loads(
                    crit_raw[crit_raw.find("{") : crit_raw.rfind("}") + 1]
                )
                return CritiqueResult(**data)
            else:
                logger.warning("Critic response did not contain JSON curly braces.")
        except (InferenceError, InfrastructureError) as e:
            logger.error(
                f"Critic generation failed due to AI/Infrastructure error: {e}"
            )
            return CritiqueResult(
                is_relevant=False,
                relevance_score=0.0,
                suggested_action="PROCEED",
                missing_info=f"Erreur d'inférence: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error in ResponseCritic: {e}", exc_info=True)
            return CritiqueResult(
                is_relevant=False,
                relevance_score=0.0,
                suggested_action="PROCEED",
                missing_info=f"Unexpected failure: {str(e)}",
            )

        logger.warning(
            "Critic returned malformed or incomplete output. Using conservative fallback."
        )
        return CritiqueResult(
            is_relevant=False,
            relevance_score=0.0,
            suggested_action="PROCEED",
            missing_info="Malformed critic output",
        )
