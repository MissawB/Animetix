# -*- coding: utf-8 -*-
"""
Tests unitaires pour les modules d'IA Ultra-SOTA (Horizons 2028-2030) d'Animetix.
Couvre DSPyPromptOptimizer, CFRGameSolver, et LiquidNeuralNetworkSimulator.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# ==========================================
# 1. TESTS DSPY PROMPT OPTIMIZER
# ==========================================
def test_dspy_prompt_optimizer():
    from backend.core.domain.services.dspy_prompt_optimizer import DSPyPromptOptimizer
    
    mock_engine = MagicMock()
    # Simuler des retours LLM :
    # Les premiers sont les mutations générées, les suivants sont les évaluations du juge
    mock_engine.generate.side_effect = [
        "Mutated template A",  # mutation 1
        "Mutated template B",  # mutation 2
        "Generated response A1", # eval 1 for template 1
        "0.95",                 # judge score for A1
        "Generated response A2", # eval 2 for template 1
        "0.85",                 # judge score for A2
        "Generated response B1", # eval 1 for template 2
        "0.70",                 # judge score for B1
        "Generated response B2", # eval 2 for template 2
        "0.60"                  # judge score for B2
    ]
    
    optimizer = DSPyPromptOptimizer(inference_engine=mock_engine)
    
    dataset = [
        {"query": "Luffy", "expected": "One Piece"},
        {"query": "Guts", "expected": "Berserk"}
    ]
    
    best, score = optimizer.evaluate_and_select_best("Original template: {query}", dataset)
    
    assert "template" in best
    assert score == pytest.approx(0.90)

    assert best == "Original template: {query}"


# ==========================================
# 2. TESTS CFR GAME SOLVER
# ==========================================
def test_cfr_game_solver():
    from backend.core.domain.services.cfr_game_solver import CFRGameSolver
    
    solver = CFRGameSolver(num_actions=3)
    
    # 1. Vérification que la stratégie initiale est équitable
    strategy = solver.get_strategy()
    assert len(strategy) == 3
    assert np.allclose(strategy, [1/3, 1/3, 1/3])
    
    # 2. Simulation de pas d'entraînement CFR
    utilities = np.array([0.9, 0.1, 0.4])
    for _ in range(50):
        solver.train_step(opponent_action=0, utilities=utilities)
        
    avg_strategy = solver.get_average_strategy()
    # L'action 0 (utilité 0.9) doit dominer largement les autres
    assert avg_strategy[0] > avg_strategy[1]
    assert np.isclose(np.sum(avg_strategy), 1.0)
    
    # 3. Résolution de question Akinetix CFR
    questions = ["Est-ce un Shonen ?", "Est-ce un Seinen ?", "Est-ce un Ghibli ?"]
    best_q, confidence = solver.solve_best_question(questions, {})
    
    assert best_q in questions
    assert confidence > 0.0

# ==========================================
# 3. TESTS LIQUID NEURAL NETWORK (LNN)
# ==========================================
def test_liquid_neural_network_simulator():
    from backend.core.domain.services.liquid_neural_network import LiquidNeuralNetworkSimulator
    
    simulator = LiquidNeuralNetworkSimulator(state_dimension=4, input_dimension=2)
    
    # 1. Vérification des dimensions initiales
    assert simulator.W.shape == (4, 4)
    assert simulator.tau.shape == (4,)
    
    # 2. Simulation d'un pas temporel via Runge-Kutta 4
    x_init = np.array([0.1, -0.2, 0.3, 0.0])
    u_input = np.array([1.0, -0.5])
    
    x_next = simulator.integrate_rk4(x_init, u_input, dt=0.05)
    
    assert x_next.shape == (4,)
    # Les états doivent être bornés sémantiquement par tanh et relaxation
    assert np.all(x_next <= 1.0) and np.all(x_next >= -1.0)
    
    # 3. Traitement de signal continu
    continuous_signal = [
        [0.5, 0.2],
        [0.6, 0.1],
        [0.4, 0.3]
    ]
    states = simulator.process_continuous_signal(continuous_signal, dt=0.05)
    
    assert len(states) == 3
    assert len(states[0]) == 4
