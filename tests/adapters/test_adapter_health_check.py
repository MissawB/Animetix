"""health_check is factored into LazyLocalModelAdapter; adapters expose _is_ready.

Instances are built with object.__new__ to avoid loading real models in __init__.
"""

from adapters.inference.audio_transformers_adapter import AudioTransformersAdapter
from adapters.inference.diffusers_adapter import DiffusersAdapter
from adapters.inference.local_rerank_adapter import LocalRerankAdapter
from adapters.inference.local_text_adapter import LocalTextAdapter
from adapters.inference.manga_ocr_adapter import MangaOCRAdapter
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from adapters.inference.vision_transformers_adapter import VisionTransformersAdapter


def test_local_text_readiness_tracks_the_generation_model_only():
    """A loaded EMBEDDING model used to vouch for the (unloaded) causal LM, so the
    fallback router preferred this adapter over the managed remote one -- then
    generate() pulled multi-GB weights in and OOM-killed the container (prod 503,
    2026-07-12). Only the model that answers generate() may mark it online."""
    a = object.__new__(LocalTextAdapter)
    a.model = None
    a._embedding_model = None
    assert a.health_check()["status"] == "offline"

    a._embedding_model = object()  # embedder loaded, LLM still absent
    assert a.health_check()["status"] == "offline"

    a.model = object()  # the generation model is what counts
    assert a.health_check()["status"] == "online"


def test_diffusers_health_check_readiness_and_fields():
    a = object.__new__(DiffusersAdapter)
    a.pipe = None
    a._img2img_pipe = None
    a._inpaint_pipe = None
    a.model_id = "black-forest-labs/FLUX.1-schnell"
    hc = a.health_check()
    assert hc["engine"] == "diffusers"
    assert hc["status"] == "offline"
    assert hc["model"] == "black-forest-labs/FLUX.1-schnell"
    a._img2img_pipe = object()
    assert a.health_check()["status"] == "online"


def test_audio_health_check_readiness():
    a = object.__new__(AudioTransformersAdapter)
    a._tts_model = None
    a._audioldm_pipeline = None
    a._moshi_model = None
    assert a.health_check() == {"status": "offline", "engine": "audio_transformers"}
    a._moshi_model = object()
    assert a.health_check()["status"] == "online"


def test_local_rerank_health_check_readiness():
    # Readiness is delegated to the composed RerankComponent's lazy cache.
    a = LocalRerankAdapter()
    assert a.health_check() == {"status": "offline", "engine": "local_rerank"}
    a._rerank._cross_encoder = object()
    assert a.health_check()["status"] == "online"


def test_manga_ocr_health_check_readiness():
    a = object.__new__(MangaOCRAdapter)
    a.ocr_pipeline = None
    assert a.health_check() == {"status": "offline", "engine": "LightonOCR"}
    a.ocr_pipeline = object()
    assert a.health_check()["status"] == "online"


def test_qwen3_vl_health_check_precise_readiness():
    a = object.__new__(Qwen3VLAdapter)
    a.client = None
    assert a.health_check() == {"status": "offline", "engine": "Qwen3-VL"}
    a.client = object()
    assert a.health_check()["status"] == "online"


def test_vision_transformers_facade_always_online():
    a = object.__new__(VisionTransformersAdapter)
    assert a.health_check() == {"status": "online", "engine": "vision_transformers"}
