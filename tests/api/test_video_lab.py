from unittest.mock import MagicMock

import pytest
from animetix.api.labs import VideoFateZeroLabView, VideoLabDataView
from animetix.containers import get_container
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory


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


from django.contrib.auth.models import User  # noqa: E402
from rest_framework.test import force_authenticate  # noqa: E402


@pytest.mark.django_db
def test_video_fatezero_lab_view(dummy_video):
    factory = RequestFactory()
    user = User.objects.create_user(username="testuser")
    request = factory.post(
        "/api/v1/labs/video/fatezero/", {"video": dummy_video, "studio_style": "Ghibli"}
    )
    force_authenticate(request, user=user)

    mock_service = MagicMock()
    mock_service.transform_video_to_anime_sota.return_value = (
        "http://storage.com/result.mp4"
    )
    container = get_container()
    container.core.studio_transform_service.override(mock_service)
    try:
        view = VideoFateZeroLabView.as_view()
        response = view(request)
    finally:
        container.core.studio_transform_service.reset_last_overriding()

    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["video_url"] == "http://storage.com/result.mp4"
    mock_service.transform_video_to_anime_sota.assert_called_once_with(
        b"video_content", "Ghibli"
    )
