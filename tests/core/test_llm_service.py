import pytest
from unittest.mock import MagicMock
from core.domain.services.llm_service import LLMService
from core.domain.exceptions import InferenceError
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata

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
    mock_engine.generate.return_value = InferenceResponse(text="Hello World")
    assert llm_service.generate("Hi") == "Hello World"

def test_generate_empty(llm_service, mock_engine):
    mock_engine.generate.return_value = InferenceResponse(text="")
    with pytest.raises(InferenceError, match="Engine returned empty response"):
        llm_service.generate("Hi")

def test_generate_error(llm_service, mock_engine):
    mock_engine.generate.side_effect = Exception("Boom")
    with pytest.raises(InferenceError, match="AI Generation failed"):
        llm_service.generate("Hi")

def test_generate_with_forbidden_terms(llm_service, mock_engine):
    mock_engine.generate.return_value = InferenceResponse(text="Naruto is a ninja from Naruto series.")
    res = llm_service.generate("Hi", forbidden_terms=["Naruto"])
    assert "[CENSURÉ]" in res
    assert "Naruto" not in res

def test_generate_fusion_scenario(llm_service, mock_engine):
    mock_engine.generate.return_value = InferenceResponse(text="Fusion story")
    res = llm_service.generate_fusion_scenario("Anime", {"title": "Naruto"}, {"title": "Sasuke"}, "Français")
    assert res == "Fusion story"
    mock_engine.generate.assert_called_once()

def test_get_status(llm_service, mock_engine):
    mock_engine.health_check.return_value = {"status": "ok"}
    assert llm_service.get_status() == {"status": "ok"}

def test_generate_logs_usage_correctly(llm_service, mock_engine):
    from core.ports.usage_port import UsagePort
    from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata
    from unittest.mock import MagicMock
    
    usage_port = MagicMock(spec=UsagePort)
    llm_service.usage_port = usage_port
    
    mock_engine.generate.return_value = InferenceResponse(
        text="Response",
        metadata=InferenceMetadata(usage={"prompt_tokens": 10, "completion_tokens": 5})
    )
    
    llm_service.generate("Prompt", "System")
    
    usage_port.log_usage.assert_called_once()
    args, kwargs = usage_port.log_usage.call_args
    assert kwargs['input_tokens'] == 10
    assert kwargs['output_tokens'] == 5
