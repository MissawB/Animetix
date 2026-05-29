import unittest
from unittest.mock import MagicMock, patch
from adapters.inference.manga_ocr_adapter import MangaOCRAdapter

class TestMangaOCRAdapter(unittest.TestCase):
    def setUp(self):
        # Créer une sous-classe qui implémente la méthode abstraite pour le test
        class ConcreteMangaOCRAdapter(MangaOCRAdapter):
            def moderate_content(self, text, categories):
                return {"is_safe": True}
        
        # Mock du pipeline pour éviter le chargement réel du modèle
        with patch('adapters.inference.manga_ocr_adapter.pipeline'):
            self.adapter = ConcreteMangaOCRAdapter()
        self.adapter.ocr_pipeline = MagicMock()

    def test_process_manga_page_success(self):
        self.adapter.ocr_pipeline.return_value = [{'generated_text': 'test text'}]
        result = self.adapter.process_manga_page(b"fake_image_data")
        self.assertEqual(result['text'], 'test text')

    def test_process_manga_page_error(self):
        from core.domain.exceptions import InferenceError
        self.adapter.ocr_pipeline.side_effect = Exception("OCR error")
        with self.assertRaises(InferenceError):
            self.adapter.process_manga_page(b"bad_data")
