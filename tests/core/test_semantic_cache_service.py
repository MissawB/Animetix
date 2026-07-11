"""Behavior tests for SemanticCacheService (was ~31% covered — only the
None-port guards were exercised through other suites)."""

from unittest.mock import MagicMock

import pytest
from core.domain.services.semantic_cache_service import SemanticCacheService


@pytest.fixture
def cache_port():
    port = MagicMock()
    port.get.return_value = None
    port.get_semantic.return_value = None
    return port


@pytest.fixture
def engine():
    eng = MagicMock()
    eng.get_text_embedding.return_value = [0.1, 0.2, 0.3]
    return eng


@pytest.fixture
def service(engine, cache_port):
    return SemanticCacheService(inference_engine=engine, cache_port=cache_port)


def test_no_cache_port_returns_none_and_set_is_noop(engine):
    svc = SemanticCacheService(inference_engine=engine, cache_port=None)
    assert svc.get_cached_response("q") is None
    svc.set_cached_response("q", "r")  # must not raise
    engine.get_text_embedding.assert_not_called()


def test_exact_hit_short_circuits_semantic_lookup(service, cache_port, engine):
    cache_port.get.return_value = "cached answer"

    assert service.get_cached_response("who is Luffy?") == "cached answer"
    engine.get_text_embedding.assert_not_called()
    cache_port.get_semantic.assert_not_called()


def test_semantic_hit_uses_embedding_and_threshold(service, cache_port, engine):
    cache_port.get_semantic.return_value = "semantic answer"

    assert service.get_cached_response("who is luffy") == "semantic answer"
    engine.get_text_embedding.assert_called_once_with("who is luffy")
    cache_port.get_semantic.assert_called_once_with([0.1, 0.2, 0.3], 0.92)


def test_full_miss_returns_none(service):
    assert service.get_cached_response("brand new question") is None


def test_engine_without_embedding_support_skips_semantic(cache_port):
    engine = MagicMock(spec=[])  # no get_text_embedding attribute
    svc = SemanticCacheService(inference_engine=engine, cache_port=cache_port)

    assert svc.get_cached_response("q") is None
    cache_port.get_semantic.assert_not_called()


def test_retrieval_error_is_swallowed_to_none(service, cache_port):
    cache_port.get.side_effect = RuntimeError("redis down")
    assert service.get_cached_response("q") is None


def test_set_stores_query_embedding_and_response(service, cache_port, engine):
    service.set_cached_response("the query", "the response")
    cache_port.set.assert_called_once_with("the query", [0.1, 0.2, 0.3], "the response")


def test_set_without_embedding_support_stores_empty_vector(cache_port):
    engine = MagicMock(spec=[])
    svc = SemanticCacheService(inference_engine=engine, cache_port=cache_port)

    svc.set_cached_response("q", "r")
    cache_port.set.assert_called_once_with("q", [], "r")


def test_storage_error_is_swallowed(service, cache_port):
    cache_port.set.side_effect = RuntimeError("redis down")
    service.set_cached_response("q", "r")  # must not raise
