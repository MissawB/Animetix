# -*- coding: utf-8 -*-
"""
Tests unitaires pour les modules d'IA de Cinquième Génération (Singularité SOTA 2035+) d'Animetix.
Couvre SelfEvolvingCompiler et AutonomousDomainSynthesizer.
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
# 2. TESTS SYNTHÉTISEUR DE MULTIVERS AUTONOME (ADMS)
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
