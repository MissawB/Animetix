# -*- coding: utf-8 -*-
"""
Tests unitaires et d'intégration pour l'interconnexion sémantique
de la plasticité synaptique et de la cognition quantique au RAG d'Animetix.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock
from core.domain.services.advanced_rag_service import AdvancedRAGService
from core.domain.services.quantum_cognitive_model import QuantumCognitivePreferenceModel
from core.domain.services.synaptic_plasticity import SynapticPlasticitySimulator
from core.domain.services.rag_workflow_manager import RAGWorkflowManager

@pytest.fixture
def quantum_model():
    return QuantumCognitivePreferenceModel(dimension=4)

@pytest.fixture
def plasticity_simulator():
    return SynapticPlasticitySimulator(num_concepts=10)

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
    
    # Configurer l'état quantique pour favoriser Comedy (100% comedy)
    quantum_model.state = np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
    
    # Simuler des candidats avec différents genres/thèmes
    candidates = [
        {"id": "1", "title": "Kimi ni Todoke", "genres": ["Romance", "Comedy"], "score": 0.5},
        {"id": "2", "title": "Attack on Titan", "genres": ["Action", "Shonen"], "score": 0.5}
    ]
    
    # Renforcer les poids Hebb de Romance (concept 1) et Comedy (concept 3) dans le simulateur
    activations = [0.0] * 10
    activations[1] = 1.0 # Romance
    activations[3] = 1.0 # Comedy
    plasticity_simulator.update_hebbian(activations, learning_rate=0.5)
    
    # Faire une recherche pour "comedy"
    adjusted = service._adjust_scores_cognitively(candidates, query="comedy romance")
    
    assert len(adjusted) == 2
    # Le premier candidat possède "Comedy" et "Romance", il doit avoir un score ajusté plus élevé
    assert adjusted[0]["id"] == "1"
    assert adjusted[0]["score"] > 0.5
    assert adjusted[0]["cognitive_boost"] > 0.0
    
    # Le second candidat a un boost différent
    assert "cognitive_boost" in adjusted[1]

def test_graceful_degradation_without_cognitive_models():
    """Vérifie que le RAG fonctionne normalement si les modèles cognitifs sont absents."""
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    
    service = AdvancedRAGService(mock_repo, mock_llm, quantum_model=None, plasticity_simulator=None)
    candidates = [{"id": "1", "title": "Bleach", "genres": ["Shonen"], "score": 0.8}]
    
    adjusted = service._adjust_scores_cognitively(candidates, query="action")
    
    # Le score et la liste doivent rester intacts
    assert adjusted == candidates

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
    old_state_norm = np.linalg.norm(quantum_model.state)
    old_weight_matrix = np.copy(plasticity_simulator.W)
    
    # 2. Exécuter la mise à jour cognitive pour une requête de "shonen"
    candidates = [{"id": "1", "title": "Naruto", "genres": ["Action", "Adventure", "Shonen"]}]
    manager._update_cognitive_state(query="action", answer="Naruto utilise le rasengan", candidates=candidates)
    
    # 3. Vérifications :
    # A. Modèle Quantique : L'état quantique doit avoir subi une mesure sur le thème "shonen",
    # provoquant un effondrement. L'état quantique doit être normalisé.
    assert np.linalg.norm(quantum_model.state) == pytest.approx(1.0)
    
    # B. Plasticité Synaptique : Les poids synaptiques co-activés de Action (0) et Shonen (non mappé mais Action = 0)
    # doivent avoir changé sous la règle de Hebb.
    assert not np.array_equal(plasticity_simulator.W, old_weight_matrix)
    # L'activation Hebbian a augmenté le poids d'auto-co-activation moyen
    assert np.mean(plasticity_simulator.W) != np.mean(old_weight_matrix)
