from unittest.mock import MagicMock, patch

import pytest
from animetix.models import VoiceProfile
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_voice_profile_indexing_and_seiyuu_discovery():
    # Create test voice profiles
    VoiceProfile.objects.create(
        name="Rie Takahashi",
        language="japanese",
        origin="dataset",
        definition="Voix legendaire de Megumin",
        roles="Megumin, Emilia",
        impact="SOTA",
        origin_detail="http://fakeurl.com/megumin.wav",
    )
    VoiceProfile.objects.create(
        name="Donald Reignoux",
        language="french",
        origin="youtube",
        definition="Voix francaise de Spider-Man",
        roles="Spider-Man, Sora",
        impact="High",
        origin_detail="https://youtube.com/watch?v=123",
    )

    client = APIClient()

    # Test discovery without query (lists all)
    url = reverse("api_audio_seiyuu")
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) == 2

    # Test filtering by query
    response = client.get(f"{url}?q=Megumin")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Rie Takahashi"

    # Test filtering by language
    response = client.get(f"{url}?language=french")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Donald Reignoux"

    # Test filtering by origin
    response = client.get(f"{url}?origin=dataset")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Rie Takahashi"


@pytest.mark.django_db
def test_voice_profile_sample_url_lazy_loading():
    profile = VoiceProfile.objects.create(
        name="Luffy",
        language="japanese",
        origin="dataset",
        origin_detail="https://huggingface.co/datasets/taresh18/AnimeVox/resolve/main/audio/luffy_sample.wav",
    )

    assert not profile.sample_file

    # Mock safe_http_request to return a dummy file content
    with patch("core.utils.security.safe_http_request") as mock_safe_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake wav data content"
        mock_safe_request.return_value = mock_response

        url = profile.sample_url
        assert url.startswith("/media/audio/samples/luffy_sample")
        assert profile.sample_file.read() == b"fake wav data content"


@pytest.mark.django_db
def test_voice_profile_ingest_endpoint():
    user = User.objects.create_user(username="testuser", password="password")
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("api_audio_seiyuu_ingest")

    # Mock the yt-dlp, pydub, and file system calls
    with (
        patch("yt_dlp.YoutubeDL") as mock_yt,
        patch("pydub.AudioSegment.from_file") as mock_audio_segment,
        patch("pydub.silence.detect_leading_silence", return_value=0),
        patch("animetix.api.labs.audio.deduct_berrix"),
        patch("os.path.exists", return_value=True),
    ):
        # Setup mock for yt-dlp
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {
            "id": "abc123video",
            "webpage_url": "https://www.youtube.com/watch?v=abc123video",
        }
        mock_yt.return_value.__enter__.return_value = mock_ydl_instance

        # Setup mock for pydub AudioSegment
        mock_segment_instance = MagicMock()
        mock_segment_instance.__len__.return_value = 15000  # 15 seconds
        mock_segment_instance.high_pass_filter.return_value = mock_segment_instance
        mock_segment_instance.low_pass_filter.return_value = mock_segment_instance

        # Mock slice syntax [start_trim:start_trim + duration_ms]
        mock_segment_instance.__getitem__.return_value = mock_segment_instance

        mock_audio_segment.return_value = mock_segment_instance

        # Payload
        payload = {
            "name": "Eren Yeager",
            "language": "japanese",
            "query": "Eren Yeager shouting",
            "definition": "Protagoniste de SNK",
            "roles": "Eren Yeager, Attack Titan",
        }

        response = client.post(url, payload, format="json")
        assert response.status_code == 201
        assert response.data["message"] == "Ingestion réussie !"
        assert response.data["profile"]["name"] == "Eren Yeager"

        # Verify db persistence
        db_profile = VoiceProfile.objects.get(name="Eren Yeager")
        assert db_profile.language == "japanese"
        assert db_profile.origin == "youtube"
        assert db_profile.origin_detail == "https://www.youtube.com/watch?v=abc123video"
