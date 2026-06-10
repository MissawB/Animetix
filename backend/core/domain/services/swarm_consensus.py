# -*- coding: utf-8 -*-
"""
Swarm Consensus Orchestrator for Animetix Multi-Agent Swarms.
Applies a Paxos-style semantic voting consensus protocol to validate sémantiques facts.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field


logger = logging.getLogger("animetix.swarm.consensus")


class SwarmConsensusVotes(BaseModel):
    votes: Dict[str, float] = Field(
        ..., 
        description="Dictionnaire associant chaque nom d'agent à son score de confiance (entre 0.0 et 1.0)."
    )


class SwarmConsensusOrchestrator:
    def __init__(self, agent_names: Optional[List[str]] = None, inference_engine: Optional[Any] = None):
        self.agents = agent_names or [
            "VisualExpert", 
            "AcousticExpert", 
            "LoreExpert", 
            "LogicGate", 
            "SentimentScanner", 
            "TemporalGuard", 
            "StyleCritic"
        ]
        self.consensus_log: List[Dict[str, Any]] = []
        self.inference_engine = inference_engine

    def _get_swarm_votes_via_llm(self, fact: str, media: str) -> Dict[str, float]:
        """
        Interroge le moteur d'inférence pour obtenir les votes (scores de confiance) 
        des différents agents de l'essaim pour un fait donné sur un média.
        """
        agents_desc = "\n".join([f"- {name}" for name in self.agents])
        prompt = (
            f"Tu es l'arbitre d'un essaim d'agents d'IA analysant des faits sur des animés ou mangas.\n"
            f"Analyse le fait suivant concernant l'œuvre '{media}':\n"
            f"Fait : \"{fact}\"\n\n"
            f"Évalue le niveau de confiance de chacun des experts suivants sous la forme d'un score entre 0.0 et 1.0 :\n"
            f"{agents_desc}\n\n"
            f"Retourne un objet JSON contenant les scores pour chaque agent dans le champ 'votes'."
        )
        try:
            result = self.inference_engine.generate_structured(
                prompt=prompt,
                response_model=SwarmConsensusVotes,
                system_prompt="Tu es un orchestrateur d'essaim d'agents d'IA de consensus sémantique."
            )
            if isinstance(result, dict):
                return result.get("votes", {})
            elif result and hasattr(result, "votes"):
                return result.votes
            return {}
        except Exception as e:
            logger.warning(f"Failed to get swarm votes via LLM: {e}. Falling back to simulations.")
            return {}

    def get_paxos_diagnostics(self, fact: str, media_title: str, proposer: str = "ClientAPI") -> Dict[str, Any]:
        """
        Simule et retourne le détail technique du protocole Paxos-sémantique.
        """
        logger.info(f"🧬 Paxos-Semantic: Starting consensus for '{fact}'...")
        
        # Phase 1: Prepare/Promise (Simulation of agent availability)
        prepare_phase = {
            "proposal_id": f"px-{int(time.time())}",
            "proposer": proposer,
            "agents_contacted": self.agents,
            "promises_received": [a for a in self.agents if np.random.random() > 0.1] # 90% availability
        }

        # Phase 2: Propose/Accept (The actual voting)
        llm_votes = {}
        if self.inference_engine is not None:
            llm_votes = self._get_swarm_votes_via_llm(fact, media_title)

        votes = {}
        for agent in self.agents:
            if agent in llm_votes:
                votes[agent] = llm_votes[agent]
            else:
                votes[agent] = self._simulate_agent_vote(agent, fact, media_title)

        accept_phase = {
            "votes": votes,
            "threshold": 0.6,
            "quorum_required": len(self.agents) // 2 + 1
        }

        # Phase 3: Learn (Outcome)
        positive_votes = sum(1 for score in votes.values() if score >= 0.6)
        consensus_achieved = positive_votes >= accept_phase["quorum_required"]
        consensus_score = sum(votes.values()) / len(self.agents)

        outcome = {
            "consensus_achieved": consensus_achieved,
            "consensus_score": consensus_score,
            "paxos_state": "DECIDED" if consensus_achieved else "REJECTED",
            "message": "Fact integrated to Knowledge Graph" if consensus_achieved else "Consensus not reached"
        }

        return {
            "fact": fact,
            "media": media_title,
            "phases": {
                "prepare": prepare_phase,
                "accept": accept_phase,
                "learn": outcome
            },
            "is_recorded": consensus_achieved,
            "consensus_score": consensus_score,
            "votes": votes
        }

    def propose_fact(self, proposer: str, fact: str, media_title: str) -> Tuple[bool, float]:
        """
        Soumet un fait à l'essaim d'agents.
        Chaque agent vote en fonction d'un score heuristique/sémantique simulé ou évalué par un LLM.
        La majorité absolue est nécessaire pour valider le fait.
        """
        logger.info(f"🐝 Swarm: Proposing fact: '{fact}' for media '{media_title}' by agent '{proposer}'...")
        
        llm_votes = {}
        if self.inference_engine is not None:
            llm_votes = self._get_swarm_votes_via_llm(fact, media_title)

        votes = {}
        for agent in self.agents:
            if agent == proposer:
                votes[agent] = 1.0  # Le proposant vote toujours pour
            else:
                # Si l'agent a un score retourné par le LLM, on l'utilise
                if agent in llm_votes:
                    votes[agent] = llm_votes[agent]
                else:
                    # Sinon, simulation de vote sémantique basé sur la sensibilité de l'agent
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
