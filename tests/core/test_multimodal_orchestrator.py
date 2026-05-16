import unittest
from unittest.mock import MagicMock
from core.domain.services.multimodal_orchestrator import MultimodalOrchestrator

class TestMultimodalOrchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_adapter = MagicMock()
        self.orchestrator = MultimodalOrchestrator(self.mock_adapter)

    def test_analyze_video_content(self):
        self.mock_adapter.get_video_temporal_embeddings.return_value = [{"segment": 1}]
        self.mock_adapter.localize_video_actions.return_value = [{"action": "combat"}]
        
        result = self.orchestrator.analyze_video_content(b"fake_video", ["combat"])
        
        self.assertIn("embeddings", result)
        self.assertIn("actions", result)
        self.mock_adapter.get_video_temporal_embeddings.assert_called_once()

    def test_transform_to_anime_safe(self):
        self.mock_adapter.moderate_content.return_value = {"is_safe": True}
        self.mock_adapter.transform_image_to_anime.return_value = "anime_url"
        
        result = self.orchestrator.transform_to_anime(b"fake_img", "cyberpunk")
        
        self.assertEqual(result, "anime_url")
        self.mock_adapter.moderate_content.assert_called_once()
