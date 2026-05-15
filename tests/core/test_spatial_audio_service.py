import pytest
from unittest.mock import MagicMock
from core.domain.services.spatial_audio_service import VoiceCloningService, NativeSpeechLLMService

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def voice_service(mock_engine):
    return VoiceCloningService(inference_engine=mock_engine)

@pytest.fixture
def native_s2s_service(mock_engine):
    return NativeSpeechLLMService(inference_engine=mock_engine)

def test_generate_character_voice_success(voice_service, mock_engine):
    mock_engine.clone_voice.return_value = b"audio_data"
    res = voice_service.generate_character_voice("Hello", b"sample")
    assert res == b"audio_data"
    mock_engine.clone_voice.assert_called_once()

def test_generate_character_voice_failure(voice_service, mock_engine):
    mock_engine.clone_voice.return_value = b""
    assert voice_service.generate_character_voice("Hello", b"sample") == b""

def test_process_voice_interaction_success(native_s2s_service, mock_engine):
    mock_engine.speech_to_speech.return_value = b"response_audio"
    res = native_s2s_service.process_voice_interaction(b"input")
    assert res["status"] == "success"
    assert res["audio_data"] == b"response_audio"

def test_process_voice_interaction_failure(native_s2s_service, mock_engine):
    mock_engine.speech_to_speech.return_value = b""
    res = native_s2s_service.process_voice_interaction(b"input")
    assert res["status"] == "error"
