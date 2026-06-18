from unittest.mock import MagicMock

import pytest
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferencePort


@pytest.fixture
def mock_adapter_1():
    adapter = MagicMock(spec=InferencePort)
    adapter.health_check.return_value = {"status": "online"}
    return adapter


@pytest.fixture
def mock_adapter_2():
    adapter = MagicMock(spec=InferencePort)
    adapter.health_check.return_value = {"status": "offline"}
    return adapter


@pytest.fixture
def fallback_adapter(mock_adapter_1, mock_adapter_2):
    return FallbackInferenceAdapter(adapters=[mock_adapter_1, mock_adapter_2])


def test_generate_success_first(fallback_adapter, mock_adapter_1, mock_adapter_2):
    mock_adapter_1.generate.return_value = InferenceResponse(text="Result 1")
    response = fallback_adapter.generate("prompt")
    assert response.text == "Result 1"
    mock_adapter_1.generate.assert_called_once()
    mock_adapter_2.generate.assert_not_called()


def test_generate_fallback_success(fallback_adapter, mock_adapter_1, mock_adapter_2):
    mock_adapter_1.generate.side_effect = Exception("Fail 1")
    mock_adapter_2.generate.return_value = InferenceResponse(text="Result 2")
    response = fallback_adapter.generate("prompt")
    assert response.text == "Result 2"
    mock_adapter_1.generate.assert_called_once()
    mock_adapter_2.generate.assert_called_once()


def test_generate_all_fail(fallback_adapter, mock_adapter_1, mock_adapter_2):
    mock_adapter_1.generate.side_effect = Exception("Fail 1")
    mock_adapter_2.generate.side_effect = Exception("Fail 2")
    res = fallback_adapter.generate("prompt")
    assert "Tous les moteurs LLM ont échoué" in res.text
    assert "Fail 2" in res.text


def test_health_check(fallback_adapter):
    res = fallback_adapter.health_check()
    assert res["status"] == "online"
    assert len(res["adapters"]) == 2


def test_get_image_embedding_fallback(fallback_adapter, mock_adapter_1, mock_adapter_2):
    mock_adapter_1.get_image_embedding.side_effect = Exception()
    mock_adapter_2.get_image_embedding.return_value = [0.1, 0.2]
    assert fallback_adapter.get_image_embedding(b"data") == [0.1, 0.2]


def test_clone_voice_fallback(fallback_adapter, mock_adapter_1, mock_adapter_2):
    mock_adapter_1.clone_voice.return_value = None
    mock_adapter_2.clone_voice.return_value = b"audio"
    assert fallback_adapter.clone_voice("text", b"ref") == b"audio"


def test_rerank_documents_fallback(fallback_adapter, mock_adapter_1, mock_adapter_2):
    mock_adapter_1.rerank_documents.return_value = [0.9, 0.8]
    assert fallback_adapter.rerank_documents("query", ["doc1", "doc2"]) == [0.9, 0.8]


def test_rerank_documents_fallback_failure(
    fallback_adapter, mock_adapter_1, mock_adapter_2
):
    mock_adapter_1.rerank_documents.side_effect = Exception("Fail")
    assert fallback_adapter.rerank_documents("query", ["doc1", "doc2"]) == [0.0, 0.0]
