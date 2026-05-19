import pytest
from unittest.mock import MagicMock
from core.domain.services.llm_service import LLMService
from core.domain.exceptions import InferenceError

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("prompt", "system")
    return pm

@pytest.fixture
def llm_service(mock_engine, mock_prompt_manager):
    return LLMService(inference_engine=mock_engine, prompt_manager=mock_prompt_manager)

def test_generate_success(llm_service, mock_engine):
    mock_engine.generate.return_value = "Hello World"
    assert llm_service.generate("Hi") == "Hello World"

def test_generate_empty(llm_service, mock_engine):
    mock_engine.generate.return_value = ""
    with pytest.raises(InferenceError, match="Engine returned empty response"):
        llm_service.generate("Hi")

def test_generate_error(llm_service, mock_engine):
    mock_engine.generate.side_effect = Exception("Boom")
    with pytest.raises(InferenceError, match="AI Generation failed"):
        llm_service.generate("Hi")

def test_generate_with_forbidden_terms(llm_service, mock_engine):
    mock_engine.generate.return_value = "Naruto is a ninja from Naruto series."
    res = llm_service.generate("Hi", forbidden_terms=["Naruto"])
    assert "[CENSURÉ]" in res
    assert "Naruto" not in res

def test_generate_fusion_scenario(llm_service, mock_engine):
    mock_engine.generate.return_value = "Fusion story"
    res = llm_service.generate_fusion_scenario("Anime", {"title": "Naruto"}, {"title": "Sasuke"}, "Français")
    assert res == "Fusion story"
    mock_engine.generate.assert_called_once()

def test_get_status(llm_service, mock_engine):
    mock_engine.health_check.return_value = {"status": "ok"}
    assert llm_service.get_status() == {"status": "ok"}
