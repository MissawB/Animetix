# -*- coding: utf-8 -*-
"""
Tests unitaires et d'intégration pour l'interconnexion sémantique
de la plasticité synaptique et de la cognition quantique au RAG d'Animetix.
"""

from unittest.mock import MagicMock  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from core.domain.services.advanced_rag_service import AdvancedRAGService  # noqa: E402
from core.domain.services.neuromorphic_plasticity_service import (  # noqa: E402
    SynapticPlasticityService,
)
from core.domain.services.quantum_cognitive_service import (  # noqa: E402
    QuantumCognitiveService,
)


@pytest.fixture
def quantum_model():
    return QuantumCognitiveService(dimension=4)


@pytest.fixture
def plasticity_simulator():
    return SynapticPlasticityService(num_concepts=10)


def test_cognitive_biasing_score_adjustment(quantum_model, plasticity_simulator):
    """Vérifie que _adjust_scores_cognitively applique correctement les boosts Hebb et Born."""
    mock_repo = MagicMock()
    mock_llm = MagicMock()

    # 1. Instancier le RAG avec les modèles cognitifs
    service = AdvancedRAGService(
        mock_repo,
        mock_llm,
        quantum_model=quantum_model,
        plasticity_simulator=plasticity_simulator,
    )

    # 2. Préparer des candidats (un Shonen, un Seinen)
    candidates = [
        {"id": "1", "title": "Naruto", "genres": ["Shonen"], "score": 0.5},
        {"id": "2", "title": "Monster", "genres": ["Seinen"], "score": 0.5},
    ]

    # 3. Simuler une préférence marquée pour le Shonen dans les modèles
    # On force le vecteur d'état quantique sur |Shonen>
    quantum_model.state = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)

    # On booste le poids synaptique du concept "Action" (0) dans la plasticité
    # (Supposons que query="action" stimule concept 0)
    plasticity_simulator.W[0, 0] = 0.8

    # 4. Exécuter l'ajustement pour une requête "action"
    adjusted = service._adjust_scores_cognitively(candidates, query="action")

    # 5. Vérifications
    naruto = next(c for c in adjusted if c["id"] == "1")
    monster = next(c for c in adjusted if c["id"] == "2")

    # Naruto (Shonen) doit avoir un score plus élevé que Monster (Seinen)
    # car l'état quantique est collapsé sur Shonen et le concept Action est boosté.
    assert naruto["score"] > monster["score"]
    assert naruto["cognitive_boost"] > 0
    assert "cognitive_boost" in naruto


def test_graceful_degradation_without_cognitive_models():
    """Vérifie que le RAG fonctionne normalement si les modèles cognitifs sont explicitement absents."""
    mock_repo = MagicMock()
    mock_llm = MagicMock()

    # On passe explicitement None pour désactiver
    service = AdvancedRAGService(
        mock_repo, mock_llm, quantum_model=None, plasticity_simulator=None
    )
    candidates = [{"id": "1", "title": "Bleach", "genres": ["Shonen"], "score": 0.8}]

    adjusted = service._adjust_scores_cognitively(candidates, query="action")

    # Le score et la liste doivent rester intacts
    assert adjusted[0]["score"] == 0.8
    assert "cognitive_boost" not in adjusted[0]


def test_workflow_manager_triggers_cognitive_evolution(
    quantum_model, plasticity_simulator
):
    """Vérifie que la plasticité et l'effondrement quantique sont déclenchés en fin de workflow."""
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    rag_service = AdvancedRAGService(
        mock_repo,
        mock_llm,
        quantum_model=quantum_model,
        plasticity_simulator=plasticity_simulator,
    )

    # 1. Définir l'état initial des modèles
    old_weight_matrix = np.copy(plasticity_simulator.W)

    # 2. Exécuter la mise à jour cognitive pour une requête de "action"
    # On passe user_id="test_user" pour s'assurer que ça ne retourne pas early
    candidates = {"genres": ["Action", "Adventure", "Shonen"]}
    rag_service.update_cognitive_state(
        user_id="test_user", query="action", clicked_item_metadata=candidates
    )

    # 3. Vérifications :
    # A. Modèle Quantique : L'état quantique doit avoir subi une mesure sur le thème "shonen",
    # provoquant un effondrement. L'état quantique doit être normalisé.
    assert np.linalg.norm(quantum_model.state) == pytest.approx(1.0)

    # B. Plasticité Synaptique : Les poids synaptiques doivent avoir changé.
    assert not np.array_equal(plasticity_simulator.W, old_weight_matrix)
