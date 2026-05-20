import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.adapters.inference.transformers_adapter import TransformersAdapter

@pytest.mark.asyncio
async def test_visual_rerank_success():
    # Mocking necessary components
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read.return_value = b"fake_image_data"
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session), \
         patch("sentence_transformers.SentenceTransformer") as mock_model, \
         patch("sentence_transformers.util.cos_sim") as mock_cos_sim:
        
        # Setup mocks
        mock_model.return_value.encode.return_value = [1, 0]
        mock_cos_sim.return_value = [[0.9], [0.5]]
        
        adapter = TransformersAdapter()
        results = await adapter.visual_rerank(
            query="test query", 
            items=[{"id": "1", "image_url": "url1"}, {"id": "2", "image_url": "url2"}]
        )
        
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["score"] == 0.9

@pytest.mark.asyncio
async def test_visual_rerank_failure():
    # Mocking an HTTP error
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        adapter = TransformersAdapter()
        with pytest.raises(Exception):
            await adapter.visual_rerank(
                query="test query", 
                items=[{"id": "1", "image_url": "invalid_url"}]
            )
