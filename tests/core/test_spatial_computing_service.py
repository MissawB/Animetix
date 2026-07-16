import pytest
from core.domain.services.spatial_computing_service import SpatialComputingService


@pytest.fixture
def spatial_service(mock_engine):
    return SpatialComputingService(inference_engine=mock_engine)


def test_reconstruct_3d_scene_success(spatial_service, mock_engine):
    mock_engine.estimate_depth.return_value = b"depth_map"
    mock_engine.generate_3d_scene.return_value = {
        "status": "success",
        "model_url": "data:application/octet-stream;base64,fake_data",
        "point_count": 1000,
    }

    res = spatial_service.reconstruct_3d_scene(b"img", "Naruto")
    assert res["status"] == "success"
    assert "data:application/octet-stream;base64," in res["model_url"]
    assert res["metadata"]["navigable"] is True


def test_reconstruct_3d_scene_depth_fail(spatial_service, mock_engine):
    mock_engine.estimate_depth.return_value = b""
    res = spatial_service.reconstruct_3d_scene(b"img", "Title")
    assert res["status"] == "error"
    assert "depth" in res["message"].lower()


def test_reconstruct_3d_scene_generation_fail(spatial_service, mock_engine):
    mock_engine.estimate_depth.return_value = b""
    res = spatial_service.reconstruct_3d_scene(b"img", "Title")
    assert res["status"] == "error"
