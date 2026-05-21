import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.adapters.inference.transformers_adapter import TransformersAdapter

@pytest.mark.asyncio
async def test_visual_rerank_success():
    # Mocking necessary components
    class MockResponse:
        status = 200
        async def read(self):
            return b"fake_image_data"
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockSession:
        def get(self, url, **kwargs):
            return MockResponse()
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("aiohttp.ClientSession", return_value=MockSession()), \
         patch("sentence_transformers.SentenceTransformer") as mock_model, \
         patch("sentence_transformers.util.cos_sim") as mock_cos_sim, \
         patch("PIL.Image.open") as mock_image_open:
        
        # Setup mocks
        mock_model.return_value.encode.return_value = [1, 0]
        mock_cos_sim.return_value = [[0.9], [0.5]]
        mock_image_open.return_value = MagicMock()
        
        adapter = TransformersAdapter()
        results = await adapter.visual_rerank(
            query="test query",
            image_urls=["url1", "url2"]
        )        
        assert len(results) >= 1
        assert "url" in results[0]
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
