# -*- coding: utf-8 -*-
"""
Tests unitaires pour les modules d'IA Cognitive Next-Gen d'Animetix.
Couvre Tree-of-Thoughts (ToT), EpisodicMemoryCompressor, et NeuroSymbolicUserProfiler.
"""

import pytest
from unittest.mock import MagicMock, patch

# ==========================================
# 1. TESTS TREE-OF-THOUGHTS (MCTS)
# ==========================================
def test_tree_of_thoughts_search():
    from core.domain.services.tree_of_thoughts_service import TreeOfThoughtsSearchService
    
    mock_engine = MagicMock()
    # Simuler des retours LLM :
    # Les premiers retours sont les étapes de pensées, le dernier est le score de pertinence, et la synthèse finale
    mock_engine.generate.side_effect = [
        "Thought path A",  # step 1, branch 1
        "0.85",            # score for step 1, branch 1
        "Thought path B",  # step 1, branch 2
        "0.40",            # score for step 1, branch 2 (pruned!)
        "Thought path C",  # step 1, branch 3
        "0.90",            # score for step 1, branch 3 (selected!)
        "Final synthesis text" # synthesis response
    ]
    
    service = TreeOfThoughtsSearchService(inference_engine=mock_engine, prompt_manager=MagicMock())
    result = service.solve_with_tree_of_thoughts(query="Enigme Otaku", breadth=3, depth=1)
    
    assert result["query"] == "Enigme Otaku"
    assert "Final synthesis text" in result["final_answer"]
    assert len(result["best_thought_path"]) == 1
    assert result["best_thought_path"][0] == "Thought path C"


# ==========================================
# 2. TESTS COMPRESSEUR DE MEMOIRE EPISODIQUE
# ==========================================
def test_episodic_memory_compressor():
    from core.domain.services.episodic_memory_compressor import EpisodicMemoryCompressor
    
    mock_chroma = MagicMock()
    # Simuler deux souvenirs vectoriels dans Chroma
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "documents": [
            "L'utilisateur aime la dark fantasy et Berserk.",
            "L'utilisateur déteste les animes comiques niaises."
        ]
    }
    mock_chroma.get_collection.return_value = mock_collection
    
    mock_engine = MagicMock()
    mock_engine.generate.return_value = "Profil consolidé : adepte de Berserk et Seinen sombre."
    
    mock_neo4j = MagicMock()
    
    compressor = EpisodicMemoryCompressor(
        chroma_resource=mock_chroma,
        inference_engine=mock_engine,
        neo4j_manager=mock_neo4j
    )
    
    profile = compressor.compress_user_memories("user_123")
    
    assert "adepte de Berserk" in profile
    mock_chroma.get_collection.assert_called_once_with("user_long_term_memories")
    # Vérification que le graphe de relations Neo4j a bien été mis à jour
    assert mock_neo4j.execute_query.call_count >= 1

# ==========================================
# 3. TESTS PROFILER NEURO-SYMBOLIQUE (SAT SOLVER)
# ==========================================
def test_neuro_symbolic_user_profiler():
    from core.domain.services.neuro_symbolic_user_profiler import NeuroSymbolicUserProfiler
    
    feedbacks = [
        {"input_context": "Recommande un seinen sombre et sanglant.", "is_positive": True},
        {"input_context": "Anime shonen plein de violence niaise.", "is_positive": False}
    ]
    
    profiler = NeuroSymbolicUserProfiler()
    rules = profiler.deduce_preference_rules(feedbacks)
    
    assert len(rules) >= 1
    # Doit contenir soit des assertions logiques symboliques, soit des déductions par repli Python
    # ex: "Avoid == Violence" ou "Prefer == Seinen"
    assert any("seinen" in r.lower() or "prefer" in r.lower() for r in rules)
