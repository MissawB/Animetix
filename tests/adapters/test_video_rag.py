import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from adapters.inference.vision_transformers_adapter import (  # noqa: E402
    VisionTransformersAdapter,
)
from core.domain.services.rag.video_rag_service import (  # noqa: E402
    VideoRAGService,
)
from PIL import Image

# `video_rag_service` importe `imageio` paresseusement (dans une méthode), donc le
# mock n'est nécessaire que pendant les tests — injecté via monkeypatch (auto-restauré)
# plutôt qu'en écrasant `sys.modules` au niveau module (qui fuyait sur toute la suite).
mock_imageio = MagicMock()


@pytest.fixture(autouse=True)
def _mock_imageio(monkeypatch):
    monkeypatch.setitem(sys.modules, "imageio", mock_imageio)
    yield
    mock_imageio.reset_mock()


@pytest.fixture
def adapter():
    return VisionTransformersAdapter(use_4bit=False)


@pytest.fixture
def video_service(adapter):
    return VideoRAGService(inference_engine=adapter)


def test_frame_sampling_logic(adapter):
    """Vérifie que l'échantillonnage de frames extrait le bon nombre d'images."""
    # On mock imageio.get_reader directement via le mock pré-injecté
    mock_instance = MagicMock()
    mock_instance.get_meta_data.return_value = {"fps": 1, "duration": 10}
    # On yield des tableaux numpy (ce que fait imageio par défaut)
    mock_instance.__iter__.return_value = [
        np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(10)
    ]
    mock_imageio.get_reader.return_value = mock_instance

    with patch("builtins.open", MagicMock()):
        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            mock_tmp.return_value.__enter__.return_value.name = "fake_path"
            with patch("os.unlink", MagicMock()):
                frames = adapter._sample_video_frames(b"fake_video", max_frames=5)

    assert len(frames) == 5
    assert isinstance(frames[0], Image.Image)


@patch(
    "adapters.inference.video_analysis.VideoAnalysisMixin._load_video_vlm",
    MagicMock(),
)
def test_get_video_temporal_embeddings_mocked(adapter):
    """Vérifie le workflow de récit temporel avec mocks VLM."""
    adapter._video_processor = MagicMock()
    adapter._video_vlm = MagicMock()

    # Mock du processor
    adapter._video_processor.apply_chat_template.return_value = "prompt"
    adapter._video_processor.return_value.to.return_value = {}

    # Mock de la génération
    adapter._video_vlm.generate.return_value = [1, 2, 3]
    adapter._video_processor.batch_decode.return_value = [
        "Le héros utilise son Gear 5."
    ]

    with patch.object(
        adapter, "_sample_video_frames", return_value=[Image.new("RGB", (10, 10))]
    ):
        res = adapter.get_video_temporal_embeddings(b"data")

    assert len(res) == 1
    assert "Gear 5" in res[0]["summary"]


@patch(
    "adapters.inference.video_analysis.VideoAnalysisMixin._load_video_vlm",
    MagicMock(),
)
def test_video_rag_service_orchestration(video_service):
    """Vérifie que le service de domaine orchestre correctement l'analyse."""
    video_service.inference_engine.get_video_temporal_embeddings = MagicMock(
        return_value=[{"summary": "test"}]
    )
    video_service.inference_engine.localize_video_actions = MagicMock(
        return_value=[{"action": "combat", "start": 1}]
    )

    res = video_service.process_long_video(b"data")

    assert "narrative" in res
    assert "actions" in res
    assert res["narrative"][0]["summary"] == "test"
    assert res["actions"][0]["action"] == "combat"


def test_video_rag_indexing_and_search():
    from unittest.mock import MagicMock  # noqa: E402

    from core.domain.services.rag.video_rag_service import (  # noqa: E402
        VideoRAGService,
    )

    mock_engine = MagicMock()
    mock_repo = MagicMock()

    # Mock inference to return a summary with an embedding
    mock_engine.get_video_temporal_embeddings.return_value = [
        {"start": 0, "end": 10, "summary": "A battle scene", "embedding": [0.1, 0.2]}
    ]

    # Mock repo search to return the indexed segment
    mock_repo.search_media_items.return_value = [
        {
            "id": "vid1_0_0",
            "video_id": "vid1",
            "start": 0,
            "end": 10,
            "summary": "A battle scene",
        }
    ]
    # `video_temporal` holds data in this scenario -- the availability guard
    # must let the search through.
    mock_repo.get_collection_count.return_value = 3

    service = VideoRAGService(inference_engine=mock_engine, repository=mock_repo)

    # Test Indexing
    service.index_video("vid1", b"fake_video")
    mock_repo.upsert_items.assert_called_once()

    # Check that the ID passed to upsert_items has the sub-index
    args, kwargs = mock_repo.upsert_items.call_args
    # args[1] is the list of IDs
    assert args[1][0] == "vid1_0_0"

    # Test Searching
    results = service.search_video_segment("battle")
    assert len(results) == 1
    assert results[0]["video_id"] == "vid1"


# --------------------------------------------------------------------------- #
# Empty-index guard: `video_temporal`'s only writer is admin-gated and hidden
# from the UI, so for every ordinary user the collection is empty. Searching
# it must say so rather than silently return [].
# --------------------------------------------------------------------------- #
def test_video_rag_is_available_false_when_collection_empty():
    from unittest.mock import MagicMock  # noqa: E402

    from core.domain.services.rag.video_rag_service import (  # noqa: E402
        VideoRAGService,
    )

    mock_repo = MagicMock()
    mock_repo.get_collection_count.return_value = 0
    service = VideoRAGService(inference_engine=MagicMock(), repository=mock_repo)

    assert service.is_available() is False
    mock_repo.get_collection_count.assert_called_once_with("video_temporal")


def test_video_rag_is_available_false_without_repository():
    from unittest.mock import MagicMock  # noqa: E402

    from core.domain.services.rag.video_rag_service import (  # noqa: E402
        VideoRAGService,
    )

    service = VideoRAGService(inference_engine=MagicMock(), repository=None)
    assert service.is_available() is False


def test_video_rag_search_raises_when_collection_empty():
    from unittest.mock import MagicMock  # noqa: E402

    import pytest  # noqa: E402
    from core.domain.exceptions import SearchIndexUnavailableError  # noqa: E402
    from core.domain.services.rag.video_rag_service import (  # noqa: E402
        VideoRAGService,
    )

    mock_repo = MagicMock()
    mock_repo.get_collection_count.return_value = 0
    service = VideoRAGService(inference_engine=MagicMock(), repository=mock_repo)

    with pytest.raises(SearchIndexUnavailableError):
        service.search_video_segment("battle")

    mock_repo.search_media_items.assert_not_called()
