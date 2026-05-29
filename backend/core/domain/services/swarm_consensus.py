# -*- coding: utf-8 -*-
"""
Swarm Consensus Orchestrator for Animetix Multi-Agent Swarms.
Applies a Paxos-style semantic voting consensus protocol to validate sémantiques facts.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional


logger = logging.getLogger("animetix.swarm.consensus")

class SwarmConsensusOrchestrator:
    def __init__(self, agent_names: Optional[List[str]] = None):
        self.agents = agent_names or ["VisualExpert", "AcousticExpert", "LoreExpert"]
        self.consensus_log: List[Dict[str, Any]] = []

    def propose_fact(self, proposer: str, fact: str, media_title: str) -> Tuple[bool, float]:
        """
        Soumet un fait à l'essaim d'agents.
        Chaque agent vote en fonction d'un score heuristique/sémantique simulé.
        La majorité absolue est nécessaire pour valider le fait.
        """
        logger.info(f"🐝 Swarm: Proposing fact: '{fact}' for media '{media_title}' by agent '{proposer}'...")
        
        votes = {}
        for agent in self.agents:
            if agent == proposer:
                votes[agent] = 1.0  # Le proposant vote toujours pour
            else:
                # Simulation de vote sémantique basé sur la sensibilité de l'agent
                votes[agent] = self._simulate_agent_vote(agent, fact, media_title)
                
        # Calcul du verdict (Majorité absolue s'appuyant sur un seuil de confiance de 0.6)
        positive_votes = sum(1 for a, score in votes.items() if score >= 0.6)
        majority_achieved = positive_votes > len(self.agents) / 2
        consensus_score = sum(votes.values()) / len(self.agents)
        
        verdict = {
            "media": media_title,
            "fact": fact,
            "proposer": proposer,
            "votes": votes,
            "consensus_score": consensus_score,
            "majority_achieved": majority_achieved
        }
        
        if majority_achieved:
            self.consensus_log.append(verdict)
            logger.info(f"✅ Swarm Consensus Achieved! Fact recorded (Score: {consensus_score:.2f}).")
        else:
            logger.warning(f"❌ Swarm Consensus Failed! Fact rejected (Score: {consensus_score:.2f}).")
            
        return majority_achieved, consensus_score

    def _simulate_agent_vote(self, agent: str, fact: str, media: str) -> float:
        """
        Simule le vote sémantique d'un micro-agent.
        """
        f_lower = fact.lower()
        if agent == "VisualExpert":
            # Très sensible au style, animation, paysages, couleurs
            if any(w in f_lower for w in ["couleur", "visuel", "animation", "paysage", "dessin", "graphisme", "studio"]):
                return 0.85
            return 0.50
        elif agent == "AcousticExpert":
            # Très sensible à la musique, seiyuu, OST, sons, voix
            if any(w in f_lower for w in ["ost", "musique", "theme", "voix", "seiyuu", "opening", "ending", "son"]):
                return 0.90
            return 0.45
        elif agent == "LoreExpert":
            # Très sensible au scénario, arcs, fillers, mythes, tropes
            if any(w in f_lower for w in ["scénario", "lore", "arc", "filler", "trope", "histoire", "personnage"]):
                return 0.88
            return 0.52
            
        return 0.55
