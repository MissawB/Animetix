from unittest.mock import MagicMock, patch

import pytest
from adapters.inference.brain_api_adapter import BrainAPIAdapter
from adapters.inference.local_rerank_adapter import LocalRerankAdapter
from adapters.inference.local_text_adapter import LocalTextAdapter
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from core.domain.exceptions import ConfigurationError
from core.ports.inference_port import InferenceNotImplementedError


def test_qwen3_vl_not_implemented():
    adapter = Qwen3VLAdapter()
    assert adapter.calculate_visual_similarity("test", "1", "image") == 0.5


def test_brain_api_not_implemented(monkeypatch):
    # Clear the env fallback so the test is independent of the local environment.
    monkeypatch.delenv("BRAIN_API_URL", raising=False)
    with pytest.raises(ConfigurationError, match="Brain API URL not configured"):
        BrainAPIAdapter(api_url="", api_key="")


def test_transformers_not_implemented():
    adapter = LocalTextAdapter(model_id="fake/id")
    assert adapter.calculate_visual_similarity("test", "1", "image") == 0.5


def test_inference_not_implemented_error():
    adapter = Qwen3VLAdapter()

    # rerank_documents is defined on InferencePort and raises InferenceNotImplementedError by default
    with pytest.raises(InferenceNotImplementedError) as excinfo:
        adapter.rerank_documents("prompt", ["doc"])

    assert "rerank_documents not implemented for this adapter" in str(excinfo.value)


def test_transformers_rerank_documents():
    adapter = LocalRerankAdapter()
    with patch("adapters.inference.rerank_mixin.lazy_import") as mock_lazy:
        mock_st = MagicMock()
        mock_ce = MagicMock()
        mock_ce.predict.return_value = [0.9, 0.1]
        mock_st.CrossEncoder.return_value = mock_ce

        # mock lazy_import to return mock_st when called with 'sentence_transformers'
        def side_effect(name):
            if name == "sentence_transformers":
                return mock_st
            import importlib  # noqa: E402

            return importlib.import_module(name)

        mock_lazy.side_effect = side_effect

        result = adapter.rerank_documents("query", ["doc1", "doc2"])
        assert result == [0.9, 0.1]


def test_transformers_rerank_empty():
    adapter = LocalRerankAdapter()
    result = adapter.rerank_documents("query", [])
    assert result == []


def test_transformers_text_and_rerank_adapters_instantiation():
    text_adapter = LocalTextAdapter(model_id="fake/id")
    assert text_adapter.model_id == "fake/id"

    rerank_adapter = LocalRerankAdapter()
    assert rerank_adapter.model_name is not None


def test_inference_container_raises_on_missing_url(monkeypatch):
    import importlib

    from django.conf import settings

    # Simulate a non-test environment and remove BRAIN_API_URL
    monkeypatch.setattr(settings, "SETTINGS_MODULE", "animetix_project.settings")
    monkeypatch.delenv("BRAIN_API_URL", raising=False)

    with pytest.raises(ConfigurationError, match="BRAIN_API_URL is not configured"):
        importlib.reload(importlib.import_module("animetix.containers.inference"))


def test_inference_container_succeeds_when_url_present(monkeypatch):
    import importlib

    from django.conf import settings

    # Simulate a non-test environment and configure BRAIN_API_URL
    monkeypatch.setattr(settings, "SETTINGS_MODULE", "animetix_project.settings")
    monkeypatch.setenv("BRAIN_API_URL", "http://brain-api:7861")

    module = importlib.reload(importlib.import_module("animetix.containers.inference"))
    assert module.InferenceContainer is not None
