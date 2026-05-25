import pytest
import logging
from unittest.mock import MagicMock
from pydantic import BaseModel
from src.core.domain.services.llm_service import LLMService
from src.core.domain.exceptions import InferenceError, ParsingError

class MockSchema(BaseModel):
    name: str
    age: int

def test_generate_structured_success():
    inference_engine = MagicMock()
    prompt_manager = MagicMock()
    # Mocking a valid JSON response
    inference_engine.generate.return_value = '{"name": "Alice", "age": 30}'
    
    service = LLMService(inference_engine, prompt_manager)
    result = service.generate_structured("test prompt", MockSchema)
    
    assert result.name == "Alice"
    assert result.age == 30
    assert inference_engine.generate.call_count == 1

def test_generate_structured_retry_success():
    inference_engine = MagicMock()
    prompt_manager = MagicMock()
    
    # First call returns invalid JSON, second call returns valid JSON
    inference_engine.generate.side_effect = [
        'Invalid JSON string',
        '{"name": "Bob", "age": 25}'
    ]
    
    service = LLMService(inference_engine, prompt_manager)
    result = service.generate_structured("test prompt", MockSchema)
    
    assert result.name == "Bob"
    assert result.age == 25
    assert inference_engine.generate.call_count == 2

def test_generate_structured_retry_failure():
    inference_engine = MagicMock()
    prompt_manager = MagicMock()
    
    # Both calls return invalid JSON
    inference_engine.generate.side_effect = [
        'Invalid JSON 1',
        'Invalid JSON 2'
    ]
    
    service = LLMService(inference_engine, prompt_manager)
    with pytest.raises(ParsingError) as excinfo:
        service.generate_structured("test prompt", MockSchema)
    
    assert "JSON recovery failed after retry" in str(excinfo.value)
    assert inference_engine.generate.call_count == 2

def test_generate_inference_error_context():
    inference_engine = MagicMock()
    prompt_manager = MagicMock()
    inference_engine.generate.side_effect = Exception("Connection Timeout")
    
    service = LLMService(inference_engine, prompt_manager)
    with pytest.raises(InferenceError) as excinfo:
        service.generate("test prompt")
    
    assert "AI Generation failed: Connection Timeout" in str(excinfo.value)
    assert excinfo.value.context.get('original_error') == "Connection Timeout"

def test_generate_inference_error_logging(caplog):
    inference_engine = MagicMock()
    prompt_manager = MagicMock()
    inference_engine.generate.side_effect = Exception("Connection Timeout")
    
    # Ensure logger propagates and level is high enough
    logger = logging.getLogger('animetix')
    logger.propagate = True
    
    service = LLMService(inference_engine, prompt_manager)
    
    with caplog.at_level(logging.ERROR, logger='animetix'):
        with pytest.raises(InferenceError):
            service.generate("test prompt")
    
    # Check records instead of text for better reliability
    assert any("AI Generation failed: Connection Timeout" in record.message for record in caplog.records)
