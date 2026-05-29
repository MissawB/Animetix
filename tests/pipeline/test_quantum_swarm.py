# -*- coding: utf-8 -*-
"""
Tests unitaires pour les modules d'IA de Quatrième Génération (SOTA 2030+) d'Animetix.
Couvre QuantumCognitivePreferenceModel, SwarmConsensusOrchestrator, et CounterfactualConversationSimulator.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# ==========================================
# 1. TESTS COGNITION QUANTIQUE (BORN'S RULE & NON-COMMUTATIVITÉ)
# ==========================================
def test_quantum_cognitive_model():
    from backend.core.domain.services.quantum_cognitive_model import QuantumCognitivePreferenceModel
    np.random.seed(42)
    model = QuantumCognitivePreferenceModel(dimension=4)
    
    # 1. Norme de l'état d'esprit doit être 1.0
    norm = np.linalg.norm(model.state)
    assert pytest.approx(norm) == 1.0
    
    # 2. Mesure de préférence via règle de Born
    prob_shonen, outcome_shonen = model.measure_preference("shonen")
    assert 0.0 <= prob_shonen <= 1.0
    
    # L'état doit s'effondrer et rester normalisé
    new_norm = np.linalg.norm(model.state)
    assert pytest.approx(new_norm) == 1.0

def test_quantum_order_effects():
    from backend.core.domain.services.quantum_cognitive_model import QuantumCognitivePreferenceModel
    
    np.random.seed(42)
    model = QuantumCognitivePreferenceModel(dimension=4)
    
    # Démonstration sémantique de non-commutativité (effet d'ordre)
    # Mesurer Ghibli puis Seinen donne une probabilité différente de Seinen puis Ghibli
    p_ba, p_ab = model.order_effects_demonstration("ghibli", "seinen")
    
    # La non-commutativité implique que l'état d'arrivée et les probabilités dépendent de l'ordre de mesure
    assert not np.isclose(p_ba, p_ab), f"Order effects not demonstrated: p_ba={p_ba}, p_ab={p_ab}"

# ==========================================
# 2. TESTS SWARM CONSENSUS ORCHESTRATOR (PAXOS)
# ==========================================
def test_swarm_consensus_paxos():
    from backend.core.domain.services.swarm_consensus import SwarmConsensusOrchestrator
    
    orchestrator = SwarmConsensusOrchestrator()
    
    fact_visuel = "L'animation de Demon Slayer par Ufotable présente des graphismes et des couleurs époustouflantes, soutenue par un scénario et un lore d'exception."
    success, score = orchestrator.propose_fact(
        proposer="VisualExpert",
        fact=fact_visuel,
        media_title="Demon Slayer"
    )

    
    assert success is True
    assert score >= 0.6
    
    fact_inconnu = "Ce manga s'est bien vendu en boutique en 2012."

    success_fail, score_fail = orchestrator.propose_fact(
        proposer="AcousticExpert",
        fact=fact_inconnu,
        media_title="Unknown Media"
    )
    
    assert success_fail is False

# ==========================================
# 3. TESTS SIMULATEUR CONTREFACTUEL
# ==========================================
def test_counterfactual_conversation_simulator():
    from backend.core.domain.services.counterfactual_simulator import CounterfactualConversationSimulator
    
    mock_engine = MagicMock()
    mock_engine.generate.side_effect = [
        "Réponse alternative : Steins;Gate intègre une ligne temporelle complexe.", # response
        "0.92" # judge utility score
    ]
    
    simulator = CounterfactualConversationSimulator(inference_engine=mock_engine)
    
    actual_dialogue = [
        {"role": "user", "content": "Recommande un anime de voyage temporel."},
        {"role": "assistant", "content": "Je te conseille Erased."}
    ]
    
    result = simulator.simulate_counterfactual_path(
        actual_dialogue=actual_dialogue,
        what_if_query="Et si on demandait Steins;Gate ?"
    )
    
    assert result["what_if_query"] == "Et si on demandait Steins;Gate ?"
    assert "Steins;Gate" in result["alternative_response"]
    assert result["alternative_utility"] == 0.92
    assert result["counterfactual_regret"] == pytest.approx(0.07) # 0.92 - 0.85 = 0.07
