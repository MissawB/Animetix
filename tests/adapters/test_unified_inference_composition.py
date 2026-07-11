# tests/adapters/test_unified_inference_composition.py
from unittest.mock import MagicMock

from adapters.inference.components.manga_ocr_component import MangaOcrComponent
from adapters.inference.components.rerank_component import RerankComponent
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter


def _adapter():
    return UnifiedInferenceAdapter(api_base="http://x/v1", model_name="m")


def test_components_are_built_and_typed():
    a = _adapter()
    assert isinstance(a._rerank, RerankComponent)
    assert isinstance(a._manga_ocr, MangaOcrComponent)


def test_context_wired_from_adapter():
    a = _adapter()
    assert a._rerank._ctx.log_usage == a._log_usage
    assert a._rerank._ctx.generate == a.generate
    assert a._manga_ocr._ctx.log_usage == a._log_usage


def test_rerank_delegates_to_component():
    a = _adapter()
    a._rerank.rerank_documents = MagicMock(return_value=[0.5])
    assert a.rerank_documents("q", ["d"]) == [0.5]
    a._rerank.rerank_documents.assert_called_once_with("q", ["d"])


def test_manga_delegates_to_component():
    a = _adapter()
    a._manga_ocr.process_manga_page = MagicMock(return_value={"status": "success"})
    assert a.process_manga_page(b"img") == {"status": "success"}
    a._manga_ocr.process_manga_page.assert_called_once_with(b"img")


def test_no_longer_inherits_pilot_mixins():
    import importlib

    import pytest
    from adapters.inference.manga_ocr import MangaOcrMixin

    assert not issubclass(UnifiedInferenceAdapter, MangaOcrMixin)
    # RerankMixin is fully retired: RerankComponent is the single rerank
    # implementation (LocalRerankAdapter composes it too).
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("adapters.inference.rerank_mixin")


def test_capability_detection_still_routes_to_unified():
    a = _adapter()
    a.health_check = lambda: {"status": "offline"}  # avoid network in fallback init
    fb = FallbackInferenceAdapter([a])
    assert a in fb._capabilities.for_method("rerank_documents")
    assert a in fb._capabilities.for_method("process_manga_page")
