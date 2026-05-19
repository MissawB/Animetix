import sys
import os
import logging

# Mock logging to avoid output during test
logging.basicConfig(level=logging.ERROR)

# Add src to path
sys.path.append(os.path.abspath("src"))

from adapters.inference.vllm_adapter import VllmAdapter
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from adapters.inference.gguf_adapter import GgufAdapter
from adapters.inference.local_llama_adapter import LocalLlamaAdapter
from adapters.inference.moondream_adapter import MoondreamAdapter

def check_instantiation(cls, *args, **kwargs):
    try:
        cls(*args, **kwargs)
        print(f"✅ {cls.__name__} instantiated successfully.")
    except TypeError as e:
        print(f"❌ {cls.__name__} failed to instantiate: {e}")

if __name__ == "__main__":
    check_instantiation(VllmAdapter)
    check_instantiation(Qwen3VLAdapter)
    check_instantiation(GgufAdapter, model_path="mock.gguf")
    check_instantiation(LocalLlamaAdapter, model_path="mock_path")
    check_instantiation(MoondreamAdapter)
