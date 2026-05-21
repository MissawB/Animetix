import pytest
from src.adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from src.adapters.inference.vllm_adapter import VllmAdapter
from src.adapters.inference.brain_api_adapter import BrainAPIAdapter
from src.adapters.inference.gguf_adapter import GgufAdapter
from src.adapters.inference.local_llama_adapter import LocalLlamaAdapter
from src.adapters.inference.manga_ocr_adapter import MangaOCRAdapter
from src.adapters.inference.transformers_adapter import TransformersAdapter

def test_qwen3_vl_not_implemented():
    adapter = Qwen3VLAdapter()
    result = adapter.calculate_visual_similarity("test", "1", "image")
    assert result == 0.0

def test_vllm_not_implemented():
    adapter = VllmAdapter()
    result = adapter.calculate_visual_similarity("test", "1", "image")
    assert result == 0.0

def test_brain_api_not_implemented():
    # BrainAPIAdapter return default list when no brain_api_url is provided
    adapter = BrainAPIAdapter(brain_api_url="")
    result = adapter.get_image_embedding(b"")
    assert result == []

def test_gguf_not_implemented():
    adapter = GgufAdapter(model_path="fake/path")
    result = adapter.calculate_visual_similarity("test", "1", "image")
    assert result == 0.0

def test_local_llama_not_implemented():
    adapter = LocalLlamaAdapter(model_path="fake/path")
    result = adapter.calculate_visual_similarity("test", "1", "image")
    assert result == 0.0

def test_transformers_not_implemented():
    adapter = TransformersAdapter(model_id="fake/id")
    result = adapter.calculate_visual_similarity("test", "1", "image")
    assert isinstance(result, float)

def test_inference_not_implemented_error():
    from core.ports.inference_port import InferenceNotImplementedError
    adapter = Qwen3VLAdapter()
    
    # generate_structured is defined on InferencePort and raises InferenceNotImplementedError
    with pytest.raises(InferenceNotImplementedError) as excinfo:
        adapter.generate_structured("prompt", response_model=dict)
        
    assert "generate_structured not implemented for this adapter" in str(excinfo.value)

def test_transformers_rerank_documents():
    adapter = TransformersAdapter(model_id="fake/id")
    from unittest.mock import patch, MagicMock
    with patch('core.utils.lazy_import.lazy_import') as mock_lazy:
        mock_st = MagicMock()
        mock_ce = MagicMock()
        mock_ce.predict.return_value = [0.9, 0.1]
        mock_st.CrossEncoder.return_value = mock_ce
        
        # mock lazy_import to return mock_st when called with 'sentence_transformers'
        def side_effect(name):
            if name == 'sentence_transformers':
                return mock_st
            import importlib
            return importlib.import_module(name)
        mock_lazy.side_effect = side_effect
        
        result = adapter.rerank_documents("query", ["doc1", "doc2"])
        assert result == [0.9, 0.1]
        
def test_transformers_rerank_empty():
    adapter = TransformersAdapter(model_id="fake/id")
    result = adapter.rerank_documents("query", [])
    assert result == []

