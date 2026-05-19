import pytest
from unittest.mock import MagicMock
from core.domain.services.creative import (
    VideoQuestService, StudioTransformService, SoundscapeGenerationService, MangaFlowService
)

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("formatted prompt", "system prompt")
    return pm

@pytest.fixture
def video_service(mock_engine):
    return VideoQuestService(inference_engine=mock_engine)

@pytest.fixture
def studio_service(mock_engine):
    return StudioTransformService(inference_engine=mock_engine)

@pytest.fixture
def soundscape_service(mock_engine, video_service, mock_prompt_manager):
    return SoundscapeGenerationService(
        inference_engine=mock_engine, 
        video_service=video_service,
        prompt_manager=mock_prompt_manager
    )

@pytest.fixture
def manga_service(mock_engine, mock_prompt_manager):
    return MangaFlowService(
        inference_engine=mock_engine, 
        llm_service=MagicMock(),
        prompt_manager=mock_prompt_manager
    )

def test_index_video_clips(video_service, mock_engine):
    mock_engine.get_video_temporal_embeddings.return_value = [{"start": 0, "end": 10}]
    assert video_service.index_video_clips(b"data") == [{"start": 0, "end": 10}]

def test_find_action_boundaries(video_service, mock_engine):
    mock_engine.localize_video_actions.return_value = [{"action": "jump", "start": 5, "end": 6}]
    res = video_service.find_action_boundaries(b"data", ["jump"])
    assert res[0]["action"] == "jump"

def test_identify_episode_from_clip(video_service, mock_engine):
    mock_engine.localize_video_actions.return_value = [{"answer": "Episode 5: The First Duel", "confidence": 0.95}]
    result = video_service.identify_episode_from_clip(b"video_data", "Naruto")
    assert result == "Episode 5: The First Duel"
    mock_engine.localize_video_actions.assert_called_once()

def test_studio_transform(studio_service, mock_engine):
    mock_engine.transform_image_to_anime.return_value = "img_url"
    assert studio_service.transform_user_to_anime(b"data", "Ghibli") == "img_url"

def test_studio_transform_video(studio_service, mock_engine):
    mock_engine.transform_video_to_anime.return_value = "vid_url"
    assert studio_service.transform_video_to_anime_sota(b"data", "Ufotable") == "vid_url"

def test_soundscape_generation(soundscape_service, mock_engine):
    mock_engine.generate_soundscape.return_value = "audio_url"
    assert soundscape_service.generate_soundscape_for_video(b"data") == "audio_url"

def test_translate_manga_page(manga_service, mock_engine):
    mock_engine.process_manga_page.return_value = {
        'text': 'Hello', 'layout': []
    }
    manga_service.llm_service.generate.return_value = "Salut"
    mock_engine.inpaint_text_bubbles.return_value = "new_img_url"
    
    assert manga_service.translate_manga_page(b"data") == "new_img_url"
