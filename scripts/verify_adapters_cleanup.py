import sys
import os
import logging
from typing import List

# Mock logging to avoid output during test
logging.basicConfig(level=logging.ERROR)

# Add src to path
sys.path.append(os.path.abspath("src"))

from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from adapters.inference.local_llama_adapter import LocalLlamaAdapter
from adapters.inference.transformers_adapter import TransformersAdapter
from adapters.inference.moondream_adapter import MoondreamAdapter
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from adapters.inference.transformers_text_adapter import TransformersTextAdapter
from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter

def test_adapter(adapter: InferencePort, adapter_name: str):
    print(f"\n--- Testing {adapter_name} ---")

    # These should be implemented and NOT raise NotImplementedError
    try:
        adapter.health_check()
        print(f"✅ {adapter_name}.health_check() implemented")
    except Exception as e:
        print(f"❌ {adapter_name}.health_check() failed: {e}")

    # This should raise InferenceNotImplementedError if removed correctly (and if not implemented)
    try:
        adapter.calculate_visual_similarity("test", "test", "test")
        print(f"⚠️ {adapter_name}.calculate_visual_similarity() returned a value (maybe implemented?)")
    except InferenceNotImplementedError:
        print(f"✅ {adapter_name}.calculate_visual_similarity() correctly delegates to base class (raises InferenceNotImplementedError)")
    except Exception as e:
        print(f"❌ {adapter_name}.calculate_visual_similarity() raised unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # Disable lazy loading effects if possible or just ignore for instantiation
    adapters = [
        (LocalLlamaAdapter(model_path="mock"), "LocalLlamaAdapter"),
        (TransformersTextAdapter(), "TransformersTextAdapter"),
        (MoondreamAdapter(), "MoondreamAdapter"),
        (Qwen3VLAdapter(), "Qwen3VLAdapter"),
        (AudioTransformersAdapter(), "AudioTransformersAdapter"),
        (MangaOCRAdapter(), "MangaOCRAdapter"),
    ]
    
    for adapter, name in adapters:
        try:
            test_adapter(adapter, name)
        except Exception as e:
            print(f"❌ Global failure for {name}: {e}")
