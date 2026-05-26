import pytest
from unittest.mock import MagicMock
from src.core.domain.services.companion_service import CompanionService

@pytest.fixture
def mock_llm_service():
    return MagicMock()

@pytest.fixture
def mock_prompt_manager():
    return MagicMock()

def test_companion_service_generate_response_sensei(mock_llm_service, mock_prompt_manager):
    # Setup
    mock_prompt_manager.get_prompt.return_value = ("formatted_prompt", "system_prompt")
    mock_llm_service.generate.return_value = "Réponse du Sensei"
    
    service = CompanionService(mock_llm_service, mock_prompt_manager)
    
    # Execute
    response = service.generate_response(
        "sensei", 
        "Bonjour", 
        context="RAG info", 
        history=[{"role": "user", "content": "Hi"}]
    )
    
    # Verify
    mock_prompt_manager.get_prompt.assert_called_once()
    args, kwargs = mock_prompt_manager.get_prompt.call_args
    assert args[0] == "sensei_personality"
    assert kwargs["user_msg"] == "Bonjour"
    assert kwargs["context"] == "RAG info"
    assert "User: Hi" in kwargs["history"]
    
    mock_llm_service.generate.assert_called_once_with("formatted_prompt", system_prompt="system_prompt")
    assert response == "Réponse du Sensei"

def test_companion_service_generate_response_tsundere(mock_llm_service, mock_prompt_manager):
    # Setup
    mock_prompt_manager.get_prompt.return_value = ("baka prompt", "tsundere system")
    mock_llm_service.generate.return_value = "Baka! C'est pas pour toi!"
    
    service = CompanionService(mock_llm_service, mock_prompt_manager)
    
    # Execute
    response = service.generate_response("tsundere", "Aide-moi")
    
    # Verify
    mock_prompt_manager.get_prompt.assert_called_once()
    assert mock_prompt_manager.get_prompt.call_args[0][0] == "tsundere_personality"
    assert response == "Baka! C'est pas pour toi!"

def test_companion_service_invalid_mentor(mock_llm_service, mock_prompt_manager):
    service = CompanionService(mock_llm_service, mock_prompt_manager)
    with pytest.raises(ValueError, match="Unknown mentor ID"):
        service.generate_response("invalid", "msg")
