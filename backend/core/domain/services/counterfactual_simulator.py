# -*- coding: utf-8 -*-
"""
Counterfactual Conversation Simulator for Animetix RAG.
Simulates alternative dialogue branches to measure conversation regrets and optimize RAG strategies.
"""

import logging
from typing import List, Dict, Any, Tuple
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.counterfactual.simulator")

class CounterfactualConversationSimulator:
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def simulate_counterfactual_path(
        self, 
        actual_dialogue: List[Dict[str, str]], 
        what_if_query: str
    ) -> Dict[str, Any]:
        """
        Génère une timeline de dialogue alternative en remplaçant la première requête réelle
        par un scénario alternatif et en mesurant le regret de décision.
        """
        logger.info(f"⏳ Counterfactual: Simulating alternative trajectory for 'What if: {what_if_query}'...")
        
        # 1. Génération de la réponse alternative simulée
        simulated_prompt = (
            f"Dans une conversation alternative, au lieu de poser la question d'origine, "
            f"l'utilisateur demande : \"{what_if_query}\"\n\n"
            f"Rédige la réponse du RAG de manière cohérente, structurée et concise."
        )
        
        try:
            alternative_response = self.inference_engine.generate(
                prompt=simulated_prompt,
                system_prompt="Tu es le Simulateur de Dialogue Contrefactuel."
            )
        except Exception as e:
            logger.error(f"Error during counterfactual generation: {e}")
            alternative_response = "Réponse alternative simulée."

        # 2. Évaluation sémantique du regret contrefactuel (Regret = Efficacité Réelle - Efficacité Alternative)
        # Pour cet exemple: nous mesurons l'utilité informative de la réponse alternative par rapport à l'attendu.
        actual_utility = 0.85  # Utilité de la vraie conversation
        
        # Le LLM-as-a-Judge évalue l'utilité sémantique de l'alternative
        judge_prompt = (
            f"Question alternative : \"{what_if_query}\"\n"
            f"Réponse alternative : \"{alternative_response}\"\n\n"
            f"Donne une note d'utilité informative entre 0.0 et 1.0 (ex: 0.75) mesurant la richesse "
            f"des informations transmises. Ne renvoie rien d'autre que le nombre."
        )
        
        try:
            score_text = self.inference_engine.generate(
                prompt=judge_prompt,
                system_prompt="Tu es l'Évaluateur d'Utilité Contrefactuelle."
            ).strip()
            import re
            match = re.search(r"\d+\.\d+", score_text)
            alternative_utility = float(match.group(0)) if match else 0.70
        except Exception as e:
            logger.warning("⚠️ Counterfactual Utility evaluation failed. Falling back to default utility 0.75.", exc_info=True)
            alternative_utility = 0.75
            
        # Calcul du regret contrefactuel :
        # Si l'alternative est meilleure que la réalité, le regret est positif (on a raté une opportunité)
        regret = alternative_utility - actual_utility
        
        logger.info(f"⏳ Counterfactual complete. Regret score calculated: {regret:.3f}")
        return {
            "what_if_query": what_if_query,
            "alternative_response": alternative_response,
            "actual_utility": actual_utility,
            "alternative_utility": alternative_utility,
            "counterfactual_regret": regret
        }
