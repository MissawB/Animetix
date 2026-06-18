import pytest
from unittest.mock import MagicMock
from core.domain.services.vision_quest_service import VisionQuestDomainService


@pytest.fixture
def mock_inference_engine():
    return MagicMock()


@pytest.fixture
def mock_vision_service():
    return MagicMock()


@pytest.fixture
def vision_quest_service(mock_inference_engine, mock_vision_service):
    return VisionQuestDomainService(
        inference_engine=mock_inference_engine, vision_service=mock_vision_service
    )


def test_select_secret(vision_quest_service):
    catalog = {
        "db": [
            {"id": "1", "title": "Anime 1", "image": "img1.png"},
            {"id": "2", "title": "Anime 2"},  # No image
            {"id": "3", "title": "Anime 3", "image": "img3.png"},
        ]
    }
    secret = vision_quest_service.select_secret(catalog)
    assert secret is not None
    assert secret["image"] is not None
    assert secret["id"] in ["1", "3"]


def test_select_secret_no_images(vision_quest_service):
    catalog = {"db": [{"id": "2", "title": "Anime 2"}]}
    assert vision_quest_service.select_secret(catalog) is None


def test_get_image_style_info(vision_quest_service, mock_vision_service):
    mock_vision_service.identify_artist_style.return_value = "Studio Ghibli"
    style = vision_quest_service.get_image_style_info(b"fake_image_data")
    assert style == "Studio Ghibli"
    mock_vision_service.identify_artist_style.assert_called_once_with(
        b"fake_image_data"
    )


def test_calculate_score(vision_quest_service, mock_inference_engine):
    mock_inference_engine.calculate_visual_similarity.return_value = 80.0
    score = vision_quest_service.calculate_score("desc", "id1", "My Secret", "Anime")
    assert score == 80.0

    # Test bonus
    mock_inference_engine.calculate_visual_similarity.return_value = 90.0
    score = vision_quest_service.calculate_score(
        "This is My Secret", "id1", "My Secret", "Anime"
    )
    assert score == 100.0


def test_check_victory(vision_quest_service):
    assert vision_quest_service.check_victory(95.0) is True
    assert vision_quest_service.check_victory(94.9) is False
