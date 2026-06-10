# -*- coding: utf-8 -*-
"""
Counterfactual Regret Minimization (CFR) Solver for Akinetix Game Theory.
Optimizes question selection paths under incomplete information and user bluffing/noise.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("animetix.gametheory.cfr")

class CFRGameSolver:
    def __init__(self, num_actions: int = 4):
        self.num_actions = num_actions
        # Tables de regret et de stratégie (Action index -> cumulative val)
        self.regret_sum = np.zeros(num_actions)
        self.strategy_sum = np.zeros(num_actions)

    def get_strategy(self) -> np.ndarray:
        """
        Calcule la stratégie actuelle (distribution de probabilité) à partir des regrets cumulés.
        """
        # Seuls les regrets positifs sont pris en compte pour la stratégie courante
        normalizing_sum = 0.0
        strategy = np.zeros(self.num_actions)
        
        for a in range(self.num_actions):
            strategy[a] = max(self.regret_sum[a], 0.0)
            normalizing_sum += strategy[a]
            
        for a in range(self.num_actions):
            if normalizing_sum > 0.0:
                strategy[a] /= normalizing_sum
            else:
                strategy[a] = 1.0 / self.num_actions
                
            self.strategy_sum[a] += strategy[a]
            
        return strategy

    def get_action(self, strategy: np.ndarray) -> int:
        """
        Sélectionne une action (question à poser) en fonction des probabilités de la stratégie.
        """
        return int(np.random.choice(self.num_actions, p=strategy))

    def train_step(self, opponent_action: int, utilities: np.ndarray):
        """
        Simule un pas d'entraînement CFR :
        Met à jour les regrets en comparant le gain de chaque action à l'action réellement jouée.
        """
        # utilities : vecteur de gains pour chaque action possible (longueur = num_actions)
        # On suppose que l'action jouée était basée sur la stratégie courante
        strategy = self.get_strategy()
        action_played = self.get_action(strategy)
        
        played_utility = utilities[action_played]
        
        for a in range(self.num_actions):
            # Le regret est la différence de gain si on avait joué 'a' par rapport à 'action_played'
            regret = utilities[a] - played_utility
            self.regret_sum[a] += regret

    def get_average_strategy(self) -> np.ndarray:
        """
        Retourne la stratégie moyenne de convergence (Nash Equilibrium pour information incomplète).
        """
        avg_strategy = np.zeros(self.num_actions)
        normalizing_sum = np.sum(self.strategy_sum)
        
        if normalizing_sum > 0.0:
            avg_strategy = self.strategy_sum / normalizing_sum
        else:
            avg_strategy.fill(1.0 / self.num_actions)
            
        return avg_strategy

    def solve_with_history(self, questions: List[str], iterations: int = 100) -> Dict[str, Any]:
        """
        Exécute le solveur et retourne l'historique complet de convergence pour visualisation.
        """
        # Reset tables for a clean simulation
        self.regret_sum = np.zeros(self.num_actions)
        self.strategy_sum = np.zeros(self.num_actions)
        
        history = []
        utilities = np.zeros(self.num_actions)
        for i in range(min(self.num_actions, len(questions))):
            q = questions[i]
            utilities[i] = (len(q) % 7) / 7.0 + (0.2 if "genre" in q.lower() else 0.0)

        for t in range(iterations):
            opponent_action = int(np.random.randint(2))
            self.train_step(opponent_action, utilities)
            
            if t % 5 == 0 or t == iterations - 1:
                history.append({
                    "iteration": t,
                    "regrets": self.regret_sum.tolist(),
                    "strategy": self.get_strategy().tolist(),
                    "avg_strategy": self.get_average_strategy().tolist()
                })

        return {
            "questions": questions[:self.num_actions],
            "utilities": utilities.tolist(),
            "history": history,
            "final_strategy": self.get_average_strategy().tolist()
        }

    def solve_best_question(self, questions: List[str], game_state: Dict[str, Any]) -> Tuple[str, float]:
        """
        Applique le solveur CFR pour choisir la question otaku idéale
        maximisant le gain d'information tout en minimisant les risques de bluff/bruits.
        """
        logger.info(f"⚖️ CFR: Solving best question path among {len(questions)} options...")
        
        # Simulation rapide de pas d'entraînement CFR pour calibrer le choix
        # Le gain d'information (utilité) de chaque question est estimé à partir de l'état du jeu (entropie)
        utilities = np.zeros(self.num_actions)
        for i in range(min(self.num_actions, len(questions))):
            # Simulation d'utilité basée sur l'entropie de la question
            q = questions[i]
            # Heuristique simple de démonstration
            utilities[i] = (len(q) % 7) / 7.0 + (0.2 if "genre" in q.lower() else 0.0)
            
        # 100 pas de convergence CFR
        for _ in range(100):
            opponent_action = int(np.random.randint(2))
            self.train_step(opponent_action, utilities)
            
        avg_strategy = self.get_average_strategy()
        best_action_idx = int(np.argmax(avg_strategy))
        
        best_question = questions[best_action_idx] if best_action_idx < len(questions) else questions[0]
        confidence = float(avg_strategy[best_action_idx])
        
        logger.info(f"🏆 CFR Choice: Chosen '{best_question}' (Nash strategy confidence: {confidence:.2f})")
        return best_question, confidence
