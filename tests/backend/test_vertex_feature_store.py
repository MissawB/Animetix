"""Unit + API tests for the ported Vertex AI Feature Store feature.

Covers the self-contained client/adapter and the VertexFeatureStoreView API
(auth + get/post via DI override). The deeper personalization integration
(ArchetypeDriftService feature_store_port + PersonalizationMiddleware fast-path)
is intentionally deferred — it rewrites a central middleware/service and is a
separate, higher-risk change.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from adapters.infrastructure.vertex_feature_store_client import (
    VertexFeatureStoreClient,
)
from animetix.containers import container
from core.ports.feature_store_port import FeatureStorePort
from dependency_injector import providers
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse


@pytest.fixture(autouse=True)
def _brain_api_url(monkeypatch):
    # Authenticated JSON responses pass through PersonalizationMiddleware, which
    # builds the inference chain (incl. BrainAPIAdapter, requiring BRAIN_API_URL).
    # Set a dummy so construction succeeds; keeps the tests hermetic.
    monkeypatch.setenv("BRAIN_API_URL", "http://localhost:5000")


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


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="user", password="password")


@pytest.fixture
def mock_feature_store():
    store = MagicMock(spec=FeatureStorePort)
    store.get_user_preferences.return_value = {
        "shonen_hero": 0.7,
        "seinen_rebel": 0.2,
        "ghibli_dreamer": 0.1,
        "comedy_relief": 0.0,
        "last_calculated": "2026-06-04T19:30:00Z",
    }
    return store


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

        cache_key = "user_features_user_202"
        assert cache.get(cache_key) == test_features

        fetched = adapter.get_user_preferences("user_202")
        assert fetched == test_features


@pytest.mark.django_db
def test_vertex_feature_store_api_auth(client, regular_user):
    url = reverse("mlops-features")

    # Unauthenticated
    response = client.get(url, {"user_id": "1"})
    assert response.status_code in [401, 403]

    # Regular (non-admin) user forbidden
    client.force_login(regular_user)
    response = client.get(url, {"user_id": "1"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_vertex_feature_store_api_get_post(client, admin_user, mock_feature_store):
    client.force_login(admin_user)
    url = reverse("mlops-features")

    with container.persistence.feature_store_adapter.override(
        providers.Object(mock_feature_store)
    ):
        # GET
        response = client.get(url, {"user_id": "999"})
        assert response.status_code == 200
        assert response.json()["features"]["seinen_rebel"] == 0.2
        mock_feature_store.get_user_preferences.assert_any_call("999")

        # POST
        post_data = {
            "user_id": "999",
            "features": {
                "shonen_hero": 1.0,
                "seinen_rebel": 0.0,
                "ghibli_dreamer": 0.0,
                "comedy_relief": 0.0,
            },
        }
        response = client.post(url, post_data, content_type="application/json")
        assert response.status_code == 201
        mock_feature_store.save_user_preferences.assert_called_once_with(
            "999", post_data["features"]
        )
