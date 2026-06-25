"""Standalone unit tests for the ported Vertex AI Feature Store infrastructure.

Only the self-contained client/adapter tests are kept here. The integration
tests from feature/vertex-pipelines (ArchetypeDriftService feature_store_port
wiring, PersonalizationMiddleware fast path, API routes) depend on wiring that
is still being re-integrated against main — they will be restored with that
batch.
"""

import os
from unittest.mock import patch

import pytest
from adapters.infrastructure.vertex_feature_store_client import (
    VertexFeatureStoreClient,
)
from django.core.cache import cache


@pytest.fixture(autouse=True)
def cleanup_mock_store():
    client = VertexFeatureStoreClient()
    mock_store_path = client.mock_store_path
    if os.path.exists(mock_store_path):
        try:
            os.remove(mock_store_path)
        except OSError:
            pass
    cache.clear()
    yield
    if os.path.exists(mock_store_path):
        try:
            os.remove(mock_store_path)
        except OSError:
            pass
    cache.clear()


def test_vertex_feature_store_client_simulation():
    with patch.dict(os.environ, {"VERTEX_AI_FEATURE_STORE_SIMULATION": "true"}):
        client = VertexFeatureStoreClient()
        assert client.simulation_mode is True

        test_features = {
            "shonen_hero": 0.9,
            "seinen_rebel": 0.1,
            "ghibli_dreamer": 0.0,
            "comedy_relief": 0.0,
        }
        client.write_online_features("user_101", test_features)

        fetched = client.get_online_features("user_101")
        assert fetched["shonen_hero"] == 0.9
        assert fetched["seinen_rebel"] == 0.1
        assert "last_calculated" in fetched


@pytest.mark.django_db
def test_feature_store_adapter_caching():
    with patch.dict(os.environ, {"VERTEX_AI_FEATURE_STORE_SIMULATION": "true"}):
        from adapters.persistence.feature_store_adapter import FeatureStoreAdapter

        adapter = FeatureStoreAdapter()

        test_features = {
            "shonen_hero": 0.5,
            "seinen_rebel": 0.5,
            "ghibli_dreamer": 0.0,
            "comedy_relief": 0.0,
        }
        adapter.save_user_preferences("user_202", test_features)

        # Verify Django Cache (L1) is updated
        cache_key = "user_features_user_202"
        assert cache.get(cache_key) == test_features

        # Fetch preferences and verify (served from L1 cache)
        fetched = adapter.get_user_preferences("user_202")
        assert fetched == test_features
