import pytest
from unittest.mock import patch, MagicMock
from adapters.persistence.fandom_adapter import FandomAdapter

@patch('adapters.persistence.fandom_adapter.httpx.get')
def test_fetch_character_data_success(mock_get):
    # Setup search response
    mock_search_res = MagicMock()
    mock_search_res.status_code = 200
    mock_search_res.json.return_value = {
        "query": {
            "search": [
                {"title": "Goku"}
            ]
        }
    }

    # Setup fetch response
    mock_fetch_res = MagicMock()
    mock_fetch_res.status_code = 200
    mock_fetch_res.json.return_value = {
        "query": {
            "pages": [
                {
                    "pageid": 123,
                    "title": "Goku",
                    "original": {"source": "https://example.com/goku.jpg"},
                    "revisions": [{"content": "Character info here"}]
                }
            ]
        }
    }

    mock_get.side_effect = [mock_search_res, mock_fetch_res]

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Goku")

    assert len(data) == 1
    assert data[0]["name"] == "Goku"
    assert data[0]["wikitext"] == "Character info here"
    assert data[0]["image_url"] == "https://example.com/goku.jpg"
    assert mock_get.call_count == 2

@patch('adapters.persistence.fandom_adapter.httpx.get')
def test_fetch_character_data_missing(mock_get):
    mock_search_res = MagicMock()
    mock_search_res.status_code = 200
    mock_search_res.json.return_value = {
        "query": {
            "search": []
        }
    }
    mock_get.return_value = mock_search_res

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Unknown")

    assert data == []
    mock_get.assert_called_once()
