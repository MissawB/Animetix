import pytest
from unittest.mock import MagicMock, patch
from core.domain.services.llm_service import LLMService
from core.domain.exceptions import QuotaExceededError, InferenceError

@pytest.fixture
def mock_inference_engine():
    engine = MagicMock()
    engine.generate.return_value = "Normal response"
    return engine

@pytest.fixture
def mock_prompt_manager():
    return MagicMock()

@pytest.fixture
def mock_usage_port():
    port = MagicMock()
    port.check_quota.return_value = True
    return port

def test_generate_raises_quota_exceeded(mock_inference_engine, mock_prompt_manager, mock_usage_port):
    # Setup
    mock_usage_port.check_quota.return_value = False
    service = LLMService(mock_inference_engine, mock_prompt_manager, usage_port=mock_usage_port)
    
    # Execute & Verify
    with pytest.raises(QuotaExceededError) as excinfo:
        service.generate("test prompt", user_id=123, tier='free')
    
    assert "reached your daily AI limit" in str(excinfo.value)
    mock_inference_engine.generate.assert_not_called()

def test_generate_allows_within_quota(mock_inference_engine, mock_prompt_manager, mock_usage_port):
    # Setup
    mock_usage_port.check_quota.return_value = True
    service = LLMService(mock_inference_engine, mock_prompt_manager, usage_port=mock_usage_port)
    
    # Execute
    res = service.generate("test prompt", user_id=123, tier='free')
    
    # Verify
    assert res == "Normal response"
    mock_inference_engine.generate.assert_called_once()

@patch("animetix.middleware.get_current_user_id")
@patch("animetix.middleware.get_current_user_tier")
def test_generate_retrieves_from_middleware(mock_get_tier, mock_get_id, mock_inference_engine, mock_prompt_manager, mock_usage_port):
    # Setup
    mock_get_id.return_value = 456
    mock_get_tier.return_value = 'pro'
    mock_usage_port.check_quota.return_value = False
    
    service = LLMService(mock_inference_engine, mock_prompt_manager, usage_port=mock_usage_port)
    
    # Execute & Verify
    with pytest.raises(QuotaExceededError):
        service.generate("test prompt")
        
    mock_usage_port.check_quota.assert_called_with(456, 'pro')

def test_generate_no_usage_port_skips_check(mock_inference_engine, mock_prompt_manager):
    # Setup
    service = LLMService(mock_inference_engine, mock_prompt_manager, usage_port=None)
    
    # Execute
    res = service.generate("test prompt", user_id=123)
    
    # Verify
    assert res == "Normal response"
    mock_inference_engine.generate.assert_called_once()
