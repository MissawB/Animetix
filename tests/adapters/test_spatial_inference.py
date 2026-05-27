import pytest
from io import BytesIO
from PIL import Image
from unittest.mock import MagicMock, patch
from src.adapters.inference.diffusers_adapter import DiffusersAdapter
from src.adapters.inference.vision_transformers_adapter import VisionTransformersAdapter

@pytest.fixture
def sample_image():
    img = Image.new('RGB', (256, 256), color=(73, 109, 137))
    buf = BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

def test_diffusers_adapter_depth_estimation(sample_image):
    mock_pipeline = MagicMock()
    dummy_depth = Image.new('L', (256, 256), color=128)
    mock_pipeline.return_value = {"depth": dummy_depth}

    with patch("transformers.pipeline", return_value=mock_pipeline):
        adapter = DiffusersAdapter()
        depth_map = adapter.estimate_depth(sample_image)
        assert depth_map is not None
        assert len(depth_map) > 0
        img = Image.open(BytesIO(depth_map))
        assert img.size == (256, 256)

def test_vision_transformers_adapter_depth_estimation(sample_image):
    mock_pipeline = MagicMock()
    dummy_depth = Image.new('L', (256, 256), color=128)
    mock_pipeline.return_value = {"depth": dummy_depth}

    with patch("transformers.pipeline", return_value=mock_pipeline):
        adapter = VisionTransformersAdapter()
        depth_map = adapter.estimate_depth(sample_image)
        assert depth_map is not None
        assert len(depth_map) > 0
        img = Image.open(BytesIO(depth_map))
        assert img.size == (256, 256)

def test_vision_transformers_adapter_generate_3d_scene(sample_image):
    mock_pipeline = MagicMock()
    dummy_depth = Image.new('L', (256, 256), color=128)
    mock_pipeline.return_value = {"depth": dummy_depth}

    with patch("transformers.pipeline", return_value=mock_pipeline):
        adapter = VisionTransformersAdapter()
        depth_map = adapter.estimate_depth(sample_image)
        scene = adapter.generate_3d_scene(sample_image, depth_map)
        assert scene["status"] == "success"
        assert "placeholder" in scene["model_url"]
