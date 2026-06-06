# -*- coding: utf-8 -*-
"""
Tests unitaires et d'intégration pour l'interconnexion sémantique
de la plasticité synaptique et de la cognition quantique au RAG d'Animetix.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock
from core.domain.services.advanced_rag_service import AdvancedRAGService
from core.domain.services.quantum_cognitive_service import QuantumCognitiveService
from core.domain.services.neuromorphic_plasticity_service import SynapticPlasticityService
from core.domain.services.rag_workflow_manager import RAGWorkflowManager

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
        plasticity_simulator=plasticity_simulator
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
    service = AdvancedRAGService(mock_repo, mock_llm, quantum_model=None, plasticity_simulator=None)
    candidates = [{"id": "1", "title": "Bleach", "genres": ["Shonen"], "score": 0.8}]

    adjusted = service._adjust_scores_cognitively(candidates, query="action")

    # Le score et la liste doivent rester intacts
    assert adjusted[0]["score"] == 0.8
    assert "cognitive_boost" not in adjusted[0]


def test_workflow_manager_triggers_cognitive_evolution(quantum_model, plasticity_simulator):
    """Vérifie que RAGWorkflowManager déclenche correctement la plasticité et l'effondrement quantique en fin de workflow."""
    # Mocks de tous les agents du workflow
    mock_planner = MagicMock()
    mock_critic = MagicMock()
    mock_synthesizer = MagicMock()
    mock_judge = MagicMock()
    mock_scout = MagicMock()
    mock_router = MagicMock()
    mock_evaluator = MagicMock()
    mock_partitioner = MagicMock()
    mock_graph_exp = MagicMock()
    mock_debate = MagicMock()
    mock_lib = MagicMock()
    mock_forge = MagicMock()
    mock_saga = MagicMock()
    mock_chron = MagicMock()
    mock_uncertainty = MagicMock()
    mock_engine = MagicMock()
    mock_search = MagicMock()
    mock_prompt_mgr = MagicMock()

    # Mock RAG Service avec nos vrais modèles cognitifs injectés
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    rag_service = AdvancedRAGService(
        mock_repo,
        mock_llm,
        quantum_model=quantum_model,
        plasticity_simulator=plasticity_simulator
    )

    manager = RAGWorkflowManager(
        planner=mock_planner,
        critic=mock_critic,
        synthesizer=mock_synthesizer,
        judge=mock_judge,
        scout=mock_scout,
        semantic_router=mock_router,
        retrieval_evaluator=mock_evaluator,
        community_partitioner=mock_partitioner,
        graph_expert=mock_graph_exp,
        debate_manager=mock_debate,
        librarian=mock_lib,
        forge=mock_forge,
        saga_agent=mock_saga,
        chronicler=mock_chron,
        uncertainty_service=mock_uncertainty,
        inference_engine=mock_engine,
        web_search=mock_search,
        prompt_manager=mock_prompt_mgr,
        rag_service=rag_service
    )

    # 1. Définir l'état initial des modèles
    old_weight_matrix = np.copy(plasticity_simulator.W)

    # 2. Exécuter la mise à jour cognitive pour une requête de "action"
    # On passe user_id="test_user" pour s'assurer que ça ne retourne pas early
    candidates = [{"id": "1", "title": "Naruto", "genres": ["Action", "Adventure", "Shonen"]}]
    manager._update_cognitive_state(query="action", answer="Naruto utilise le rasengan", candidates=candidates, user_id="test_user")

    # 3. Vérifications :
    # A. Modèle Quantique : L'état quantique doit avoir subi une mesure sur le thème "shonen",
    # provoquant un effondrement. L'état quantique doit être normalisé.
    assert np.linalg.norm(quantum_model.state) == pytest.approx(1.0)

    # B. Plasticité Synaptique : Les poids synaptiques doivent avoir changé.
    assert not np.array_equal(plasticity_simulator.W, old_weight_matrix)
