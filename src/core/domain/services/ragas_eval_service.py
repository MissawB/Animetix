import os
import json
import time
import logging
from typing import List, Dict, Optional
from core.ports.inference_port import InferencePort
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.ragas")

class RagasEvalService:
    """
    Service d'évaluation automatisé inspiré par le framework RAGAS.
    Mesure mathématiquement la qualité du RAG (Faithfulness, Relevancy).
    """
    def __init__(self, judge_engine: InferencePort, prompt_manager: PromptManager = None):
        self.judge_engine = judge_engine
        self.prompt_manager = prompt_manager

    def evaluate_response(self, query: str, context: str, response: str) -> Dict[str, float]:
        """
        Calcule les scores de qualité pour une interaction RAG donnée et enregistre le résultat.
        """
        scores = {
            "faithfulness": self._score_faithfulness(context, response),
            "answer_relevancy": self._score_relevancy(query, response),
            "context_precision": self._score_precision(query, context)
        }
        
        # Détection d'hallucination (seuil arbitraire)
        hallucination = scores['faithfulness'] < 0.3
        
        # Persistance (si Django est disponible)
        try:
            from animetix.models import AIREvalResult
            AIREvalResult.objects.create(
                query=query,
                response=response,
                context=context,
                faithfulness=scores['faithfulness'],
                relevancy=scores['answer_relevancy'],
                precision=scores['context_precision'],
                hallucination_detected=hallucination
            )
        except ImportError:
            pass
            
        return scores

    def _score_faithfulness(self, context: str, response: str) -> float:
        """Fidélité : La réponse est-elle supportée par le contexte ? (0.0 à 1.0)"""
        prompt, system_prompt = self.prompt_manager.get_prompt("ragas_faithfulness_calc", context=context[:2000], response=response)
        res = self.judge_engine.generate(prompt, system_prompt=system_prompt)
        try:
            return float(res.strip())
        except Exception as e:
            logger.warning(f"RAGAS Faithfulness scoring failed (raw response: '{res}'): {e}")
            return 0.5

    def _score_relevancy(self, query: str, response: str) -> float:
        """Pertinence : La réponse répond-elle directement à la question ?"""
        prompt, _ = self.prompt_manager.get_prompt("ragas_relevance_eval", query=query, response=response)
        res = self.judge_engine.generate(prompt)
        try:
            return float(res.strip())
        except Exception as e:
            logger.warning(f"RAGAS Relevancy scoring failed (raw response: '{res}'): {e}")
            return 0.5

    def _score_precision(self, query: str, context: str) -> float:
        """Précision du contexte : Le contexte contient-il l'information nécessaire ?"""
        prompt, _ = self.prompt_manager.get_prompt("ragas_faithfulness_eval", query=query, context=context)
        res = self.judge_engine.generate(prompt)
        try:
            return float(res.strip())
        except Exception as e:
            logger.warning(f"RAGAS Context Precision scoring failed (raw response: '{res}'): {e}")
            return 0.0
