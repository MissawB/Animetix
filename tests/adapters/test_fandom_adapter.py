import pytest
from unittest.mock import patch, MagicMock
from adapters.persistence.fandom_adapter import FandomAdapter

@patch('requests.get')
def test_fetch_character_data_success(mock_get):
    # Mock response from MediaWiki API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "parse": {
            "wikitext": {
                "*": "Character info here"
            }
        }
    }
    mock_get.return_value = mock_response

    adapter = FandomAdapter()
    data = adapter.fetch_character_data("Goku")

    assert data["name"] == "Goku"
    assert "wikitext" in data
    assert data["wikitext"] == "Character info here"
    mock_get.assert_called_once()
