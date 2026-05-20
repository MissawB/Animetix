import pytest
import io
from unittest.mock import MagicMock, patch
from adapters.inference.transformers_adapter import TransformersAdapter
from core.domain.services.rag.video_rag_service import VideoRAGService
from PIL import Image

@pytest.fixture
def adapter():
    return TransformersAdapter(use_4bit=False)

@pytest.fixture
def video_service(adapter):
    return VideoRAGService(inference_engine=adapter)

def test_frame_sampling_logic(adapter):
    """Vérifie que l'échantillonnage de frames extrait le bon nombre d'images."""
    # On mock imageio.get_reader pour simuler une vidéo
    with patch("imageio.get_reader") as mock_reader:
        mock_instance = MagicMock()
        mock_instance.get_meta_data.return_value = {"fps": 1, "duration": 10}
        mock_instance.__iter__.return_value = [Image.new('RGB', (10, 10)) for _ in range(10)]
        mock_reader.return_value = mock_instance
        
        frames = adapter._sample_video_frames(b"fake_video", max_frames=5)
        
        assert len(frames) == 5
        assert isinstance(frames[0], Image.Image)

@patch("adapters.inference.transformers_adapter.TransformersAdapter._load_video_vlm", MagicMock())
def test_get_video_temporal_embeddings_mocked(adapter):
    """Vérifie le workflow de récit temporel avec mocks VLM."""
    adapter._video_processor = MagicMock()
    adapter._video_vlm = MagicMock()
    
    # Mock du processor
    adapter._video_processor.apply_chat_template.return_value = "prompt"
    adapter._video_processor.return_value.to.return_value = {}
    
    # Mock de la génération
    adapter._video_vlm.generate.return_value = [1, 2, 3]
    adapter._video_processor.batch_decode.return_value = ["Le héros utilise son Gear 5."]
    
    with patch.object(adapter, "_sample_video_frames", return_value=[Image.new('RGB', (10,10))]):
        res = adapter.get_video_temporal_embeddings(b"data")
        
    assert len(res) == 1
    assert "Gear 5" in res[0]["summary"]

@patch("adapters.inference.transformers_adapter.TransformersAdapter._load_video_vlm", MagicMock())
def test_video_rag_service_orchestration(video_service):
    """Vérifie que le service de domaine orchestre correctement l'analyse."""
    video_service.inference_engine.get_video_temporal_embeddings = MagicMock(return_value=[{"summary": "test"}])
    video_service.inference_engine.localize_video_actions = MagicMock(return_value=[{"action": "combat", "start": 1}])
    
    res = video_service.process_long_video(b"data")
    
    assert "narrative" in res
    assert "actions" in res
    assert res["narrative"][0]["summary"] == "test"
    assert res["actions"][0]["action"] == "combat"
