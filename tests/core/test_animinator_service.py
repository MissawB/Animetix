import pytest
from unittest.mock import MagicMock
from core.domain.services.animinator_service import AniminatorDomainService

@pytest.fixture
def mock_llm_service():
    return MagicMock()

@pytest.fixture
def animinator_service(mock_llm_service):
    return AniminatorDomainService(llm_service=mock_llm_service)

def test_select_secret(animinator_service):
    catalog = {
        'title_to_full_data': {
            'A': {'title': 'A'}, 
            'B': {'title': 'B'}
        }
    }
    secret = animinator_service.select_secret(catalog)
    assert secret in ['A', 'B']

def test_select_secret_empty(animinator_service):
    catalog = {'titles': []}
    assert animinator_service.select_secret(catalog) is None

def test_ask_oracle(animinator_service, mock_llm_service):
    mock_llm_service.ask_oracle.return_value = "Yes"
    res = animinator_service.ask_oracle("Anime", "Naruto", {}, "Is it a ninja?")
    assert res == "Yes"
    mock_llm_service.ask_oracle.assert_called_once_with("Anime", "Naruto", "Is it a ninja?")

def test_check_guess(animinator_service):
    assert animinator_service.check_guess(" Naruto ", "naruto") is True
    assert animinator_service.check_guess("Bleach", "Naruto") is False
