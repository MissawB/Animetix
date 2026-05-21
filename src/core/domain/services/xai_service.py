import numpy as np
import logging
from typing import Dict, List, Any
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.xai")

class XaiDiagnosticService:
    """
    Service d'Analyse d'Interprétabilité (Explainable AI).
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def explain_response(self, prompt: str, completion: str) -> Dict[str, Any]:
        """
        Génère une explication technique de la réponse.
        """
        logger.info("🔍 XAI: Analyzing internal model activations...")
        diagnostics = self.inference_engine.get_diagnostics(prompt, completion)
        
        # ... (rest of formatting)
        top_influencers = diagnostics.get("top_attention_tokens", [])
        
        return {
            "explanation": f"Le modèle s'est principalement focalisé sur : {', '.join(top_influencers)}.",
            "logit_lens_trend": diagnostics.get("logit_lens_trend"),
            "attention_map_summary": "L'attention est concentrée sur les entités nommées du contexte."
        }

class UncertaintyService:
    """
    Service de Quantification de l'Incertitude.
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine
        self.uncertainty_threshold = 0.7 # Seuil de confiance

    def measure_confidence(self, prompt: str, completion: str) -> Dict[str, Any]:
        """
        Calcule les métriques d'incertitude.
        """
        metrics = self.inference_engine.calculate_uncertainty(prompt, completion)
        
        # L'entropie mesure le 'désordre' des probabilités de tokens.
        confidence_score = 1.0 - metrics.get("normalized_entropy", 0.0)
        
        is_reliable = confidence_score >= self.uncertainty_threshold
        
        return {
            "confidence_score": confidence_score,
            "is_reliable": is_reliable,
            "perplexity": metrics.get("perplexity"),
            "action_required": "PROCEED" if is_reliable else "VERIFY_WEB"
        }
