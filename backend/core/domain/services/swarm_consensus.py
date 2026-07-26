# -*- coding: utf-8 -*-
"""
Swarm Consensus Orchestrator for Animetix Multi-Agent Swarms.
Applies a Paxos-style semantic voting consensus protocol to validate sémantiques facts.
"""

import logging  # noqa: E402
import time  # noqa: E402
from typing import Any, Dict, List, Optional, Tuple  # noqa: E402

import numpy as np  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

logger = logging.getLogger("animetix.swarm.consensus")


class SwarmConsensusVotes(BaseModel):
    votes: Dict[str, float] = Field(
        ...,
        description="Dictionnaire associant chaque nom d'agent à son score de confiance (entre 0.0 et 1.0).",
    )


class SwarmConsensusOrchestrator:
    # Panel d'experts de l'essaim : chacun juge un fait sous un angle propre.
    # `keywords` déclenche un vote favorable (hit), sinon on retombe sur `miss`.
    # L'« Avocat du Diable » est volontairement sceptique (base basse) pour forcer
    # le débat. Ce profil ne sert qu'au repli hors-LLM ; avec LLM, les votes sont
    # demandés au modèle par nom d'expert.
    AGENT_PROFILES: Dict[str, Dict[str, Any]] = {
        "Expert Visuel": {
            "keywords": [
                "couleur",
                "visuel",
                "animation",
                "paysage",
                "dessin",
                "graphisme",
                "studio",
                "réalisation",
            ],
            "hit": 0.85,
            "miss": 0.5,
        },
        "Expert Sonore": {
            "keywords": [
                "ost",
                "musique",
                "thème",
                "voix",
                "seiyuu",
                "doublage",
                "opening",
                "ending",
                "son",
            ],
            "hit": 0.9,
            "miss": 0.45,
        },
        "Expert Lore": {
            "keywords": [
                "scénario",
                "lore",
                "arc",
                "canon",
                "histoire",
                "personnage",
                "intrigue",
                "mythe",
            ],
            "hit": 0.88,
            "miss": 0.52,
        },
        "Expert Combat": {
            "keywords": [
                "combat",
                "pouvoir",
                "force",
                "fort",
                "technique",
                "puissance",
                "bataille",
                "duel",
            ],
            "hit": 0.86,
            "miss": 0.5,
        },
        "Expert Émotion": {
            "keywords": [
                "émotion",
                "drame",
                "romance",
                "tragédie",
                "amour",
                "relation",
                "larmes",
            ],
            "hit": 0.84,
            "miss": 0.48,
        },
        "Historien Otaku": {
            "keywords": [
                "époque",
                "historique",
                "auteur",
                "production",
                "année",
                "adaptation",
                "manga",
                "origine",
            ],
            "hit": 0.82,
            "miss": 0.5,
        },
        "Avocat du Diable": {"keywords": [], "hit": 0.4, "miss": 0.35},
    }

    def __init__(
        self,
        agent_names: Optional[List[str]] = None,
        inference_engine: Optional[Any] = None,
    ):
        self.agents = agent_names or list(self.AGENT_PROFILES.keys())
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
            f'Fait : "{fact}"\n\n'
            f"Évalue le niveau de confiance de chacun des experts suivants sous la forme d'un score entre 0.0 et 1.0 :\n"
            f"{agents_desc}\n\n"
            f"Retourne un objet JSON contenant les scores pour chaque agent dans le champ 'votes'."
        )
        if self.inference_engine is None:
            return {}
        try:
            result = self.inference_engine.generate_structured(
                prompt=prompt,
                response_model=SwarmConsensusVotes,
                system_prompt="Tu es un orchestrateur d'essaim d'agents d'IA de consensus sémantique.",
            )
            if isinstance(result, dict):
                return result.get("votes", {})
            elif result and hasattr(result, "votes"):
                return result.votes
            return {}
        except Exception as e:
            logger.warning(
                f"Failed to get swarm votes via LLM: {e}. Falling back to simulations."
            )
            return {}

    def get_paxos_diagnostics(
        self, fact: str, media_title: str, proposer: str = "ClientAPI"
    ) -> Dict[str, Any]:
        """
        Simule et retourne le détail technique du protocole Paxos-sémantique.
        """
        logger.info(f"🧬 Paxos-Semantic: Starting consensus for '{fact}'...")

        # Phase 1: Prepare/Promise (Simulation of agent availability)
        prepare_phase = {
            "proposal_id": f"px-{int(time.time())}",
            "proposer": proposer,
            "agents_contacted": self.agents,
            "promises_received": [
                a for a in self.agents if np.random.random() > 0.1
            ],  # 90% availability
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

        quorum_required = len(self.agents) // 2 + 1
        accept_phase = {
            "votes": votes,
            "threshold": 0.6,
            "quorum_required": quorum_required,
        }

        # Phase 3: Learn (Outcome)
        positive_votes = sum(1 for score in votes.values() if score >= 0.6)
        consensus_achieved = positive_votes >= quorum_required
        consensus_score = sum(votes.values()) / len(self.agents)

        outcome = {
            "consensus_achieved": consensus_achieved,
            "consensus_score": consensus_score,
            "paxos_state": "DECIDED" if consensus_achieved else "REJECTED",
            "message": (
                "Fact integrated to Knowledge Graph"
                if consensus_achieved
                else "Consensus not reached"
            ),
        }

        return {
            "fact": fact,
            "media": media_title,
            "phases": {
                "prepare": prepare_phase,
                "accept": accept_phase,
                "learn": outcome,
            },
            "is_recorded": consensus_achieved,
            "consensus_score": consensus_score,
            "votes": votes,
        }

    def propose_fact(
        self, proposer: str, fact: str, media_title: str
    ) -> Tuple[bool, float]:
        """
        Soumet un fait à l'essaim d'agents.
        Chaque agent vote en fonction d'un score heuristique/sémantique simulé ou évalué par un LLM.
        La majorité absolue est nécessaire pour valider le fait.
        """
        logger.info(
            f"🐝 Swarm: Proposing fact: '{fact}' for media '{media_title}' by agent '{proposer}'..."
        )

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
            "majority_achieved": majority_achieved,
        }

        if majority_achieved:
            self.consensus_log.append(verdict)
            logger.info(
                f"✅ Swarm Consensus Achieved! Fact recorded (Score: {consensus_score:.2f})."
            )
        else:
            logger.warning(
                f"❌ Swarm Consensus Failed! Fact rejected (Score: {consensus_score:.2f})."
            )

        return majority_achieved, consensus_score

    def _simulate_agent_vote(self, agent: str, fact: str, media: str) -> float:
        """
        Simule le vote sémantique d'un expert d'après son profil (repli hors-LLM).
        """
        profile = self.AGENT_PROFILES.get(agent)
        if not profile:
            return 0.55
        f_lower = fact.lower()
        keywords = profile.get("keywords", [])
        if keywords and any(w in f_lower for w in keywords):
            return float(profile["hit"])
        return float(profile["miss"])
