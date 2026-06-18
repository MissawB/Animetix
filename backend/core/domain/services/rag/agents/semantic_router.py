import logging
from pydantic import BaseModel, Field
from core.domain.services.llm_service import LLMService
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.rag.semantic_router")


class RoutingDecision(BaseModel):
    decision: str = Field(
        description="La classification de la requête: soit 'SIMPLE', soit 'COMPLEX'"
    )
    rationale: str = Field(description="Explication concise du choix de classification")


class SemanticRouter:
    """
    Semantic Router ultra-léger basé sur un modèle SLM (1.5B/3B) ou LLM pour catégoriser
    les requêtes utilisateur et court-circuiter l'orchestrateur d'agents complet s'il s'agit
    d'une question simple et directe.
    """

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def classify(self, query: str) -> str:
        prompt = (
            f"Analyse la requête de l'utilisateur suivante et détermine si elle est SIMPLE ou COMPLEXE.\n"
            f'Requête : "{query}"\n\n'
            f"Consignes de classification :\n"
            f"- SIMPLE : Une question directe demandant des faits précis (ex: auteur, studio, date de sortie, seiyū, comédien de doublage, maison d'édition, nombre de saisons/épisodes, opening de manga ou anime), sans comparaison complexe, sans spéculation, sans théorie croisée.\n"
            f"- COMPLEX : Une question transversale (ex: comparer des thèmes de deux œuvres), de lore profond, de théorie de fan, de spéculation logique, de déduction ou nécessitant un débat approfondi, ou une question avec négation/absurde.\n\n"
            f"Retourne obligatoirement un JSON valide avec les clés 'decision' ('SIMPLE' ou 'COMPLEX') et 'rationale' (explication concise)."
        )
        system_prompt = "Tu es un routeur sémantique d'élite. Sois précis et rapide."

        try:
            decision = self.llm_service.generate_structured(
                prompt=prompt,
                schema=RoutingDecision,
                system_prompt=system_prompt,
                use_slm=True,  # Utilise le SLM ultra-léger pour réduire le temps d'inférence
            )
            logger.info(
                f"🚦 Semantic Router: Decision={decision.decision} for query='{query}' (Rationale: {decision.rationale})"
            )
            if decision.decision in ["SIMPLE", "COMPLEX"]:
                return decision.decision
            return "COMPLEX"
        except Exception as e:
            logger.error(f"❌ Semantic Router failed: {e}. Defaulting to COMPLEX.")
            return "COMPLEX"
