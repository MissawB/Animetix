import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.pipeline.mlops.train_expert_model import format_chatml_messages

class TestTrainExpertModel(unittest.TestCase):
    def test_format_chatml_messages_french(self):
        item = {
            "instruction": "Qui est Luffy ?",
            "input": "One Piece",
            "output": "Luffy est le capitaine...",
            "language": "Français"
        }
        messages = format_chatml_messages(item)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Tu es Animetix, un expert absolu", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Qui est Luffy ?\n\nContexte : One Piece")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[2]["content"], "Luffy est le capitaine...")

    def test_format_chatml_messages_english(self):
        item = {
            "instruction": "Who is Luffy?",
            "input": "One Piece",
            "output": "Luffy is the captain...",
            "language": "English"
        }
        messages = format_chatml_messages(item)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("You are Animetix, an absolute expert", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Who is Luffy?\n\nContext: One Piece")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[2]["content"], "Luffy is the captain...")

    def test_format_chatml_messages_default_french(self):
        item = {
            "instruction": "Qui est Luffy ?",
            "input": "",
            "output": "Luffy est le capitaine..."
        }
        messages = format_chatml_messages(item)
        self.assertIn("Tu es Animetix, un expert absolu", messages[0]["content"])
        self.assertEqual(messages[1]["content"], "Qui est Luffy ?")

if __name__ == "__main__":
    unittest.main()
