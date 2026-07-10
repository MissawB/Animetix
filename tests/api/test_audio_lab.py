import base64
from unittest.mock import MagicMock, patch

import pytest
from animetix.api.labs import (
    AudioLabDataView,
    SoundscapeGenerationView,
    SpeechToSpeechLabView,
)
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory


@pytest.fixture
def dummy_video():
    return SimpleUploadedFile("clip.mp4", b"video_content", content_type="video/mp4")


@pytest.fixture
def dummy_audio():
    return SimpleUploadedFile("input.wav", b"audio_content", content_type="audio/wav")


def test_audio_lab_data_view():
    factory = RequestFactory()
    request = factory.get("/api/v1/labs/audio/")
    view = AudioLabDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert any(tool["id"] == "soundscape" for tool in response.data["tools"])
    assert any(tool["id"] == "s2s" for tool in response.data["tools"])


def test_soundscape_generation_view(dummy_video):
    factory = RequestFactory()
    request = factory.post("/api/v1/labs/audio/soundscape/", {"video": dummy_video})

    with (
        patch("animetix.api.labs.audio.get_container") as mock_get_container,
        patch("animetix.api.labs.audio.deduct_berrix"),
    ):
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.generate_soundscape_for_video.return_value = (
            "http://storage.com/ambient.wav"
        )
        mock_container.core.soundscape_service.return_value = mock_service
        mock_get_container.return_value = mock_container

        # Bypass permissions for testing
        view = SoundscapeGenerationView.as_view(permission_classes=[])
        response = view(request)
        assert response.status_code == 200
        assert response.data["audio_url"] == "http://storage.com/ambient.wav"


def test_speech_to_speech_lab_view(dummy_audio):
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/labs/audio/s2s/", {"audio": dummy_audio, "persona": "Saber"}
    )

    with (
        patch("animetix.api.labs.audio.get_container") as mock_get_container,
        patch("animetix.api.labs.audio.deduct_berrix"),
    ):
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.process_voice_interaction.return_value = {
            "status": "success",
            "audio_data": b"voice_output_bytes",
        }
        mock_container.core.native_speech_llm_service.return_value = mock_service
        mock_get_container.return_value = mock_container

        # Bypass permissions for testing
        view = SpeechToSpeechLabView.as_view(permission_classes=[])
        response = view(request)
        assert response.status_code == 200
        assert response.data["audio_data"] == base64.b64encode(
            b"voice_output_bytes"
        ).decode("utf-8")
