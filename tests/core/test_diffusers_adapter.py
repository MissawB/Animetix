import pytest
import base64
import sys
from unittest.mock import MagicMock, patch
from io import BytesIO

# Mock missing modules for environment independence
mock_diffusers = MagicMock()
mock_pil = MagicMock()
sys.modules["diffusers"] = mock_diffusers
sys.modules["PIL"] = mock_pil

from adapters.inference.diffusers_adapter import DiffusersAdapter

@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    # Mock the __call__ return value to have images[0]
    mock_image = MagicMock()
    mock_result = MagicMock()
    mock_result.images = [mock_image]
    pipeline.return_value = mock_result
    
    mock_diffusers.AutoPipelineForText2Image.from_pretrained.return_value = pipeline
    return pipeline

def test_generate_image_success(mock_pipeline):
    adapter = DiffusersAdapter(model_id="test/model")
    
    # Run generation
    # On mock l'encodage base64 pour éviter PIL.Image
    with patch("base64.b64encode") as mock_b64:
        mock_b64.return_value = b"fake_base64"
        result = adapter.generate_image("A futuristic city", "Cyberpunk")
    
    # Assertions
    assert result.startswith("data:image/jpeg;base64,")
    # Verify pipeline was called
    mock_pipeline.assert_called_once()
    args, kwargs = mock_pipeline.call_args
    assert "A futuristic city, Cyberpunk" in kwargs["prompt"]

def test_health_check(mock_pipeline):
    adapter = DiffusersAdapter(model_id="test/model")
    # Trigger load
    with patch("base64.b64encode"):
        adapter.generate_image("test")
    
    health = adapter.health_check()
    assert health["status"] == "online"
    assert health["engine"] == "diffusers"
    assert health["model"] == "test/model"
