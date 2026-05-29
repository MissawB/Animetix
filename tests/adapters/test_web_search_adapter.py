import pytest
from unittest.mock import patch, MagicMock
from adapters.persistence.web_search_adapter import DuckDuckGoSearchAdapter

def test_duckduckgo_search_adapter_success():
    # Create adapter
    adapter = DuckDuckGoSearchAdapter()
    
    # Mock the DDGS context manager
    mock_results = [
        {"title": "Eva Season 2", "href": "https://example.com/eva", "body": "Fans await season 2!"}
    ]
    
    with patch("adapters.persistence.web_search_adapter.DDGS") as mock_ddgs_cls:
        mock_ddgs_inst = MagicMock()
        mock_ddgs_cls.return_value.__enter__.return_value = mock_ddgs_inst
        mock_ddgs_inst.text.return_value = mock_results
        
        results = adapter.search("neon genesis evangelion", limit=3)
        
        assert len(results) == 1
        assert results[0]["title"] == "Eva Season 2"
        assert results[0]["url"] == "https://example.com/eva"
        assert results[0]["snippet"] == "Fans await season 2!"
        mock_ddgs_inst.text.assert_called_once_with("neon genesis evangelion", max_results=3)

def test_duckduckgo_search_adapter_exception():
    adapter = DuckDuckGoSearchAdapter()
    with patch("adapters.persistence.web_search_adapter.DDGS") as mock_ddgs_cls:
        mock_ddgs_cls.side_effect = Exception("DDG rate limit")
        results = adapter.search("neon genesis evangelion")
        # Should fallback to empty list instead of crashing
        assert results == []
