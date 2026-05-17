import pytest
from src.adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from src.adapters.inference.vllm_adapter import VllmAdapter
from src.adapters.inference.brain_api_adapter import BrainAPIAdapter
from src.adapters.inference.gguf_adapter import GgufAdapter
from src.adapters.inference.local_llama_adapter import LocalLlamaAdapter
from src.adapters.inference.manga_ocr_adapter import MangaOCRAdapter
from src.adapters.inference.transformers_adapter import TransformersAdapter

# Note: MangaOCRAdapter est abstrait dans les tests actuels, nous allons le mocker ou ignorer son instanciation directe si nécessaire.

def test_qwen3_vl_not_implemented():
    adapter = Qwen3VLAdapter()
    with pytest.raises(NotImplementedError):
        adapter.calculate_visual_similarity("test", "1", "image")

def test_vllm_not_implemented():
    adapter = VllmAdapter()
    with pytest.raises(NotImplementedError):
        adapter.calculate_visual_similarity("test", "1", "image")

def test_brain_api_not_implemented():
    # BrainAPIAdapter implémente calculate_visual_similarity, donc on teste une autre méthode
    adapter = BrainAPIAdapter(brain_api_url="")
    with pytest.raises(NotImplementedError):
        adapter.get_image_embedding(b"")

def test_gguf_not_implemented():
    adapter = GgufAdapter(model_path="fake/path")
    with pytest.raises(NotImplementedError):
        adapter.calculate_visual_similarity("test", "1", "image")

def test_local_llama_not_implemented():
    adapter = LocalLlamaAdapter(model_path="fake/path")
    with pytest.raises(NotImplementedError):
        adapter.calculate_visual_similarity("test", "1", "image")

def test_transformers_not_implemented():
    adapter = TransformersAdapter(model_id="fake/id")
    with pytest.raises(NotImplementedError):
        adapter.calculate_visual_similarity("test", "1", "image")
