import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.pipeline.mlops.finetuning_dataset import clean_description

class TestFinetuningDataset(unittest.TestCase):
    def test_clean_description(self):
        raw_text = "L'anime <i>SnK</i> est culte.<br> &quot;Incroyable&quot; &#039;chef-d'oeuvre&#039;  et   magnifique."
        expected = "L'anime SnK est culte. \"Incroyable\" 'chef-d'oeuvre' et magnifique."
        self.assertEqual(clean_description(raw_text), expected)

    def test_gemini_paraphrase_cache(self):
        from backend.pipeline.mlops.finetuning_dataset import paraphrase_text_via_gemini
        from unittest.mock import MagicMock
        
        # Initialiser un cache temporaire pour le test
        import backend.pipeline.mlops.finetuning_dataset as fd
        fd.PARAPHRASE_CACHE = {"Le texte original||naturel": "Texte paraphrase en cache"}
        
        # Mocker le client Gemini
        mock_client = MagicMock()
        
        # Premier appel : doit retourner la valeur du cache sans interroger le client
        res1 = paraphrase_text_via_gemini("Le texte original", mock_client, "naturel")
        self.assertEqual(res1, "Texte paraphrase en cache")
        mock_client.models.generate_content.assert_not_called()
        
        # Deuxième appel : clé manquante, doit interroger le client et alimenter le cache
        mock_response = MagicMock()
        mock_response.text = "Nouvelle paraphrase"
        mock_client.models.generate_content.return_value = mock_response
        
        res2 = paraphrase_text_via_gemini("Un autre texte", mock_client, "naturel")
        self.assertEqual(res2, "Nouvelle paraphrase")
        mock_client.models.generate_content.assert_called_once()
        self.assertIn("Un autre texte||naturel", fd.PARAPHRASE_CACHE)
        self.assertEqual(fd.PARAPHRASE_CACHE["Un autre texte||naturel"], "Nouvelle paraphrase")

if __name__ == "__main__":
    unittest.main()
