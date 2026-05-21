import pytest
from unittest.mock import patch, MagicMock
from adapters.persistence.fandom_adapter import FandomAdapter

@patch('requests.get')
def test_fetch_character_data_success(mock_get):
    # Mock response from MediaWiki API (action=query format)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
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
    mock_get.return_value = mock_response

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Goku")

    assert data["name"] == "Goku"
    assert data["wikitext"] == "Character info here"
    assert data["image_url"] == "https://example.com/goku.jpg"
    mock_get.assert_called_once()

@patch('requests.get')
def test_fetch_character_data_missing(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "query": {
            "pages": [{"title": "Unknown", "missing": True}]
        }
    }
    mock_get.return_value = mock_response

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Unknown")

    assert data["name"] == "Unknown"
    assert data["wikitext"] == ""
    assert data["image_url"] is None
    mock_get.assert_called_once()
