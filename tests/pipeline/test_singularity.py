# -*- coding: utf-8 -*-
"""
Tests unitaires pour les modules d'IA de Cinquième Génération (Singularité SOTA 2035+) d'Animetix.
Couvre SelfEvolvingCompiler, SynapticPlasticitySimulator, et AutonomousDomainSynthesizer.
"""

from unittest.mock import MagicMock  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402


# ==========================================
# 1. TESTS AUTO-COMPILATION (SELF-EVOLVING COMPILER)
# ==========================================
def test_self_evolving_compiler():
    from core.domain.services.self_evolving_compiler import (  # noqa: E402
        SelfEvolvingCompiler,
    )

    compiler = SelfEvolvingCompiler(build_dir="data/mlops/build_test")

    # 1. Optimisation d'un goulot d'étranglement fictif
    optimized_fn = compiler.analyze_and_optimize("cosine_similarity")

    assert callable(optimized_fn)

    # 2. Test du fallback NumPy de calcul vectorisé
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([1.0, 2.0, 3.0])
    similarity = optimized_fn(a, b)

    assert pytest.approx(similarity) == 1.0

    # Orthogonal
    c = np.array([1.0, 0.0])
    d = np.array([0.0, 1.0])
    ortho_sim = optimized_fn(c, d)
    assert pytest.approx(ortho_sim) == 0.0


def test_self_evolving_compiler_llm_evolution():
    from core.domain.services.self_evolving_compiler import (  # noqa: E402
        SelfEvolvingCompiler,
    )

    compiler = SelfEvolvingCompiler(build_dir="data/mlops/build_test")

    # Mock du LLM proxy
    mock_llm = MagicMock()
    mock_code = """
```python
def matrix_row_norm(x):
    res = np.zeros(x.shape[0])
    for i in range(x.shape[0]):
        row_sum = 0.0
        for j in range(x.shape[1]):
            row_sum += x[i, j] ** 2
        res[i] = np.sqrt(row_sum)
    return res
```
"""
    mock_llm.generate.return_value = mock_code

    # Évolution du runtime
    fn = compiler.evolve_with_llm("Calculate norm of each row in a matrix", mock_llm)

    assert callable(fn)
    assert fn.__name__ == "matrix_row_norm"

    # Test d'exécution
    mat = np.array([[3.0, 4.0], [1.0, 0.0]])
    norms = fn(mat)

    assert np.allclose(norms, [5.0, 1.0])


# ==========================================
# 2. TESTS PLASTICITÉ SYNAPTIQUE (HEBBIAN & STDP)
# ==========================================
def test_synaptic_plasticity_hebbian_and_stdp():
    from core.domain.services.synaptic_plasticity import (  # noqa: E402
        SynapticPlasticitySimulator,
    )

    simulator = SynapticPlasticitySimulator(
        num_concepts=5, tau_plus=10.0, tau_minus=10.0
    )

    # 1. Règle Hebbian : co-activation de concepts
    activations = [1.0, 1.0, 0.0, 0.0, 0.0]
    old_weight_0_1 = simulator.W[0, 1]

    simulator.update_hebbian(activations, learning_rate=0.1)

    # Les poids de co-activation doivent augmenter
    assert simulator.W[0, 1] > old_weight_0_1
    assert simulator.W[0, 0] == 0.0  # Diagonale doit rester nulle

    # 2. Règle STDP : Spike-Timing-Dependent Plasticity
    # Concept 0 s'active (spike) à t=10.0
    # Concept 1 s'active (spike) à t=15.0
    # post_time > pre_time => potentiation (LTP)
    simulator.trigger_spikes([0], current_time=10.0)
    simulator.trigger_spikes([1], current_time=15.0)

    old_w_ltp = simulator.W[0, 1]
    dw_ltp = simulator.update_stdp(pre_idx=0, post_idx=1, learning_rate=0.1)

    assert dw_ltp > 0.0
    assert simulator.W[0, 1] > old_w_ltp

    # LTD (Dépression) : post_time < pre_time
    # Concept 2 s'active à t=30.0
    # Concept 3 s'active à t=25.0
    simulator.trigger_spikes([2], current_time=30.0)
    simulator.trigger_spikes([3], current_time=25.0)

    old_w_ltd = simulator.W[2, 3]
    dw_ltd = simulator.update_stdp(pre_idx=2, post_idx=3, learning_rate=0.1)

    assert dw_ltd < 0.0
    assert simulator.W[2, 3] < old_w_ltd


# ==========================================
# 3. TESTS SYNTHÉTISEUR DE MULTIVERS AUTONOME (ADMS)
# ==========================================
def test_autonomous_domain_synthesizer():
    from core.domain.services.domain_synthesizer import (  # noqa: E402
        AutonomousDomainSynthesizer,
    )

    # Mocks du moteur d'inférence LLM
    mock_inference = MagicMock()
    mock_inference.generate.return_value = "Shinji active le réacteur antigravité."

    # Mock Neo4j
    mock_neo4j = MagicMock()
    mock_neo4j.execute_query.return_value = []

    # Mock Gold Dataset Port
    mock_gold_port = MagicMock()

    synthesizer = AutonomousDomainSynthesizer(
        inference_engine=mock_inference,
        neo4j_manager=mock_neo4j,
        gold_dataset_port=mock_gold_port,
    )

    # 1. Génération sémantique de l'univers
    universe = synthesizer.synthesize_multiverse(
        universe_name="NeonGenesisX", primary_genre="Sci-Fi"
    )

    assert universe["name"] == "NeonGenesisX"
    assert universe["genre"] == "Sci-Fi"
    assert len(universe["characters"]) > 0
    assert len(universe["episodes"]) > 0

    # L'enrichissement par LLM a fonctionné
    assert (
        universe["episodes"][0]["summary"] == "Shinji active le réacteur antigravité."
    )

    # 2. Test d'évaluation de cohérence (Cas digne d'intérêt : Sci-Fi populaire)
    evaluation = synthesizer.evaluate_coherence_and_interest(universe)
    assert evaluation["is_worthy"] is True
    assert evaluation["ai_score"] >= 0.7
    assert evaluation["community_score"] >= 0.7

    # 3. Persistance d'un univers digne d'intérêt (staged pour human validation)
    success = synthesizer.persist_universe_to_graph(universe)
    assert success is True
    mock_gold_port.save_synthetic_entry.assert_called_once()

    # 4. Test d'évaluation de cohérence (Cas indigne : genre impopulaire et manque de données)
    poor_universe = {
        "name": "BoringWorld",
        "genre": "Documentary",
        "description": "Short",
        "cosmology": "None",
        "characters": [],
        "episodes": [],
    }

    # Sans moteur d'inférence et sans structure, l'heuristique doit rejeter l'univers
    synthesizer_no_llm = AutonomousDomainSynthesizer(
        inference_engine=None, neo4j_manager=None
    )
    poor_eval = synthesizer_no_llm.evaluate_coherence_and_interest(poor_universe)
    assert poor_eval["is_worthy"] is False

    # Persistance de cet univers indigne doit échouer
    poor_persistence_success = synthesizer_no_llm.persist_universe_to_graph(
        poor_universe
    )
    assert poor_persistence_success is False
