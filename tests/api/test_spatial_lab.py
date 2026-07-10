from unittest.mock import MagicMock, patch

import pytest
from animetix.api.labs import (
    CinematicReconstructionView,
    Generate3DDataView,
    SpatialLabDataView,
)
from animetix.containers import get_container
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory


@pytest.fixture
def dummy_image():
    return SimpleUploadedFile("poster.png", b"image_content", content_type="image/png")


@pytest.fixture
def dummy_video():
    return SimpleUploadedFile("clip.mp4", b"video_content", content_type="video/mp4")


def test_spatial_lab_data_view():
    factory = RequestFactory()
    request = factory.get("/api/v1/labs/spatial/")
    view = SpatialLabDataView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert any(tool["id"] == "generate-3d" for tool in response.data["tools"])


def test_generate_3d_data_view(dummy_image):
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/labs/spatial/generate-3d/",
        {"image": dummy_image, "title": "Test Scene"},
    )

    mock_service = MagicMock()
    mock_service.reconstruct_3d_scene.return_value = {
        "status": "success",
        "model_url": "http://storage.com/model.ply",
        "viewer_type": "gaussian_splatting",
    }
    container = get_container()
    container.core.spatial_computing_service.override(mock_service)
    try:
        with patch("animetix.api.labs.spatial.deduct_berrix"):
            view = Generate3DDataView.as_view(permission_classes=[])
            response = view(request)
    finally:
        container.core.spatial_computing_service.reset_last_overriding()
    assert response.status_code == 200
    assert response.data["model_url"] == "http://storage.com/model.ply"


def test_cinematic_reconstruction_view(dummy_video):
    factory = RequestFactory()
    request = factory.post("/api/v1/labs/spatial/cinematic/", {"video": dummy_video})

    mock_service = MagicMock()
    mock_service.reconstruct_dynamic_cinematic_scene.return_value = {
        "status": "success",
        "frames": [{"timestamp": 0, "model_url": "url"}],
    }
    container = get_container()
    container.core.cinematic_volumetric_reconstruction_service.override(mock_service)
    try:
        with patch("animetix.api.labs.spatial.deduct_berrix"):
            view = CinematicReconstructionView.as_view(permission_classes=[])
            response = view(request)
    finally:
        container.core.cinematic_volumetric_reconstruction_service.reset_last_overriding()
    assert response.status_code == 200
    assert len(response.data["frames"]) > 0
