import pytest
from unittest.mock import MagicMock, patch
from src.adapters.inference.vision_transformers_adapter import VisionTransformersAdapter

def test_visual_rerank_success():
    # Mocking requests.get
    class MockResponse:
        status_code = 200
        content = b"fake_image_data"

    with patch("requests.get", return_value=MockResponse()), \
         patch("sentence_transformers.SentenceTransformer") as mock_model, \
         patch("sentence_transformers.util.cos_sim") as mock_cos_sim, \
         patch("PIL.Image.open") as mock_image_open:
        
        # Setup mocks
        mock_model.return_value.encode.return_value = [1, 0]
        mock_cos_sim.return_value = [[0.9, 0.5]]
        mock_image_open.return_value = MagicMock()
        
        adapter = VisionTransformersAdapter()
        results = adapter.visual_rerank(
            query="test query",
            image_urls=["url1", "url2"]
        )        
        assert len(results) >= 1
        assert "url" in results[0]
        assert results[0]["score"] == 0.9

def test_visual_rerank_failure():
    # Mocking requests.get to return a failure status code
    class MockResponse:
        status_code = 404
        content = b""
    
    with patch("requests.get", return_value=MockResponse()):
        adapter = VisionTransformersAdapter()
        results = adapter.visual_rerank(
            query="test query", 
            image_urls=["invalid_url"]
        )
        assert results == []

