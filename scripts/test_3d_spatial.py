import unittest
from unittest.mock import MagicMock
from core.domain.services.spatial_computing_service import SpatialComputingService

class TestSpatial3DSmoke(unittest.TestCase):
    def setUp(self):
        self.mock_inference = MagicMock()
        self.service = SpatialComputingService(inference_engine=self.mock_inference)

    def test_reconstruct_3d_scene_success(self):
        # Setup mocks
        dummy_image = b"fake_image_data"
        self.mock_inference.estimate_depth.return_value = b"fake_depth_map"
        self.mock_inference.generate_3d_scene.return_value = {
            "status": "success",
            "model_url": "http://example.com/model.ply",
            "point_count": 50000,
            "in_painted": True
        }

        # Run
        result = self.service.reconstruct_3d_scene(dummy_image, title="Test Scene")

        # Verify
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["viewer_type"], "gaussian_splatting")
        self.assertEqual(result["model_url"], "http://example.com/model.ply")
        self.mock_inference.estimate_depth.assert_called_once()
        self.mock_inference.generate_3d_scene.assert_called_once_with(
            dummy_image, b"fake_depth_map", mode="gaussian_splatting"
        )

    def test_reconstruct_3d_scene_failure(self):
        # Setup mocks: depth estimation fails
        dummy_image = b"fake_image_data"
        self.mock_inference.estimate_depth.return_value = None

        # Run
        result = self.service.reconstruct_3d_scene(dummy_image, title="Fail Scene")

        # Verify
        self.assertEqual(result["status"], "error")
        self.assertIn("Failed to generate depth map", result["message"])

if __name__ == "__main__":
    unittest.main()
