import pytest
from unittest.mock import MagicMock
from core.domain.services.creative.fusion_service import FusionDomainService
from core.domain.services.creative.manga_flow import MangaFlowService
from core.domain.services.creative.soundscape import SoundscapeGenerationService


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("formatted prompt", "system prompt")
    return pm


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def mock_video_service():
    return MagicMock()


def test_fusion_service_uses_prompt_manager(mock_engine, mock_prompt_manager):
    service = FusionDomainService(
        inference_engine=mock_engine, prompt_manager=mock_prompt_manager
    )

    item_a = {"title": "Naruto"}
    item_b = {"title": "One Piece"}

    service.generate_fusion_image(item_a, item_b, art_style="Ukiyo-e")

    mock_prompt_manager.get_prompt.assert_called_once_with(
        "fusion_image", title_a="Naruto", title_b="One Piece", art_style="Ukiyo-e"
    )


def test_manga_flow_uses_prompt_manager(
    mock_engine, mock_llm_service, mock_prompt_manager
):
    service = MangaFlowService(
        inference_engine=mock_engine,
        llm_service=mock_llm_service,
        prompt_manager=mock_prompt_manager,
    )

    mock_engine.process_manga_page.return_value = {
        "layout": [{"text": "Original text", "bbox": [0, 0, 10, 10]}]
    }

    service.translate_manga_page(b"fake_image_data", target_lang="English")

    mock_prompt_manager.get_prompt.assert_called_once_with(
        "manga_translation", target_lang="English", original_text="Original text"
    )


def test_soundscape_uses_prompt_manager(
    mock_engine, mock_video_service, mock_prompt_manager
):
    service = SoundscapeGenerationService(
        inference_engine=mock_engine,
        video_service=mock_video_service,
        prompt_manager=mock_prompt_manager,
    )

    mock_engine.localize_video_actions.return_value = ["action1"]
    mock_engine.generate_image_description.return_value = "Scene description"

    service.generate_soundscape_for_video(b"fake_video_data")

    mock_prompt_manager.get_prompt.assert_called_once_with(
        "soundscape_generation", scene="Scene description", actions="['action1']"
    )
