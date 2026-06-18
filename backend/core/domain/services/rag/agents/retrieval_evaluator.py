import logging

from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager
from pydantic import BaseModel, Field

logger = logging.getLogger("animetix.rag.retrieval_evaluator")


class EvaluationResult(BaseModel):
    relevance_score: float = Field(
        description="Score de pertinence globale du contexte par rapport à la question, entre 0.0 et 1.0"
    )
    is_sufficient: bool = Field(
        description="True si les documents contiennent suffisamment d'informations pour répondre précisément, False sinon"
    )
    missing_aspects: str = Field(
        description="Description concise des aspects manquants ou incomplets dans le contexte actuel"
    )
    corrective_query: str = Field(
        description="Requête de recherche corrective ciblée à exécuter sur le web si le contexte est insuffisant"
    )


class RetrievalEvaluator:
    """
    Retrieval Evaluator (CRAG) chargé de valider instantanément la pertinence
    et la complétude du contexte extrait par rapport à la requête initiale.
    Si le contexte est insuffisant, il propose une requête de recherche corrective.
    """

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def evaluate(self, query: str, context: str) -> EvaluationResult:
        prompt = (
            f"Évalue la pertinence et la complétude du contexte extrait par rapport à la question posée.\n"
            f'QUESTION : "{query}"\n\n'
            f"CONTEXTE EXTRAIT :\n{context}\n\n"
            f"Consignes :\n"
            f"1. Détermine si le contexte contient des informations directement pertinentes pour répondre à la question de manière complète et exacte sans spéculer.\n"
            f"2. Attribue un score de pertinence entre 0.0 et 1.0.\n"
            f"3. Si des faits cruciaux manquent, indique 'is_sufficient' = false et formule une requête corrective ciblée optimisée pour une recherche Web afin de combler ces lacunes précises.\n\n"
            f"Retourne un JSON valide respectant scrupuleusement le schéma demandé."
        )
        system_prompt = "Tu es un évaluateur sémantique de RAG d'élite (CRAG). Sois rigoureux, impartial et factuel."

        try:
            result = self.llm_service.generate_structured(
                prompt=prompt,
                schema=EvaluationResult,
                system_prompt=system_prompt,
                use_slm=True,  # Utilise le SLM rapide pour éviter les goulots d'étranglement
            )
            logger.info(
                f"🔍 Retrieval Evaluator (CRAG): Score={result.relevance_score:.2f}, Sufficient={result.is_sufficient} for query='{query}'"
            )
            return result
        except Exception as e:
            logger.error(
                f"❌ Retrieval Evaluation failed: {e}. Defaulting to sufficient."
            )
            return EvaluationResult(
                relevance_score=1.0,
                is_sufficient=True,
                missing_aspects="",
                corrective_query="",
            )
