"""Behavior tests for DjangoSemanticCacheAdapter.

The adapter mixes two backends:
  * a Django ``SemanticCache`` model for *exact* query-text matches, and
  * a Chroma vector store (``chroma_manager``) for *semantic* (cosine) lookups.

Both are imported lazily *inside* the methods, so we patch them in their source
modules (``animetix.models`` / ``pipeline.chroma_client``) via injected fakes —
no real Django DB and no real Chroma/pgvector are touched, keeping the test a
fast, isolated unit test. Assertions target the REAL logic: the
``similarity = 1 - distance >= threshold`` hit/miss branch, how a stored row /
metadata maps to the cached value, the exact embedding/ids passed to the store,
and the update_or_create upsert path.
"""

import hashlib
import json
import sys
import types
from unittest.mock import MagicMock

import adapters.persistence.django_semantic_cache_adapter as mod
import pytest
from adapters.persistence.django_semantic_cache_adapter import (
    DjangoSemanticCacheAdapter,
)


@pytest.fixture
def fake_model(monkeypatch):
    """Inject a fake ``animetix.models`` module exposing ``SemanticCache``."""
    semantic_cache = MagicMock(name="SemanticCache")
    fake = types.ModuleType("animetix.models")
    fake.SemanticCache = semantic_cache
    monkeypatch.setitem(sys.modules, "animetix.models", fake)
    return semantic_cache


@pytest.fixture
def fake_chroma(monkeypatch):
    """Inject a fake ``pipeline.chroma_client`` module exposing ``chroma_manager``."""
    manager = MagicMock(name="chroma_manager")
    fake = types.ModuleType("pipeline.chroma_client")
    fake.chroma_manager = manager
    monkeypatch.setitem(sys.modules, "pipeline.chroma_client", fake)
    return manager


# --- get (exact relational match) ---------------------------------------


def test_get_returns_response_text_of_matching_row(fake_model):
    row = MagicMock(response_text="cached answer")
    fake_model.objects.filter.return_value.first.return_value = row

    adapter = DjangoSemanticCacheAdapter()
    assert adapter.get("what is up") == "cached answer"
    # The query is filtered by the exact query_text, not anything else.
    fake_model.objects.filter.assert_called_once_with(query_text="what is up")


def test_get_returns_none_when_no_row(fake_model):
    fake_model.objects.filter.return_value.first.return_value = None
    assert DjangoSemanticCacheAdapter().get("missing") is None


# --- get_semantic: guard ------------------------------------------------


def test_get_semantic_empty_embedding_short_circuits(fake_chroma):
    # Empty embedding must return None *without* ever querying the vector store.
    assert DjangoSemanticCacheAdapter().get_semantic([], threshold=0.5) is None
    fake_chroma.query_collection.assert_not_called()


# --- get_semantic: hit / miss threshold branch --------------------------


def _chroma_result(distance, meta):
    return {"distances": [[distance]], "metadatas": [[meta]]}


def test_get_semantic_hit_when_similarity_meets_threshold(fake_chroma):
    # distance 0.1 -> similarity 0.9 ; threshold 0.9 -> 0.9 >= 0.9 is a HIT.
    fake_chroma.query_collection.return_value = _chroma_result(
        0.1, {"response": "semantic answer", "query": "q"}
    )
    adapter = DjangoSemanticCacheAdapter(collection_name="my_cache")

    result = adapter.get_semantic([0.1, 0.2, 0.3], threshold=0.9)

    assert result == "semantic answer"
    # The exact embedding is forwarded (wrapped in a list) to the right collection.
    fake_chroma.query_collection.assert_called_once_with(
        collection_name="my_cache",
        query_embeddings=[[0.1, 0.2, 0.3]],
        n_results=1,
    )


def test_get_semantic_miss_when_below_threshold(fake_chroma):
    # distance 0.3 -> similarity 0.7 ; threshold 0.9 -> 0.7 < 0.9 is a MISS.
    fake_chroma.query_collection.return_value = _chroma_result(
        0.3, {"response": "too far", "query": "q"}
    )
    assert DjangoSemanticCacheAdapter().get_semantic([0.1], threshold=0.9) is None


def test_get_semantic_boundary_exact_threshold_is_hit(fake_chroma):
    # similarity exactly equals threshold (0.8) -> the >= branch makes it a hit.
    fake_chroma.query_collection.return_value = _chroma_result(
        0.2, {"response": "edge", "query": "q"}
    )
    assert DjangoSemanticCacheAdapter().get_semantic([0.5], threshold=0.8) == "edge"


# --- get_semantic: metadata mapping -------------------------------------


def test_get_semantic_parses_json_string_metadata(fake_chroma):
    # Some backends return metadata as a JSON string; it must be decoded.
    meta = json.dumps({"response": "from json", "query": "q"})
    fake_chroma.query_collection.return_value = _chroma_result(0.0, meta)
    assert (
        DjangoSemanticCacheAdapter().get_semantic([1.0], threshold=0.5) == "from json"
    )


def test_get_semantic_invalid_json_string_returns_none(fake_chroma):
    fake_chroma.query_collection.return_value = _chroma_result(0.0, "{not json")
    assert DjangoSemanticCacheAdapter().get_semantic([1.0], threshold=0.5) is None


def test_get_semantic_missing_response_key_returns_none(fake_chroma):
    # Hit on similarity, but the metadata dict has no "response" key.
    fake_chroma.query_collection.return_value = _chroma_result(0.0, {"query": "q only"})
    assert DjangoSemanticCacheAdapter().get_semantic([1.0], threshold=0.5) is None


def test_get_semantic_empty_results_returns_none(fake_chroma):
    fake_chroma.query_collection.return_value = {
        "distances": [[]],
        "metadatas": [[]],
    }
    assert DjangoSemanticCacheAdapter().get_semantic([1.0], threshold=0.5) is None


def test_get_semantic_swallows_store_exception(fake_chroma):
    fake_chroma.query_collection.side_effect = RuntimeError("vector store down")
    # Error is logged and None returned — never propagated.
    assert DjangoSemanticCacheAdapter().get_semantic([1.0], threshold=0.5) is None


# --- set: relational upsert + vector add --------------------------------


def test_set_upserts_relational_and_adds_vector(fake_model, fake_chroma):
    adapter = DjangoSemanticCacheAdapter(collection_name="col")
    adapter.set("query text", [0.1, 0.2], "the response")

    # 1. Relational upsert keyed on query_text with response in defaults.
    fake_model.objects.update_or_create.assert_called_once_with(
        query_text="query text", defaults={"response_text": "the response"}
    )

    # 2. Vector add: id is the sha256 of the query, embedding + metadata forwarded.
    expected_hash = hashlib.sha256("query text".encode("utf-8")).hexdigest()
    fake_chroma.add_to_collection.assert_called_once_with(
        collection_name="col",
        ids=[expected_hash],
        embeddings=[[0.1, 0.2]],
        metadatas=[{"response": "the response", "query": "query text"}],
    )


def test_set_skips_vector_add_when_no_embedding(fake_model, fake_chroma):
    DjangoSemanticCacheAdapter().set("q", [], "resp")
    # Relational upsert still happens; vector store is left untouched.
    fake_model.objects.update_or_create.assert_called_once()
    fake_chroma.add_to_collection.assert_not_called()


def test_set_swallows_vector_add_exception(fake_model, fake_chroma):
    fake_chroma.add_to_collection.side_effect = RuntimeError("boom")
    # Must not raise; relational write already committed before the failure.
    DjangoSemanticCacheAdapter().set("q", [0.9], "resp")
    fake_model.objects.update_or_create.assert_called_once()


def test_default_collection_name():
    assert DjangoSemanticCacheAdapter().collection_name == "semantic_cache"
    assert mod is not None  # module import sanity
