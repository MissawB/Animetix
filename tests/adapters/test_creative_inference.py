import pytest
import base64
import io
import sys
import numpy as np
from unittest.mock import MagicMock, patch
from PIL import Image

# Force modules to exist in sys.modules so they can be imported and patched
mock_diffusers = MagicMock()
mock_imageio = MagicMock()
mock_tts = MagicMock()
mock_cv2 = MagicMock()

sys.modules["diffusers"] = mock_diffusers
sys.modules["imageio"] = mock_imageio
sys.modules["TTS"] = mock_tts
sys.modules["TTS.api"] = mock_tts
sys.modules["cv2"] = mock_cv2

from adapters.inference.transformers_adapter import TransformersAdapter

@pytest.fixture
def adapter():
    return TransformersAdapter(use_4bit=False)

def test_generate_3d_scene_logic(adapter):
    """Vérifie la logique de projection RGB-D en PLY."""
    img = Image.new('RGB', (2, 2), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    dummy_rgb = img_byte_arr.getvalue()
    
    depth = Image.new('L', (2, 2), color=128)
    depth_byte_arr = io.BytesIO()
    depth.save(depth_byte_arr, format='PNG')
    dummy_depth = depth_byte_arr.getvalue()
    
    res = adapter.generate_3d_scene(dummy_rgb, dummy_depth)
    
    assert res["status"] == "success"
    assert "data:application/octet-stream;base64," in res["model_url"]
    assert res["viewer_type"] == "point_cloud"
    assert res["point_count"] > 0

def test_transform_video_to_anime_mocked(adapter):
    """Vérifie le workflow de transfert de style vidéo avec des mocks."""
    # Setup mocks directly on the pre-injected sys.modules
    mock_reader = MagicMock()
    dummy_frame = np.zeros((512, 512, 3), dtype=np.uint8)
    mock_reader.__iter__.return_value = [dummy_frame]
    mock_reader.get_meta_data.return_value = {"fps": 24}
    mock_imageio.get_reader.return_value = mock_reader
    
    pipe_instance = MagicMock()
    mock_image_out = MagicMock()
    mock_image_out.images = [Image.new('RGB', (512, 512))]
    pipe_instance.return_value = mock_image_out
    mock_diffusers.AutoPipelineForImage2Image.from_pretrained.return_value = pipe_instance
    
    # On mock l'ouverture du fichier temporaire et base64
    with patch("builtins.open", MagicMock()):
        with patch("os.unlink", MagicMock()):
            with patch("base64.b64encode", return_value=b"fake_base64"):
                res = adapter.transform_video_to_anime(b"fake_video_data", "Ghibli")
    
    assert "data:video/mp4;base64," in res
    mock_diffusers.AutoPipelineForImage2Image.from_pretrained.assert_called_once()

def test_clone_voice_mocked(adapter):
    """Vérifie le workflow de clonage vocal avec des mocks."""
    # mock_tts is sys.modules["TTS"] and sys.modules["TTS.api"]
    tts_instance = mock_tts.TTS.return_value
    
    # On mock l'écriture du fichier de sortie
    with patch("builtins.open", MagicMock()):
        with patch("os.unlink", MagicMock()):
            res = adapter.clone_voice("Hello", b"audio_sample")
            
    assert isinstance(res, bytes)
    mock_tts.TTS.assert_called_once()
