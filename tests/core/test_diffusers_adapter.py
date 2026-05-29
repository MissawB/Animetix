import pytest
import base64
import sys
from unittest.mock import MagicMock, patch
from io import BytesIO

# Mock missing modules for environment independence
mock_diffusers = MagicMock()
mock_pil = MagicMock()

# Save original modules to prevent test pollution
_orig_pil = sys.modules.get("PIL")
_orig_diffusers = sys.modules.get("diffusers")

sys.modules["diffusers"] = mock_diffusers
sys.modules["PIL"] = mock_pil

@pytest.fixture(autouse=True)
def mock_cuda_available():
    with patch("torch.cuda.is_available", return_value=True):
        yield

from adapters.inference.diffusers_adapter import DiffusersAdapter

@pytest.fixture(scope="module", autouse=True)
def cleanup_sys_modules():
    yield
    # Restore original modules after this module's tests complete
    if _orig_pil is not None:
        sys.modules["PIL"] = _orig_pil
    elif "PIL" in sys.modules:
        del sys.modules["PIL"]
        
    if _orig_diffusers is not None:
        sys.modules["diffusers"] = _orig_diffusers
    elif "diffusers" in sys.modules:
        del sys.modules["diffusers"]


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
