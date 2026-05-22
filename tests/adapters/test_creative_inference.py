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
mock_audioldm = MagicMock()

# Set a mock __spec__ for them to satisfy find_spec and checks
for m_obj in [mock_diffusers, mock_imageio, mock_tts, mock_cv2, mock_audioldm]:
    m_obj.__spec__ = MagicMock()

@pytest.fixture(autouse=True)
def mock_sys_modules(monkeypatch):
    monkeypatch.setitem(sys.modules, "diffusers", mock_diffusers)
    monkeypatch.setitem(sys.modules, "imageio", mock_imageio)
    monkeypatch.setitem(sys.modules, "TTS", mock_tts)
    monkeypatch.setitem(sys.modules, "TTS.api", mock_tts)
    monkeypatch.setitem(sys.modules, "cv2", mock_cv2)
    monkeypatch.setitem(sys.modules, "audioldm", mock_audioldm)

pytest.importorskip("scipy")

from adapters.inference.transformers_adapter import TransformersAdapter
from core.domain.exceptions import InferenceError

@pytest.fixture
def adapter():
    return TransformersAdapter(use_4bit=False)

def test_inference_error_on_failure(adapter):
    """Vérifie que l'adaptateur lève une InferenceError en cas de pépin."""
    with patch.object(adapter, "_load_model", side_effect=Exception("GPU OOM")):
        with pytest.raises(InferenceError) as excinfo:
            adapter.generate("Hello")
        assert "Critical failure during model loading: GPU OOM" in str(excinfo.value)

def test_generate_3d_scene_logic(adapter):
    """Vérifie la logique de projection RGB-D en PLY."""
    img = Image.new('RGB', (2, 2))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    dummy_rgb = img_byte_arr.getvalue()
    
    depth = Image.new('L', (2, 2), color=255)
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
    
    # On mock l'écriture et la lecture du fichier de sortie
    m = MagicMock()
    m.__enter__.return_value.read.return_value = b"fake_audio_bytes"
    
    with patch("builtins.open", return_value=m):
        with patch("os.unlink", MagicMock()):
            res = adapter.clone_voice("Hello", b"audio_sample")
            
    assert res == b"fake_audio_bytes"
    mock_tts.TTS.assert_called_once()

def test_generate_soundscape_success(adapter):
    """Vérifie le workflow de génération de soundscape."""
    mock_pipe = MagicMock()
    mock_pipe.return_value = {"audios": np.zeros((1, 16000))}
    
    with patch("audioldm.build_model", return_value=mock_pipe):
        with patch("scipy.io.wavfile.write", MagicMock()):
            with patch("base64.b64encode", return_value=b"fake_audio_base64"):
                res = adapter.generate_soundscape({"scene": "forest"}, prompt="forest sounds")
                
    assert res.startswith("data:audio/wav;base64,")
    assert "fake_audio_base64" in res

def test_generate_soundscape_failure(adapter):
    """Vérifie que la génération échoue proprement si scipy est manquant."""
    # Simuler l'absence de scipy enlevant la fonction de sauvegarde
    with patch("scipy.io.wavfile.write", side_effect=ImportError("No scipy")):
        with pytest.raises(InferenceError):
            adapter.generate_soundscape({"scene": "forest"}, prompt="forest sounds")
