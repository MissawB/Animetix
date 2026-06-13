import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure correct backend imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

@pytest.fixture
def mock_wandb():
    with patch("pipeline.mlops.evaluation_metrics.wandb") as mock:
        yield mock

@pytest.fixture
def mock_safe_http_request():
    with patch("pipeline.mlops.evaluation_metrics.safe_http_request") as mock:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "This is a mock RAG answer containing Light Yagami, Ryuk and death note.",
            "usage": {
                "prompt_tokens": 1500,
                "completion_tokens": 120,
                "total_tokens": 1620
            }
        }
        mock.return_value = mock_response
        yield mock

@pytest.fixture
def mock_chroma():
    with patch("pipeline.chroma_client.chroma_manager") as mock:
        mock.query_collection.return_value = {
            "documents": [["Mock context document 1", "Mock context document 2"]],
            "ids": [["11061", "16498"]]
        }
        yield mock

@pytest.fixture
def mock_neo4j():
    with patch("pipeline.neo4j_client.neo4j_manager") as mock:
        mock.get_enriched_context.return_value = "Mock Neo4j Path Context"
        yield mock

@pytest.fixture
def mock_sentence_transformer():
    import numpy as np
    with patch("pipeline.mlops.evaluation_metrics.SentenceTransformer") as mock_class:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_class.return_value = mock_instance
        yield mock_class

@pytest.fixture
def mock_ragas_eval_service():
    with patch("core.domain.services.ragas_eval_service.RagasEvalService") as mock_class:
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.faithfulness = 0.95
        mock_result.answer_relevancy = 0.90
        mock_result.context_precision = 0.85
        mock_result.context_recall = 0.80
        mock_instance.judge_engine.generate_structured.return_value = mock_result
        mock_class.return_value = mock_instance
        yield mock_class

def test_ragas_performance_comparison_metrics_logging(
    mock_wandb,
    mock_safe_http_request,
    mock_chroma,
    mock_neo4j,
    mock_sentence_transformer,
    mock_ragas_eval_service,
    tmp_path
):
    # Setup a mock gold dataset with easy/hard, query_type and architectural properties
    mock_gold_data = [
        {
            "query": "Quel est l'animé où un jeune garçon cherche son père qui est un Hunter ?",
            "expected_id": "11061",
            "expected_title": "Hunter x Hunter (2011)",
            "is_architectural": False,
            "query_type": "graph",
            "ground_truth": "L'histoire suit Gon Freecss qui passe l'examen de Hunter pour retrouver son père Ging.",
            "difficulty": "easy"
        },
        {
            "query": "Cite 3 autres animés produits par le même studio",
            "expected_id": "16498",
            "expected_title": "Attack on Titan",
            "is_architectural": True,
            "query_type": "thematic",
            "ground_truth": "Le studio est Wit Studio.",
            "difficulty": "hard"
        }
    ]
    
    import json
    mock_gold_file = tmp_path / "gold_dataset.json"
    with open(mock_gold_file, "w", encoding="utf-8") as f:
        json.dump(mock_gold_data, f)
        
    with patch("pipeline.mlops.evaluation_metrics.GOLD_DATASET", str(mock_gold_file)):
        from pipeline.mlops.evaluation_metrics import ragas_performance_comparison
        
        # Execute the metrics comparison logic
        res = ragas_performance_comparison()
        
        assert res == {"status": "completed"}
        
        # Verify wandb was initialized and logged
        mock_wandb.init.assert_called_once()
        
        # Check that wandb.log was called
        assert mock_wandb.log.called
        
        # Verify wandb log calls included slicing keys, latency, and costs
        logged_keys = []
        for call in mock_wandb.log.call_args_list:
            if isinstance(call[0][0], dict):
                logged_keys.extend(call[0][0].keys())
        
        # Latency and cost logging verifications
        assert any("overall_avg_latency" in k for k in logged_keys)
        assert any("overall_avg_cost" in k for k in logged_keys)
        
        # Sliced metrics validation (query_type and difficulty)
        assert any("slice_query_type_graph" in k for k in logged_keys)
        assert any("slice_query_type_thematic" in k for k in logged_keys)
        assert any("slice_difficulty_easy" in k for k in logged_keys)
        assert any("slice_difficulty_hard" in k for k in logged_keys)
        
        # Verify Table logging
        assert mock_wandb.Table.called
