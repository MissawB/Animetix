import pytest
from unittest.mock import MagicMock, patch
from core.domain.exceptions import InferenceError
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.brain_api_adapter import BrainAPIAdapter

class FakeBrainAPIAdapter(BrainAPIAdapter):
    def __init__(self):
        super().__init__(brain_api_url="http://fake-api")
        
    def generate_image(self, prompt: str, style: str = "") -> str:
        return "data:image/jpeg;base64,cloud_image"
        
    def health_check(self) -> dict:
        return {"status": "offline", "engine": "Brain-API"}

def test_diffusers_no_cuda_raises():
    adapter = DiffusersAdapter()
    with patch("torch.cuda.is_available", return_value=False):
        with pytest.raises(InferenceError) as exc_info:
            adapter.generate_image("prompt")
        assert "CUDA GPU is not available" in str(exc_info.value)

def test_audio_no_cuda_raises():
    adapter = AudioTransformersAdapter()
    with patch("torch.cuda.is_available", return_value=False):
        with pytest.raises(InferenceError) as exc_info:
            adapter.clone_voice("text", b"audio")
        assert "CUDA GPU is not available" in str(exc_info.value)

def test_diffusers_inpaint_pillow_fallback_on_no_cuda():
    from PIL import Image
    from io import BytesIO
    
    # Create valid dummy JPEG image bytes
    img = Image.new("RGB", (100, 100), "white")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()
    
    adapter = DiffusersAdapter()
    with patch("torch.cuda.is_available", return_value=False):
        res = adapter.inpaint_text_bubbles(image_bytes, [{"bbox": [0,0,10,10], "text": "Hello"}])
        assert res.startswith("data:image/jpeg;base64,")

def test_fallback_adapter_transitions_on_no_cuda():
    fake_brain = FakeBrainAPIAdapter()
    mock_diffusers = DiffusersAdapter()
    
    # We put the local adapter (mock_diffusers) first, and the cloud/remote adapter (fake_brain) second,
    # to verify that when the local adapter fails due to no CUDA, we successfully fall back to the Brain API adapter.
    fallback = FallbackInferenceAdapter(adapters=[mock_diffusers, fake_brain])
    
    with patch("torch.cuda.is_available", return_value=False):
        res = fallback.generate_image("prompt")
        assert res == "data:image/jpeg;base64,cloud_image"
