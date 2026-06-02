import pytest
from unittest.mock import patch, MagicMock
from adapters.persistence.web_search_adapter import UnifiedWebSearchAdapter

def test_tavily_search_success():
    with patch.dict("os.environ", {"TAVILY_API_KEY": "test_tavily_key"}):
        adapter = UnifiedWebSearchAdapter()
        assert adapter.tavily_api_key == "test_tavily_key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "Tavily result", "url": "https://example.com/tavily", "content": "Tavily content"}
            ]
        }
        
        with patch("adapters.persistence.web_search_adapter.safe_http_request", return_value=mock_response) as mock_req:
            results = adapter.search("tavily query", limit=2)
            
            assert len(results) == 1
            assert results[0]["title"] == "Tavily result"
            assert results[0]["url"] == "https://example.com/tavily"
            assert results[0]["snippet"] == "Tavily content"
            mock_req.assert_called_once()
            
            # Verify payload passed to safe_http_request
            args, kwargs = mock_req.call_args
            assert args[0] == "POST"
            assert args[1] == "https://api.tavily.com/search"
            assert kwargs["json"]["query"] == "tavily query"
            assert kwargs["json"]["max_results"] == 2

def test_gemini_grounding_search_success():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test_gemini_key"}):
        # Ensure TAVILY_API_KEY is not present to trigger Gemini
        with patch.dict("os.environ", {"TAVILY_API_KEY": ""}, clear=False):
            adapter = UnifiedWebSearchAdapter()
            assert adapter.gemini_api_key == "test_gemini_key"
            
            mock_chunk = MagicMock()
            mock_web = MagicMock()
            mock_web.title = "Gemini Title"
            mock_web.uri = "https://example.com/gemini"
            mock_chunk.web = mock_web
            
            mock_metadata = MagicMock()
            mock_metadata.grounding_chunks = [mock_chunk]
            
            mock_candidate = MagicMock()
            mock_candidate.grounding_metadata = mock_metadata
            
            mock_response = MagicMock()
            mock_response.candidates = [mock_candidate]
            mock_response.text = "Gemini synthesized answer."
            
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            
            with patch("google.genai.Client", return_value=mock_client) as mock_client_cls:
                results = adapter.search("gemini query", limit=1)
                
                assert len(results) == 1
                assert results[0]["title"] == "Gemini Title"
                assert results[0]["url"] == "https://example.com/gemini"
                assert results[0]["snippet"] == "Gemini synthesized answer."
                mock_client_cls.assert_called_once_with(api_key="test_gemini_key")


def test_no_credentials_returns_empty_list():
    with patch.dict("os.environ", {"TAVILY_API_KEY": "", "GEMINI_API_KEY": ""}):
        adapter = UnifiedWebSearchAdapter()
        results = adapter.search("neon genesis evangelion")
        assert results == []
