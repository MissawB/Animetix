import pytest
from unittest.mock import MagicMock
from core.domain.services.advanced_vision_service import AdvancedVisionService


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def vision_service(mock_engine):
    return AdvancedVisionService(inference_engine=mock_engine)


def test_get_unified_embedding_image(vision_service, mock_engine):
    mock_engine.get_image_embedding.return_value = [0.1, 0.2]
    emb = vision_service.get_unified_embedding(b"data", is_image=True)
    assert emb == [0.1, 0.2]
    mock_engine.get_image_embedding.assert_called_with(
        b"data", model_id=vision_service.clip_anime_model
    )


def test_get_unified_embedding_text(vision_service):
    assert vision_service.get_unified_embedding(b"text", is_image=False) == []


def test_detect_visual_attributes(vision_service, mock_engine):
    mock_engine.detect_objects.return_value = [
        {"label": "katana", "score": 0.9},
        {"label": "dragon", "score": 0.3},
    ]
    tags = vision_service.detect_visual_attributes(b"img")
    assert tags == ["katana"]


def test_identify_artist_style(vision_service, mock_engine):
    mock_engine.classify_image.return_value = {"Studio Ghibli": 0.8, "Wit Studio": 0.2}
    style = vision_service.identify_artist_style(b"img")
    assert style == "Studio Ghibli"


def test_calculate_visual_resemblance(vision_service, mock_engine):
    mock_engine.get_image_embedding.side_effect = [[1.0, 0.0], [1.0, 0.0]]
    res = vision_service.calculate_visual_resemblance(b"a", b"b")
    assert res == pytest.approx(1.0)


def test_calculate_visual_resemblance_no_emb(vision_service, mock_engine):
    mock_engine.get_image_embedding.return_value = []
    assert vision_service.calculate_visual_resemblance(b"a", b"b") == 0.0
