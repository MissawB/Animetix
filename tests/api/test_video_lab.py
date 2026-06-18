import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from animetix.api.labs import VideoFateZeroLabView, VideoLabDataView
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def dummy_video():
    return SimpleUploadedFile(
        "test_video.mp4", b"video_content", content_type="video/mp4"
    )


def test_video_lab_data_view():
    factory = RequestFactory()
    request = factory.get("/api/v1/labs/video/")
    view = VideoLabDataView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert response.data["status"] == "active"
    assert any(tool["id"] == "fatezero" for tool in response.data["tools"])


from rest_framework.test import force_authenticate  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402


@pytest.mark.django_db
def test_video_fatezero_lab_view(dummy_video):
    factory = RequestFactory()
    user = User.objects.create_user(username="testuser")
    request = factory.post(
        "/api/v1/labs/video/fatezero/", {"video": dummy_video, "studio_style": "Ghibli"}
    )
    force_authenticate(request, user=user)

    with patch("animetix.api.labs.get_container") as mock_get_container:
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.transform_video_to_anime_sota.return_value = (
            "http://storage.com/result.mp4"
        )
        mock_container.core.studio_transform_service.return_value = mock_service
        mock_get_container.return_value = mock_container

        view = VideoFateZeroLabView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["video_url"] == "http://storage.com/result.mp4"
        mock_service.transform_video_to_anime_sota.assert_called_once_with(
            b"video_content", "Ghibli"
        )
