from unittest.mock import MagicMock, patch

import numpy as np
from core.domain.services.cinematic_volumetric_reconstruction_service import (
    CinematicVolumetricReconstructionService,
)


def test_reconstruct_dynamic_cinematic_scene():
    mock_engine = MagicMock()
    # Mock depth map return (bytes)
    mock_engine.estimate_depth.return_value = b"fake_depth"
    # Mock ply return
    mock_engine.generate_3d_scene.return_value = {
        "status": "success",
        "model_url": "data:...",
    }

    # Mock video temporal embeddings
    mock_engine.get_video_temporal_embeddings.return_value = [{"start": 0, "end": 1}]

    service = CinematicVolumetricReconstructionService(inference_engine=mock_engine)

    # Mock imageio.get_reader
    mock_reader = MagicMock()
    mock_reader.__iter__.return_value = [np.zeros((100, 100, 3), dtype=np.uint8)] * 10
    mock_reader.get_meta_data.return_value = {"fps": 24}

    with patch("imageio.get_reader", return_value=mock_reader):
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "fake_path"
            with patch("os.unlink", MagicMock()):
                res = service.reconstruct_dynamic_cinematic_scene(
                    b"fake_video", "Naruto Fight"
                )

    assert res["status"] == "success"
    assert res["viewer_type"] == "dynamic_cinematic_splatting"
    assert len(res["frames"]) > 0
    assert "model_url" in res["frames"][0]
