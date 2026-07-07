"""Coverage for animetix.api.developer view module.

Covers the B2B developer RAG endpoint, API-key metadata/generation and the
(now free/manual) Pro-tier subscription mock endpoint.

External collaborators are mocked:
  - the agentic RAG stream via ``developer.get_container``
  - usage logging via ``developer.DjangoUsageAdapter``
ORM access uses the real (sqlite) test DB through ``@pytest.mark.django_db``.
"""

from unittest.mock import MagicMock, patch

import pytest
from animetix.api import developer as developer_mod
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    # Profile is auto-created via post_save signal.
    return User.objects.create_user(username="devuser", password="password")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


# --------------------------------------------------------------------------- #
# DeveloperRAGView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_developer_rag_missing_query(auth_client):
    """No query -> 400."""
    response = auth_client.post(reverse("developer_rag"), {}, format="json")
    assert response.status_code == 400
    assert response.json()["error"] == "No query provided"


@pytest.mark.django_db
def test_developer_rag_success_result_event(auth_client):
    """Stream emits a 'result' event -> answer extracted from it."""
    agent = MagicMock()
    agent.plan_and_solve_stream.return_value = iter(
        [
            {"type": "status", "content": "thinking"},
            {"type": "result", "content": "Luffy is the captain."},
        ]
    )
    fake_container = MagicMock()
    fake_container.agentic.agentic_rag.return_value = agent

    with (
        patch.object(developer_mod, "get_container", return_value=fake_container),
        patch.object(developer_mod, "DjangoUsageAdapter") as usage_cls,
    ):
        response = auth_client.post(
            reverse("developer_rag"),
            {"query": "Who is Luffy?", "media_type": "Manga"},
            format="json",
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["answer"] == "Luffy is the captain."
    assert body["media_type"] == "Manga"
    usage_cls.return_value.log_usage.assert_called_once()


@pytest.mark.django_db
def test_developer_rag_fallback_to_last_non_status_event(auth_client):
    """No explicit 'result' event -> falls back to last non-error/status event."""
    agent = MagicMock()
    agent.plan_and_solve_stream.return_value = iter(
        [
            {"type": "status", "content": "thinking"},
            {"type": "token", "content": "partial answer"},
        ]
    )
    fake_container = MagicMock()
    fake_container.agentic.agentic_rag.return_value = agent

    with (
        patch.object(developer_mod, "get_container", return_value=fake_container),
        patch.object(developer_mod, "DjangoUsageAdapter"),
    ):
        response = auth_client.post(
            reverse("developer_rag"),
            {"query": "tell me"},
            format="json",
        )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "partial answer"
    assert body["media_type"] == "Anime"  # default


@pytest.mark.django_db
def test_developer_rag_exception_returns_500(auth_client):
    """Agent raising -> 500 with error message."""
    fake_container = MagicMock()
    fake_container.agentic.agentic_rag.side_effect = RuntimeError("boom")

    with patch.object(developer_mod, "get_container", return_value=fake_container):
        response = auth_client.post(
            reverse("developer_rag"),
            {"query": "x"},
            format="json",
        )

    assert response.status_code == 500
    assert response.json()["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# DeveloperApiKeyView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_api_key_get_metadata_no_key(auth_client, user):
    response = auth_client.get(reverse("developer_api_key"))
    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "free"
    assert body["has_api_key"] is False
    assert body["api_key_prefix"] is None


@pytest.mark.django_db
def test_api_key_get_metadata_with_key(auth_client, user):
    user.profile.set_api_key("ax_pro_1_secret")
    user.profile.save()
    response = auth_client.get(reverse("developer_api_key"))
    body = response.json()
    assert body["has_api_key"] is True
    assert body["api_key_prefix"] == "ax_pro_"


@pytest.mark.django_db
def test_api_key_post_forbidden_for_non_pro(auth_client, user):
    """Free-tier users cannot generate keys -> 403."""
    response = auth_client.post(reverse("developer_api_key"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_api_key_post_generates_key_for_pro(auth_client, user):
    user.profile.tier = "pro"
    user.profile.save()
    response = auth_client.post(reverse("developer_api_key"))
    assert response.status_code == 201
    body = response.json()
    assert body["api_key"].startswith(f"ax_pro_{user.profile.id}_")
    user.profile.refresh_from_db()
    assert user.profile.api_key_hash  # hashed key persisted


# --------------------------------------------------------------------------- #
# DeveloperSubscriptionMockView (Pro tier is now free/manual — no Stripe)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_subscribe_mock_sets_pro_tier(auth_client, user):
    response = auth_client.post(reverse("developer_subscribe_mock"))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "subscribed"
    assert body["tier"] == "pro"
    # Pro tier is now free/manual — no Stripe IDs are minted or returned.
    assert "stripe_customer_id" not in body
    user.profile.refresh_from_db()
    assert user.profile.tier == "pro"
