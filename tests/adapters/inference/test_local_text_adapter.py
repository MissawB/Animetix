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

    @patch("sentence_transformers.SentenceTransformer")
    def test_get_text_embedding_load_failure_raises_inference_error(self, mock_cls):
        # Same error semantics as every other local model load: a broken
        # SentenceTransformer load surfaces as InferenceError, not a raw
        # RuntimeError leaking implementation details to callers.
        from core.domain.exceptions import InferenceError

        mock_cls.side_effect = RuntimeError("weights corrupted")
        with self.assertRaises(InferenceError):
            self.adapter.get_text_embedding("Hello")

    def test_health_check(self):
        # Initial state
        hc = self.adapter.health_check()
        self.assertEqual(hc["status"], "offline")

        # An embedding model says NOTHING about generate(): it is a different,
        # far smaller model. Letting it mark the adapter online is what made the
        # fallback router prefer it over the managed remote engine, then load a
        # multi-GB causal LM and OOM-kill the container (prod 503, 2026-07-12).
        self.adapter._embedding_model = MagicMock()
        hc = self.adapter.health_check()
        self.assertEqual(hc["status"], "offline")

        # Only the generation model makes this adapter routable.
        self.adapter.model = MagicMock()
        hc = self.adapter.health_check()
        self.assertEqual(hc["status"], "online")


if __name__ == "__main__":
    unittest.main()
