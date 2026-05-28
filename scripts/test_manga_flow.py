import unittest
from unittest.mock import MagicMock
from core.domain.services.creative.manga_flow import MangaFlowService

class TestMangaFlowSmoke(unittest.TestCase):
    def setUp(self):
        self.mock_inference = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_prompt = MagicMock()
        self.service = MangaFlowService(
            inference_engine=self.mock_inference,
            llm_service=self.mock_llm,
            prompt_manager=self.mock_prompt
        )

    def test_manga_flow_pipeline_success(self):
        # Setup mocks
        dummy_image = b"fake_image_data"
        self.mock_inference.process_manga_page.return_value = {
            "text": "Hello world",
            "layout": [
                {"text": "Hello", "bbox": [10, 10, 50, 30]},
                {"text": "world", "bbox": [60, 10, 100, 30]}
            ]
        }
        self.mock_prompt.get_prompt.return_value = ("prompt", "system")
        self.mock_llm.generate.return_value = "Bonjour"
        self.mock_inference.inpaint_text_bubbles.return_value = b"inpainted_image"

        # Run
        result = self.service.translate_manga_page(dummy_image, target_lang="French")

        # Verify
        self.assertEqual(result, b"inpainted_image")
        self.assertEqual(self.mock_inference.process_manga_page.call_count, 1)
        self.assertEqual(self.mock_llm.generate.call_count, 2) # Two bubbles
        self.mock_inference.inpaint_text_bubbles.assert_called_once()

    def test_manga_flow_fallback_no_layout(self):
        # Setup mocks: OCR returns text but no layout
        dummy_image = b"fake_image_data"
        self.mock_inference.process_manga_page.return_value = {
            "text": "Full page text",
            "layout": []
        }
        self.mock_prompt.get_prompt.return_value = ("prompt", "system")
        self.mock_llm.generate.return_value = "Texte complet traduit"
        self.mock_inference.inpaint_text_bubbles.return_value = b"fallback_inpainted"

        # Run
        result = self.service.translate_manga_page(dummy_image, target_lang="French")

        # Verify
        self.assertEqual(result, b"fallback_inpainted")
        self.mock_llm.generate.assert_called_once()
        
if __name__ == "__main__":
    unittest.main()
