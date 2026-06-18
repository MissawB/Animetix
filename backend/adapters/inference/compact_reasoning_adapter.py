import logging
from typing import Optional

from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.exceptions import InferenceError
from core.ports.usage_port import UsagePort

from .local_text_adapter import LocalTextAdapter

logger = logging.getLogger("animetix.inference.compact_reasoning")


class CompactReasoningAdapter(LocalTextAdapter):
    """
    Adaptateur spécialisé pour le raisonnement compact (Inspiré par VibeThinker-3B).
    Optimisé pour les tâches de logique et de vérification avec un faible nombre de paramètres.
    """

    def __init__(
        self,
        model_id: str = "WeiboAI/VibeThinker-3B",
        use_4bit: bool = True,
        usage_port: Optional[UsagePort] = None,
    ):
        # On utilise VibeThinker-3B par défaut si disponible, sinon un fallback raisonnable comme Qwen2.5-3B-Instruct
        super().__init__(model_id=model_id, use_4bit=use_4bit, usage_port=usage_port)
        self.engine_name = "compact-reasoning-core"

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en raisonnement logique et culture Anime.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        """
        Génère une réponse en forçant un format de pensée structuré si nécessaire.
        """
        # Pour VibeThinker et les modèles de raisonnement compacts, on peut enrichir le système de pensée
        if thinking_mode or thinking_budget > 0:
            enhanced_system = (
                f"{system_prompt}\n"
                "INSTRUCTION DE RAISONNEMENT : Analyse la requête étape par étape. "
                "Utilise des balises <thought> pour ta réflexion interne si le modèle le supporte natively, "
                "sinon simule un cheminement logique rigoureux."
            )
        else:
            enhanced_system = system_prompt

        try:
            # On délègue à LocalTextAdapter qui gère déjà le chargement et la génération de base
            response = super().generate(
                prompt=prompt,
                system_prompt=enhanced_system,
                thinking_budget=thinking_budget,
                thinking_mode=thinking_mode,
                include_logprobs=include_logprobs,
                **kwargs,
            )

            # On surcharge le logging d'usage pour marquer le moteur compact
            self._log_usage(
                engine=f"compact:{self.model_id}", allocated_budget=thinking_budget
            )

            return response
        except Exception as e:
            logger.error(f"Compact reasoning generation failed: {e}")
            raise InferenceError(f"Compact Reasoning Engine Failure: {str(e)}")

    def health_check(self) -> dict:
        status = super().health_check()
        status["adapter"] = "CompactReasoningAdapter"
        status["specialization"] = "VibeThinker-Ready"
        return status
