import logging
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.scout")


class ScoutAgent:
    """
    Agent SOTA 2026 responsable de la distillation du contexte.
    Transforme les résultats bruts en un 'Chemin de Vérité' (Truth Path) cohérent.
    """

    def __init__(
        self, llm_service: LLMService, prompt_manager: PromptManager, neo4j_manager=None
    ):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.neo4j_manager = neo4j_manager

    def find_truth_path(self, query: str, plan, raw_context: str) -> str:
        """Filtre le bruit et extrait les faits essentiels du contexte brut."""
        logger.info("📡 Scout: Distilling raw context into a Truth Path...")

        try:
            # Si le contexte est trop petit, pas besoin de distiller
            if len(raw_context) < 500:
                return raw_context

            prompt, sys = self.prompt_manager.get_prompt(
                "scout_distiller", query=query, context=raw_context
            )

            # On utilise un modèle léger (SLM) pour cette tâche de filtrage
            truth_path = self.llm_service.generate(prompt, sys, use_slm=True)

            if not truth_path or len(truth_path) < 50:
                return raw_context[:2000]  # Fallback sémantique

            return truth_path
        except Exception as e:
            logger.error(
                f"❌ Scout Distillation failed: {e}. Falling back to raw context."
            )
            return raw_context[:3000]  # Fallback de secours
