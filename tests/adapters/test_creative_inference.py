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
mock_transformers = MagicMock()
mock_torch = MagicMock()
mock_scipy = MagicMock()
mock_pydub = MagicMock()

# Set a mock __spec__ for them to satisfy find_spec and checks
for m_obj in [mock_diffusers, mock_imageio, mock_tts, mock_cv2, mock_audioldm, mock_transformers, mock_torch, mock_scipy, mock_pydub]:
    m_obj.__spec__ = MagicMock()

@pytest.fixture(autouse=True)
def mock_sys_modules(monkeypatch):
    monkeypatch.setitem(sys.modules, "diffusers", mock_diffusers)
    monkeypatch.setitem(sys.modules, "imageio", mock_imageio)
    monkeypatch.setitem(sys.modules, "TTS", mock_tts)
    monkeypatch.setitem(sys.modules, "TTS.api", mock_tts)
    monkeypatch.setitem(sys.modules, "cv2", mock_cv2)
    monkeypatch.setitem(sys.modules, "audioldm", mock_audioldm)
    monkeypatch.setitem(sys.modules, "transformers", mock_transformers)
    monkeypatch.setitem(sys.modules, "torch", mock_torch)
    monkeypatch.setitem(sys.modules, "scipy", mock_scipy)
    monkeypatch.setitem(sys.modules, "scipy.io", MagicMock())
    monkeypatch.setitem(sys.modules, "scipy.io.wavfile", mock_scipy.io.wavfile)
    monkeypatch.setitem(sys.modules, "pydub", mock_pydub)
    
    # Also clear the lazy import cache so that it doesn't leak into other tests
    from core.utils.lazy_import import _loaded_modules
    for m in ["diffusers", "imageio", "TTS", "cv2", "audioldm", "transformers", "torch", "scipy", "pydub"]:
        if m in _loaded_modules:
            del _loaded_modules[m]

    yield
    
    from core.utils.lazy_import import _loaded_modules
    for m in ["diffusers", "imageio", "TTS", "cv2", "audioldm", "transformers", "torch", "scipy", "pydub"]:
        if m in _loaded_modules:
            del _loaded_modules[m]

pytest.importorskip("scipy")

from adapters.inference.local_text_adapter import LocalTextAdapter
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter
from adapters.inference.vision_transformers_adapter import VisionTransformersAdapter
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.domain.exceptions import InferenceError

@pytest.fixture
def transformers_adapter():
    return LocalTextAdapter(use_4bit=False)

@pytest.fixture
def diffusers_adapter():
    return DiffusersAdapter()

@pytest.fixture
def xtts_adapter():
    return AudioTransformersAdapter()

@pytest.fixture
def vision_adapter():
    return VisionTransformersAdapter(use_4bit=False)

@pytest.fixture
def fallback_adapter(transformers_adapter, vision_adapter):
    return FallbackInferenceAdapter(adapters=[transformers_adapter, vision_adapter])

def test_inference_error_on_failure(transformers_adapter):
    """Vérifie que l'adaptateur lève une InferenceError en cas de pépin."""
    with patch.object(transformers_adapter, "_load_model", side_effect=InferenceError("Critical failure during model loading: GPU OOM")):
        with pytest.raises(InferenceError) as excinfo:
            transformers_adapter.generate("Hello")
        assert "Critical failure during model loading: GPU OOM" in str(excinfo.value)

def test_generate_3d_scene_logic():
    """Vérifie la logique de projection RGB-D en PLY transférée dans SpatialComputingService."""
    from core.domain.services.spatial_computing_service import SpatialComputingService
    mock_engine = MagicMock()
    service = SpatialComputingService(inference_engine=mock_engine)
    
    img = Image.new('RGB', (2, 2))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    dummy_rgb = img_byte_arr.getvalue()
    
    depth = Image.new('L', (2, 2), color=255)
    depth_byte_arr = io.BytesIO()
    depth.save(depth_byte_arr, format='PNG')
    dummy_depth = depth_byte_arr.getvalue()
    
    res = service.generate_3d_scene(dummy_rgb, dummy_depth)
    
    assert res["status"] == "success"
    assert "data:application/octet-stream;base64," in res["model_url"]
    assert res["viewer_type"] == "point_cloud"
    assert res["point_count"] > 0

def test_transform_video_to_anime_mocked(diffusers_adapter):
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
                res = diffusers_adapter.transform_video_to_anime(b"fake_video_data", "Ghibli")
    
    assert "data:video/mp4;base64," in res
    mock_diffusers.AutoPipelineForImage2Image.from_pretrained.assert_called_once()

def test_clone_voice_mocked(xtts_adapter):
    """Vérifie le workflow de clonage vocal avec des mocks."""
    # mock_tts is sys.modules["TTS"] and sys.modules["TTS.api"]
    tts_instance = mock_tts.TTS.return_value
    
    # On mock l'écriture et la lecture du fichier de sortie
    m = MagicMock()
    m.__enter__.return_value.read.return_value = b"fake_audio_bytes"
    
    with patch("builtins.open", return_value=m):
        with patch("os.unlink", MagicMock()):
            res = xtts_adapter.clone_voice("Hello", b"audio_sample")
            
    assert res == b"fake_audio_bytes"
    mock_tts.TTS.assert_called_once()

def test_generate_soundscape_success(xtts_adapter):
    """Vérifie le workflow de génération de soundscape."""
    mock_pipe = MagicMock()
    mock_pipe.return_value = MagicMock(audios=[np.zeros((1, 16000))])
    mock_diffusers.AudioLDMPipeline.from_pretrained.return_value = mock_pipe
    
    with patch("scipy.io.wavfile.write", MagicMock()):
        with patch("base64.b64encode", return_value=b"fake_audio_base64"):
            res = xtts_adapter.generate_soundscape({"scene": "forest"}, prompt="forest sounds")
                
    assert res.startswith("data:audio/wav;base64,")
    assert "fake_audio_base64" in res

def test_generate_soundscape_failure(xtts_adapter):
    """Vérifie que la génération lève une InferenceError si scipy est manquant."""
    # Simuler l'absence de scipy enlevant la fonction de sauvegarde
    mock_pipe = MagicMock()
    mock_pipe.return_value = MagicMock(audios=[np.zeros((1, 16000))])
    mock_diffusers.AudioLDMPipeline.from_pretrained.return_value = mock_pipe

    with patch("scipy.io.wavfile.write", side_effect=ImportError("No scipy")):
        with pytest.raises(InferenceError) as excinfo:
            xtts_adapter.generate_soundscape({"scene": "forest"}, prompt="forest sounds")
        assert "Soundscape generation failed" in str(excinfo.value)

def test_vision_depth_estimation_mocked(vision_adapter):
    """Vérifie l'estimation de profondeur avec un pipeline mocké."""
    mock_pipeline = MagicMock()
    dummy_depth = Image.new('L', (10, 10), color=128)
    mock_pipeline.return_value = {"depth": dummy_depth}
    
    img = Image.new('RGB', (10, 10))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_image_data = buf.getvalue()
    
    with patch("adapters.inference.depth_estimation.pipeline", return_value=mock_pipeline):
        res = vision_adapter.estimate_depth(valid_image_data)
        
    assert isinstance(res, bytes)
    assert len(res) > 0

def test_vision_manga_ocr_mocked(vision_adapter):
    """Vérifie l'OCR manga avec un pipeline mocké."""
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = [{"generated_text": "Sugoi!"}]
    
    img = Image.new('RGB', (10, 10))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_image_data = buf.getvalue()
    
    with patch("adapters.inference.manga_ocr.pipeline", return_value=mock_pipeline):
        res = vision_adapter.process_manga_page(valid_image_data)
        
    assert res["status"] == "success"
    assert res["text"] == "Sugoi!"
    assert len(res["layout"]) > 0

def test_vision_3d_scene_mocked(vision_adapter):
    """Vérifie la structure de retour de la génération de scène 3D avec des images valides."""
    import io
    from PIL import Image as PILImage
    # Créer des images valides pour le test
    rgb_img = PILImage.new('RGB', (10, 10), color=(128, 64, 32))
    depth_img = PILImage.new('L', (10, 10), color=128)
    rgb_buf = io.BytesIO(); rgb_img.save(rgb_buf, format="PNG"); rgb_data = rgb_buf.getvalue()
    depth_buf = io.BytesIO(); depth_img.save(depth_buf, format="PNG"); depth_data = depth_buf.getvalue()
    
    res = vision_adapter.generate_3d_scene(rgb_data, depth_data)
    assert res["status"] == "success"
    assert "model_url" in res
    assert res["point_count"] > 0
    assert res["metadata"]["original_size"] == len(rgb_data)

def test_fallback_rerank_documents_chain():
    """Vérifie que FallbackInferenceAdapter essaie plusieurs adaptateurs pour le reranking."""
    mock_fail = MagicMock()
    mock_fail.rerank_documents.side_effect = Exception("Service Down")
    
    mock_success = MagicMock()
    mock_success.rerank_documents.return_value = [0.9, 0.1]
    
    fallback = FallbackInferenceAdapter(adapters=[mock_fail, mock_success])
    
    scores = fallback.rerank_documents("query", ["doc1", "doc2"])
    
    assert scores == [0.9, 0.1]
    assert mock_fail.rerank_documents.called
    assert mock_success.rerank_documents.called
