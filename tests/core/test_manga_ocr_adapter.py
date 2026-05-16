import unittest
from unittest.mock import MagicMock
from adapters.inference.manga_ocr_adapter import MangaOCRAdapter

class TestMangaOCRAdapter(unittest.TestCase):
    def setUp(self):
        # Mock du pipeline pour éviter le chargement réel du modèle
        self.adapter = MangaOCRAdapter()
        self.adapter.ocr_pipeline = MagicMock()

    def test_process_manga_page_success(self):
        self.adapter.ocr_pipeline.return_value = [{'generated_text': 'test text'}]
        result = self.adapter.process_manga_page(b"fake_image_data")
        self.assertEqual(result['text'], 'test text')

    def test_process_manga_page_error(self):
        self.adapter.ocr_pipeline.side_effect = Exception("OCR error")
        result = self.adapter.process_manga_page(b"bad_data")
        self.assertIn("error", result)
