import numpy as np
import logging
from typing import Dict, List, Any, Optional
from core.ports.inference_port import InferencePort
from core.domain.entities.ai_schemas import (
    InferenceResponse, 
    XaiReport, 
    DocumentAttribution, 
    ModelDiagnostics
)

logger = logging.getLogger("animetix.xai")

class XaiDiagnosticService:
    """
    Service d'Analyse d'Interprétabilité (Explainable AI).
    """
    def __init__(self, inference_engine: InferencePort, uncertainty_service: Optional['UncertaintyService'] = None):
        self.inference_engine = inference_engine
        self.uncertainty_service = uncertainty_service or UncertaintyService(inference_engine)

    def explain_response(self, prompt: str, completion: str, response: Optional[InferenceResponse] = None) -> Dict[str, Any]:
        """
        Génère une explication technique de la réponse basée sur les logprobs réels.
        """
        logger.info("🔍 XAI: Analyzing native model logprobs...")
        
        top_influencers = []
        if response and response.metadata and response.metadata.logprobs:
            # Récupérer les tokens avec les logprobs les plus bas (plus grande surprise/attention)
            sorted_logprobs = sorted(
                [lp for lp in response.metadata.logprobs if lp.logprob is not None], 
                key=lambda x: x.logprob
            )
            top_influencers = [lp.token for lp in sorted_logprobs[:5]]

        if top_influencers:
            explanation = f"L'attention native du modèle indique une forte pondération ou surprise sur les tokens : {', '.join(top_influencers)}."
        else:
            explanation = "Analyse des tokens non disponible. Veuillez activer 'include_logprobs=True' lors de l'inférence."
        
        return {
            "explanation": explanation,
            "logit_lens_trend": [],
            "attention_map_summary": "L'analyse est désormais basée sur les logprobs natifs plutôt que sur des matrices d'attention approximées."
        }

    def generate_advanced_report(self, query: str, response: InferenceResponse, collector: 'XaiCollector') -> XaiReport:
        """
        Génère un rapport XAI complet hybridant logprobs natifs et traces agentiques.
        """
        logger.info(f"📊 XAI: Generating advanced diagnostic report for query: {query[:50]}...")
        
        # 1. Extraction des diagnostics natifs (logprobs)
        top_influential_tokens = []
        if response.metadata and response.metadata.logprobs:
            sorted_logprobs = sorted(
                [lp for lp in response.metadata.logprobs if lp.logprob is not None], 
                key=lambda x: x.logprob
            )
            top_influential_tokens = [lp.token for lp in sorted_logprobs[:10]]
            
        model_diagnostics = ModelDiagnostics(
            attention_heatmap=[],  # Deprecated with native logprobs
            top_influential_tokens=top_influential_tokens,
            logit_lens_trajectory=[] # Deprecated with native logprobs
        )
        
        # 2. Attribution documentaire (RAG)
        attributions = []
        total_score = sum(doc.get("score", 0.0) for doc in collector.retrieved_docs)
        
        for doc in collector.retrieved_docs:
            score = doc.get("score", 0.0)
            weight = score / total_score if total_score > 0 else 1.0 / len(collector.retrieved_docs) if collector.retrieved_docs else 0.0
            
            attributions.append(DocumentAttribution(
                document_id=doc.get("id", "unknown"),
                title=doc.get("title", "Untitled"),
                relevance_score=float(score),
                contribution_weight=float(weight)
            ))
            
        # 3. Calcul de l'incertitude
        uncertainty = self.uncertainty_service.measure_confidence(query, response.text, response)
        
        # 4. Assemblage du rapport final
        report = XaiReport(
            query_intent=collector.intent,
            retrieval_attribution=attributions,
            internal_diagnostics=model_diagnostics,
            uncertainty=uncertainty,
            agent_trace=collector.steps,
            final_confidence=uncertainty.get("confidence_score", 0.0)
        )
        
        return report

class UncertaintyService:
    """
    Service de Quantification de l'Incertitude utilisant exclusivement des mécanismes natifs.
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine
        self.uncertainty_threshold = 0.7 # Seuil de confiance

    def measure_confidence(self, prompt: str, completion: str, response: Optional[InferenceResponse] = None) -> Dict[str, Any]:
        """
        Calcule les métriques d'incertitude. Utilise les logprobs si disponibles, 
        sinon assume une incertitude maximale par sécurité (Secure by Default).
        """
        # Utilisation des logprobs réels si disponibles (InferenceResponse)
        if response and response.metadata and response.metadata.logprobs:
            logger.info("📊 Uncertainty: Using real logprobs from inference response.")
            logprobs = [lp.logprob for lp in response.metadata.logprobs if lp.logprob is not None]
            
            if logprobs:
                # L'entropie par token est approximée par -logprob (si on n'a que le top-1)
                # L'entropie moyenne est -sum(logprobs) / len(logprobs)
                avg_entropy = -sum(logprobs) / len(logprobs)
                
                # Normalisation (constante 10.8 empirique)
                confidence_score = max(0.0, min(1.0, 1.0 - (avg_entropy / 10.8)))
                
                # Perplexité = exp(entropie moyenne)
                perplexity = float(np.exp(avg_entropy))
                
                is_reliable = confidence_score >= self.uncertainty_threshold
                
                return {
                    "confidence_score": float(confidence_score),
                    "is_reliable": bool(is_reliable),
                    "perplexity": float(perplexity),
                    "action_required": "PROCEED" if is_reliable else "VERIFY_WEB",
                    "method": "real_logprobs"
                }

        # Fallback de sécurité (Secure by Default) si aucun logprob n'est fourni.
        # On ne charge PLUS de modèles lourds locaux comme gpt2.
        logger.warning("⚠️ Uncertainty: No native logprobs provided. Defaulting to high uncertainty.")
        
        confidence_score = 0.0
        is_reliable = False
        
        return {
            "confidence_score": confidence_score,
            "is_reliable": is_reliable,
            "perplexity": None,
            "action_required": "VERIFY_WEB",
            "method": "default_fallback"
        }

class XaiCollector:
    """
    Collecteur de métriques et pensées pour le rapport XAI final.
    """
    def __init__(self):
        self.steps = []
        self.retrieved_docs = []
        self.intent = ""

    def log_intent(self, intent: str):
        """Enregistre l'intention détectée."""
        self.intent = intent

    def log_retrieval(self, docs: List[Dict]):
        """Enregistre les documents récupérés."""
        self.retrieved_docs = docs

    def log_agent_thought(self, agent: str, thought: str):
        """Enregistre une étape de réflexion d'un agent."""
        self.steps.append({"agent": agent, "thought": thought})

