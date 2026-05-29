# -*- coding: utf-8 -*-
"""
Tests unitaires pour la Feuille de Route d'Améliorations de l'IA d'Animetix.
Valide ColBERT, GraphRAG, le Décodage Spéculatif, le Budget TTC, le Sensor DPO,
et les deux modes de Calcul Spatial Statique (SGS) vs Dynamique (DCS).
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# ==========================================
# 1. TESTS ADAPTATEUR COLBERT
# ==========================================
def test_colbert_maxsim():
    from backend.adapters.persistence.colbert_adapter import LateInteractionColBERTAdapter
    adapter = LateInteractionColBERTAdapter(dimension=4)
    
    # 2 tokens pour la requête, dimension=4
    q_embeddings = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ])
    
    # 2 tokens pour le document, dimension=4
    doc_embeddings = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ])
    
    score = adapter.calculate_maxsim(q_embeddings, doc_embeddings)
    # Similarité maximale pour token 1 = 1.0, pour token 2 = 1.0. Somme = 2.0.
    assert score == 2.0

def test_colbert_ranking():
    from backend.adapters.persistence.colbert_adapter import LateInteractionColBERTAdapter
    adapter = LateInteractionColBERTAdapter(dimension=8)
    
    docs = [
        {"title": "Death Note", "description": "Un cahier de mort magique de shinigami."},
        {"title": "K-On!", "description": "Un club de musique scolaire mignon avec du thé."}
    ]
    
    ranked = adapter.rank_documents("cahier magique shinigami", docs, text_field="description")
    
    assert len(ranked) == 2
    assert ranked[0]["title"] == "Death Note"  # Plus de mots en commun
    assert ranked[0]["colbert_score"] > ranked[1]["colbert_score"]

# ==========================================
# 2. TESTS GRAPHRAG HIÉRARCHIQUE
# ==========================================
@patch('src.core.domain.services.hierarchical_graph_rag.GraphCommunityPartitioner')
def test_hierarchical_graph_rag(mock_partitioner):
    from backend.core.domain.services.hierarchical_graph_rag import HierarchicalGraphRAGService
    
    mock_partitioner_instance = MagicMock()
    mock_partitioner_instance.search_communities.return_value = [
        {
            "name": "Communauté Dark Fantasy",
            "summary": "Berserk et les drames sombres.",
            "entities": ["Berserk", "Guts"]
        }
    ]
    mock_partitioner.return_value = mock_partitioner_instance
    
    service = HierarchicalGraphRAGService(neo4j_manager=MagicMock(), llm_service=MagicMock())
    context = service.enrich_prompt_with_graphrag("Berserk", "Contexte de base.")
    
    assert "GraphRAG" in context
    assert "Communauté Dark Fantasy" in context
    assert "Berserk" in context

# ==========================================
# 3. TESTS INFERENCE SPECULATIVE
# ==========================================
def test_speculative_decoding():
    from backend.adapters.inference.speculative_inference import SpeculativeDecodingInferenceAdapter
    
    mock_verifier = MagicMock()
    mock_verifier.generate.return_value = "L'entraînement est complété."
    mock_verifier.health_check.return_value = {"model": "Llama-3-8B"}
    
    adapter = SpeculativeDecodingInferenceAdapter(verifier_engine=mock_verifier)
    res = adapter.generate("Test prompt")
    
    assert res == "L'entraînement est complété."
    mock_verifier.generate.assert_called_once_with(
        prompt="Test prompt",
        system_prompt="Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget=0,
        thinking_mode=False
    )
    
    health = adapter.health_check()
    assert health["mode"] == "speculative_decoding"
    assert health["speculative_acceleration"] == "2.4x"

# ==========================================
# 4. TESTS ANALYSEUR DE COMPLEXITÉ & TTC
# ==========================================
def test_complexity_analyser():
    from backend.core.domain.services.complexity_analyser import ComplexityAnalyser
    analyser = ComplexityAnalyser()
    
    # Test simple keyword parsing
    budget, score = analyser.assess_complexity("Qui est Luffy ?")
    assert score == 0
    assert budget == 0
    
    # Test high complexity keyword parsing
    budget_high, score_high = analyser.assess_complexity("Explique le paradoxe temporel scénaristique de Steins;Gate.")
    assert score_high == 2
    assert budget_high == 1024

# ==========================================
# 5. TESTS SENSOR DPO SANS DJANGO CRASH
# ==========================================
@patch('django.apps.apps.ready', True)
@patch('django.setup')
def test_dpo_sensor_mocked(mock_setup):
    from backend.pipeline.mlops.auto_dpo_trigger import check_dpo_feedback_sensor
    from dagster import build_sensor_context
    
    context = build_sensor_context(cursor="10")
    
    # Simuler 120 feedbacks non traités (quota dépassé de +110 par rapport au curseur de 10)
    with patch('animetix.models.AIFeedback') as mock_feedback_model:
        mock_feedback_model.objects.count.return_value = 120
        
        runs = list(check_dpo_feedback_sensor(context))
        
        assert len(runs) == 1
        assert runs[0].run_key == "auto_dpo_training_120"
        assert context.cursor == "120"



# ==========================================
# 6. TESTS MODE SPATIAL STATIQUE VS DYNAMIQUE
# ==========================================
@patch('imageio.get_reader')
@patch('subprocess.run')
def test_spatial_computing_modes(mock_sub, mock_imageio):
    from backend.core.domain.services.static_diorama_3d_service import StaticDiorama3DService
    from backend.core.domain.services.cinematic_volumetric_reconstruction_service import CinematicVolumetricReconstructionService
    
    # Mock imageio reader
    mock_reader = MagicMock()
    mock_reader.get_meta_data.return_value = {'duration': 4.0, 'fps': 24.0}
    # Mock iteration to yield at least one frame
    mock_reader.__iter__.return_value = [np.zeros((100, 100, 3), dtype=np.uint8)]
    mock_imageio.return_value = mock_reader
    
    mock_engine = MagicMock()
    mock_engine.estimate_depth.return_value = b"depth_map_bytes"
    mock_engine.generate_3d_scene.return_value = {"status": "success", "model_url": "/models/static.splat", "in_painted": True}
    mock_engine.get_video_temporal_embeddings.return_value = [{"segment": 0}, {"segment": 1}]
    
    # 1. SGS Statique
    static_service = StaticDiorama3DService(inference_engine=mock_engine)
    static_res = static_service.reconstruct_static_diorama(b"image_bytes", "Ghibli Art")
    
    assert static_res["status"] == "success"
    assert static_res["viewer_type"] == "static_gaussian_diorama"
    assert static_res["metadata"]["mode"] == "SGS_Static_Diorama_3D"
    
    # 2. DCS Dynamique Cinématique
    dynamic_service = CinematicVolumetricReconstructionService(inference_engine=mock_engine)
    dynamic_res = dynamic_service.reconstruct_dynamic_cinematic_scene(b"video_bytes", "Demon Slayer Fight")
    
    assert dynamic_res["status"] == "success"
    assert dynamic_res["viewer_type"] == "dynamic_cinematic_splatting"
    assert dynamic_res["metadata"]["mode"] == "DCS_Dynamic_Cinematic_Splatting_3D"
    assert dynamic_res["metadata"]["timeline_duration_sec"] == 4
