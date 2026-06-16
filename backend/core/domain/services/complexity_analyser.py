# -*- coding: utf-8 -*-
"""
Complexity Analyser and Dynamic Budget TTC Selector for Animetix.
Calculates the required thought process depth and reasoning token budget.
"""

import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger("animetix.complexity")

class ComplexityAnalyser:
    def __init__(self, prompt_manager=None, llm_service=None):
        self.prompt_manager = prompt_manager
        self.llm_service = llm_service

    def assess_complexity(self, query: str) -> Tuple[int, int]:
        """
        Analyse la complexité de la requête et calcule le budget TTC dynamique.
        Retourne (thinking_budget, complexity_score).
        """
        # Analyse par mots-clés sémantiques en cas d'indisponibilité du LLM
        complexity_score = 0
        q_lower = query.lower()
        
        # Mots-clés indiquant une complexité moyenne (comparaisons, recs)
        medium_keywords = ["ressemble", "comparaison", "similaire", "recommande", "différence", "pourquoi"]
        # Mots-clés indiquant une complexité élevée (paradoxes, analyses scénaristiques, intrigues profondes)
        high_keywords = ["paradoxe", "intrus", "thème", "influence", "explication", "philosophique", "scénar", "scénario", "décors"]
        
        if any(w in q_lower for w in high_keywords):
            complexity_score = 2
        elif any(w in q_lower for w in medium_keywords):
            complexity_score = 1
            
        # Si le LLM et le PromptManager sont configurés, on utilise l'analyse cognitive
        if self.prompt_manager and self.llm_service:
            try:
                prompt, sys = self.prompt_manager.get_prompt("complexity_analyzer", query=query)
                res = self.llm_service.generate(prompt, sys, use_slm=True)
                
                # Parsing simple du JSON retourné
                import json
                import re
                match = re.search(r'\{.*\}', res, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    complexity_score = int(data.get("complexity_score", complexity_score))
            except Exception as e:
                logger.error(f"Error in cognitive complexity analysis: {e}. Falling back to keyword metrics.")

        # Calcul du budget dynamique TTC (DynamicBudgetTTCSelector)
        thinking_budget = self.select_dynamic_budget(complexity_score, query)
        
        logger.info(f"🧠 TTC Analysis: Complexity {complexity_score} -> Allocated Budget: {thinking_budget} tokens.")
        return thinking_budget, complexity_score

    def select_dynamic_budget(self, complexity_score: int, query: str) -> int:
        """
        Sélecteur dynamique de budget TTC (DynamicBudgetTTCSelector) :
        - Score 0 (Simple) : 0 tokens de réflexion.
        - Score 1 (Moyen) : 256 tokens de réflexion.
        - Score 2 (Complexe) : 1024 tokens de réflexion.
        """
        if complexity_score == 0:
            return 0
        elif complexity_score == 1:
            return 256
        else:
            # Pour des requêtes particulièrement longues ou complexes, on peut étendre le budget à 1500 tokens
            if len(query.split()) > 15:
                return 1500
            return 1024
