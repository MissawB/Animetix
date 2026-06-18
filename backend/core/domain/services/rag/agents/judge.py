import logging
from core.domain.entities.ai_schemas import JudgeEvaluation, JudgeAction
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager
from core.domain.exceptions import InferenceError, InfrastructureError

logger = logging.getLogger("animetix.rag.judge")


class ResponseJudge:
    """Agent responsable de l'évaluation finale de la qualité et de la fiabilité de la réponse."""

    def __init__(
        self, llm_service: LLMService, prompt_manager: PromptManager, obs_service=None
    ):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.obs_service = obs_service

    def evaluate(self, query: str, context: str, answer: str) -> JudgeEvaluation:
        eval_prompt, eval_sys = self.prompt_manager.get_prompt(
            "answer_judge", query=query, context=context, answer=answer
        )

        try:
            eval_raw = self.llm_service.generate(eval_prompt, eval_sys, use_slm=True)

            import orjson  # noqa: E402

            if "{" in eval_raw and "}" in eval_raw:
                data = orjson.loads(
                    eval_raw[eval_raw.find("{") : eval_raw.rfind("}") + 1]
                )
                evaluation = JudgeEvaluation(**data)

                # Check for method existence to prevent AttributeError
                if self.obs_service and hasattr(self.obs_service, "log_dynamic_eval"):
                    self.obs_service.log_dynamic_eval(
                        query, context, answer, evaluation
                    )

                return evaluation
        except (InferenceError, InfrastructureError) as e:
            logger.error(f"Judge generation failed due to AI/Infrastructure error: {e}")
            return JudgeEvaluation(
                faithfulness_score=0.0,
                relevancy_score=0.0,
                hallucination_detected=True,
                reasoning=f"AI/Infrastructure error during judgment: {str(e)}",
                is_reliable=False,
                next_action=JudgeAction.REWRITE,
            )
        except Exception as e:
            logger.error(f"Unexpected error in ResponseJudge: {e}", exc_info=True)
            return JudgeEvaluation(
                faithfulness_score=0.0,
                relevancy_score=0.0,
                hallucination_detected=True,
                reasoning=f"Internal error during judgment: {str(e)}",
                is_reliable=False,
                next_action=JudgeAction.REWRITE,
            )

        return JudgeEvaluation(
            faithfulness_score=0.0,
            relevancy_score=0.0,
            hallucination_detected=True,
            reasoning="Invalid or empty response from Judge",
            is_reliable=False,
            next_action=JudgeAction.REWRITE,
        )
