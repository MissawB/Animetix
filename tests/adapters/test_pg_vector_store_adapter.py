"""Behavior tests for ``PgVectorStoreAdapter.get_collection_count``.

Added alongside the billing fix for image search (CLIP): `CrossModalSearchService
.is_available()` calls this on every search request to decide whether
`unified_clip_space` can possibly answer before Berrix is charged. We replace
the module-level ``vector_manager`` with a MagicMock so no real pgvector/DB is
touched, and clear the Django cache around each test (this adapter caches the
count for a short TTL -- see the module docstring in the adapter itself).
"""

from unittest.mock import MagicMock, patch

import pytest
from adapters.persistence.pg_vector_store_adapter import PgVectorStoreAdapter


@pytest.fixture(autouse=True)
def _clear_django_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def adapter():
    return PgVectorStoreAdapter()


def test_get_collection_count_returns_manager_count(adapter):
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.return_value = 12
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 12


def test_get_collection_count_zero_on_error(adapter):
    mock_manager = MagicMock()
    mock_manager.get_collection.side_effect = RuntimeError("boom")
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 0


def test_get_collection_count_is_cached(adapter):
    """Without a cache, `CrossModalSearchService.is_available()` would add a
    COUNT(*) to every image-search request -- this pins that it doesn't."""
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.return_value = 7
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 7
        assert adapter.get_collection_count("unified_clip_space") == 7
    mock_manager.get_collection.assert_called_once_with("unified_clip_space")
