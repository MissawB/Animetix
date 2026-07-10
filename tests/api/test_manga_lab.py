import base64
from unittest.mock import MagicMock, patch

import pytest
from animetix.api.labs import MangaCleanLabView, MangaTranslateLabView
from animetix.containers import get_container
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from rest_framework.test import force_authenticate


@pytest.fixture
def dummy_image():
    return SimpleUploadedFile(
        "test_manga.png", b"file_content", content_type="image/png"
    )


@pytest.mark.django_db
def test_manga_clean_lab_view(dummy_image):
    factory = RequestFactory()
    user = User.objects.create_user(username="testuser")
    request = factory.post("/api/v1/manga-lab/clean/", {"image": dummy_image})
    force_authenticate(request, user=user)

    mock_primary = MagicMock()
    # Mock returns bytes
    mock_primary.inpaint_text_bubbles.return_value = b"cleaned_image_bytes"
    # The view gets the engine injected from Container.inference.inference_engine.
    container = get_container()
    container.inference.inference_engine.override(mock_primary)
    try:
        with patch("animetix.api.labs.manga.deduct_berrix"):
            view = MangaCleanLabView.as_view()
            response = view(request)
    finally:
        container.inference.inference_engine.reset_last_overriding()

    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["image"] == base64.b64encode(b"cleaned_image_bytes").decode(
        "utf-8"
    )
    mock_primary.inpaint_text_bubbles.assert_called_once_with(b"file_content", [])


@pytest.mark.django_db
def test_manga_translate_lab_view(dummy_image):
    factory = RequestFactory()
    user = User.objects.create_user(username="testuser2")
    request = factory.post(
        "/api/v1/manga-lab/translate/", {"image": dummy_image, "target_lang": "English"}
    )
    force_authenticate(request, user=user)

    mock_service = MagicMock()
    mock_service.translate_manga_page.return_value = b"translated_image_bytes"
    container = get_container()
    container.core.manga_flow_service.override(mock_service)
    try:
        view = MangaTranslateLabView.as_view()
        response = view(request)
    finally:
        container.core.manga_flow_service.reset_last_overriding()

    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["image"] == base64.b64encode(b"translated_image_bytes").decode(
        "utf-8"
    )
    mock_service.translate_manga_page.assert_called_once_with(
        b"file_content", "English"
    )
