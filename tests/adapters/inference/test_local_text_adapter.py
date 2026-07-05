import unittest
from unittest.mock import MagicMock, patch

from adapters.inference.local_text_adapter import LocalTextAdapter


class TestLocalTextAdapter(unittest.TestCase):
    def setUp(self):
        self.usage_port = MagicMock()
        self.adapter = LocalTextAdapter(usage_port=self.usage_port)

    @patch("sentence_transformers.SentenceTransformer")
    def test_get_text_embedding_lazy_loading(self, mock_transformer_cls):
        # Mock the model instance
        mock_model = MagicMock()
        mock_transformer_cls.return_value = mock_model
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])

        # First call should load the model
        text = "Hello world"
        embedding = self.adapter.get_text_embedding(text)

        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        mock_transformer_cls.assert_called_once_with("all-MiniLM-L6-v2")
        mock_model.encode.assert_called_once_with(text)
        self.usage_port.log_usage.assert_called_once_with(
            "local:all-MiniLM-L6-v2", 0, 0, 1, allocated_budget=0
        )

        # Second call should NOT load the model again
        self.adapter.get_text_embedding("Another text")
        self.assertEqual(mock_transformer_cls.call_count, 1)

    def test_health_check(self):
        # Initial state
        hc = self.adapter.health_check()
        self.assertEqual(hc["status"], "offline")

        # After "loading" embedding model (manually setting it to avoid heavy mock)
        self.adapter._embedding_model = MagicMock()
        hc = self.adapter.health_check()
        self.assertEqual(hc["status"], "online")


if __name__ == "__main__":
    unittest.main()
