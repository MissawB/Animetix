import os
import json
import time
from typing import List, Dict, Optional
from core.ports.inference_port import InferencePort

class RagasEvalService:
    """
    Service d'évaluation automatisé inspiré par le framework RAGAS.
    Mesure mathématiquement la qualité du RAG (Faithfulness, Relevancy).
    """
    def __init__(self, judge_engine: InferencePort):
        self.judge_engine = judge_engine

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
        prompt = f"""
        MISSIONS :
        1. Extrais les affirmations clés de la RÉPONSE.
        2. Pour chaque affirmation, vérifie si elle est présente dans le CONTEXTE.
        3. Calcule le ratio (affirmations supportées / total affirmations).
        
        CONTEXTE : {context[:2000]}
        RÉPONSE : {response}
        
        Réponds UNIQUEMENT par un chiffre entre 0 et 1.
        """
        res = self.judge_engine.generate(prompt, system_prompt="Tu es un auditeur de vérité IA.")
        try: return float(res.strip())
        except: return 0.5

    def _score_relevancy(self, query: str, response: str) -> float:
        """Pertinence : La réponse répond-elle directement à la question ?"""
        prompt = f"Sur une échelle de 0 à 1, à quel point cette RÉPONSE est-elle pertinente pour la QUESTION : '{query}' ? RÉPONSE : {response}. Réponds UNIQUEMENT par le chiffre."
        res = self.judge_engine.generate(prompt)
        try: return float(res.strip())
        except: return 0.5

    def _score_precision(self, query: str, context: str) -> float:
        """Précision du contexte : Le contexte contient-il l'information nécessaire ?"""
        prompt = f"Le CONTEXTE suivant contient-il la réponse à '{query}' ? {context[:1000]}. Réponds par 1 pour OUI, 0 pour NON."
        res = self.judge_engine.generate(prompt)
        try: return float(res.strip())
        except: return 0.0
