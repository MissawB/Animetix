import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel

from adapters.inference.google_genai_adapter import GoogleGenAIAdapter, get_image_mime_type
from core.domain.entities.ai_schemas import TokenLogProb, InferenceResponse

class DummyModel(BaseModel):
    name: str
    rating: float

def test_image_mime_type():
    assert get_image_mime_type(b'\x89PNG\r\n\x1a\n') == "image/png"
    assert get_image_mime_type(b'\xff\xd8\xff') == "image/jpeg"
    assert get_image_mime_type(b'RIFFxxxxWEBP') == "image/webp"
    assert get_image_mime_type(b'GIF89axxxx') == "image/gif"
    assert get_image_mime_type(b'unknown') == "image/png"

@patch("adapters.inference.google_genai_adapter.genai.Client")
def test_adapter_initialization_developer(mock_client):
    # If GEMINI_API_KEY is present or provided, use developer mode
    adapter = GoogleGenAIAdapter(api_key="test-api-key", vertexai=False)
    mock_client.assert_called_once_with(api_key="test-api-key")
    assert adapter.use_vertexai is False
    assert adapter.health_check()["status"] == "online"

@patch("adapters.inference.google_genai_adapter.genai.Client")
def test_adapter_initialization_vertex(mock_client):
    # Test Vertex AI mode
    adapter = GoogleGenAIAdapter(project="my-project", location="us-central1", vertexai=True)
    mock_client.assert_called_once_with(vertexai=True, project="my-project", location="us-central1")
    assert adapter.use_vertexai is True

@patch("adapters.inference.google_genai_adapter.genai.Client")
def test_generate_text(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mocking generate_content response
    mock_response = MagicMock()
    mock_response.text = "Hello, world!"
    
    # Mock usage metadata
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 5
    mock_response.usage_metadata.total_token_count = 15
    
    # Mock candidate content parts for thoughts
    mock_part = MagicMock()
    mock_part.thought = True
    mock_part.text = "Thinking..."
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]
    
    # Mock logprobs_result
    mock_chosen = MagicMock()
    mock_chosen.token = "Hello"
    mock_chosen.log_probability = -0.05
    
    mock_alt = MagicMock()
    mock_alt.token = "Hi"
    mock_alt.log_probability = -1.2
    
    mock_step_alt = MagicMock()
    mock_step_alt.candidates = [mock_alt]
    
    mock_response.candidates[0].logprobs_result = MagicMock()
    mock_response.candidates[0].logprobs_result.chosen_candidates = [mock_chosen]
    mock_response.candidates[0].logprobs_result.top_candidates = [mock_step_alt]
    
    mock_client.models.generate_content.return_value = mock_response
    
    adapter = GoogleGenAIAdapter(api_key="key", model_name="gemini-3.5-flash")
    
    res = adapter.generate(prompt="Test prompt", include_logprobs=True)
    
    assert isinstance(res, InferenceResponse)
    assert res.text == "Hello, world!"
    assert res.metadata.usage["prompt_tokens"] == 10
    assert res.metadata.thinking == "Thinking..."
    assert len(res.metadata.logprobs) == 1
    assert res.metadata.logprobs[0].token == "Hello"
    assert res.metadata.logprobs[0].logprob == -0.05
    assert res.metadata.logprobs[0].top_logprobs[0]["Hi"] == -1.2

@patch("adapters.inference.google_genai_adapter.genai.Client")
def test_stream_generate(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mocking generate_content_stream response chunk
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "Chunk 1"
    mock_chunk1.usage_metadata = MagicMock()
    mock_chunk1.usage_metadata.prompt_token_count = 10
    mock_chunk1.usage_metadata.candidates_token_count = 3
    mock_chunk1.usage_metadata.total_token_count = 13
    mock_chunk1.candidates = []
    
    mock_client.models.generate_content_stream.return_value = [mock_chunk1]
    
    adapter = GoogleGenAIAdapter(api_key="key")
    chunks = list(adapter.stream_generate(prompt="Test stream"))
    
    assert len(chunks) == 1
    assert chunks[0].text == "Chunk 1"

@patch("adapters.inference.google_genai_adapter.genai.Client")
def test_generate_structured(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    dummy_instance = DummyModel(name="Naruto", rating=9.5)
    mock_response.parsed = dummy_instance
    mock_client.models.generate_content.return_value = mock_response
    
    adapter = GoogleGenAIAdapter(api_key="key")
    res = adapter.generate_structured(prompt="Get Naruto", response_model=DummyModel)
    
    assert res.name == "Naruto"
    assert res.rating == 9.5

@patch("adapters.inference.google_genai_adapter.genai.Client")
def test_generate_image_description(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "A beautiful anime landscape"
    mock_client.models.generate_content.return_value = mock_response
    
    adapter = GoogleGenAIAdapter(api_key="key")
    desc = adapter.generate_image_description(image_data=b"fake-bytes", prompt="Describe this")
    
    assert desc == "A beautiful anime landscape"
