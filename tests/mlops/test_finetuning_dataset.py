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

if __name__ == "__main__":
    unittest.main()
