"""Coverage for animetix.api.developer view module.

Covers the B2B developer RAG endpoint, API-key metadata/generation, Stripe
checkout/mock subscription endpoints and the Stripe webhook (bx purchase, pro
upgrade, subscription cancel, malformed payload).

External collaborators are mocked:
  - the agentic RAG stream via ``developer.get_container``
  - usage logging via ``developer.DjangoUsageAdapter``
  - Stripe via ``developer.StripeBillingService``
ORM access uses the real (sqlite) test DB through ``@pytest.mark.django_db``.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from animetix.api import developer as developer_mod
from animetix.models import WalletTransaction
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
# CreateProSubscriptionCheckoutView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_subscribe_pro_success(auth_client):
    with patch.object(
        developer_mod.StripeBillingService,
        "create_subscription_checkout_session",
        return_value=(True, "https://stripe/checkout"),
    ):
        response = auth_client.post(reverse("developer_subscribe_pro"))
    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://stripe/checkout"


@pytest.mark.django_db
def test_subscribe_pro_failure(auth_client):
    with patch.object(
        developer_mod.StripeBillingService,
        "create_subscription_checkout_session",
        return_value=(False, "stripe error"),
    ):
        response = auth_client.post(reverse("developer_subscribe_pro"))
    assert response.status_code == 500
    assert response.json()["error"] == "Internal server error"


# --------------------------------------------------------------------------- #
# DeveloperSubscriptionMockView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_subscribe_mock_sets_pro_tier(auth_client, user):
    response = auth_client.post(reverse("developer_subscribe_mock"))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "subscribed"
    assert body["tier"] == "pro"
    user.profile.refresh_from_db()
    assert user.profile.tier == "pro"
    assert user.profile.stripe_customer_id.startswith("cus_mock_")


# --------------------------------------------------------------------------- #
# CreateBxCheckoutView
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_bx_checkout_missing_fields(auth_client):
    # No pack_id -> 400 with "Unknown pack_id" error listing available packs.
    response = auth_client.post(reverse("api_wallet_checkout"), {}, format="json")
    assert response.status_code == 400
    assert "Unknown pack_id" in response.json()["error"]


@pytest.mark.django_db
def test_bx_checkout_success(auth_client):
    with patch.object(
        developer_mod.StripeBillingService,
        "create_checkout_session",
        return_value=(True, "https://stripe/bx"),
    ):
        response = auth_client.post(
            reverse("api_wallet_checkout"),
            {"pack_id": "initiate"},
            format="json",
        )
    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://stripe/bx"


@pytest.mark.django_db
def test_bx_checkout_stripe_failure(auth_client):
    with patch.object(
        developer_mod.StripeBillingService,
        "create_checkout_session",
        return_value=(False, "declined"),
    ):
        response = auth_client.post(
            reverse("api_wallet_checkout"),
            {"pack_id": "initiate"},
            format="json",
        )
    assert response.status_code == 500
    assert response.json()["error"] == "Internal server error"


@pytest.mark.django_db
def test_bx_checkout_ignores_client_price_and_uses_catalog(auth_client):
    with patch.object(
        developer_mod.StripeBillingService,
        "create_checkout_session",
        return_value=(True, "https://stripe/bx"),
    ) as mock_create:
        # Client tries to buy a real pack for 1 cent — server must ignore the price.
        resp = auth_client.post(
            reverse("api_wallet_checkout"),
            {"pack_id": "initiate", "amount": 999999, "price_cents": 1},
            format="json",
        )
    assert resp.status_code == 200
    # The endpoint must call Stripe with the CATALOG price, not the client-supplied values.
    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args.kwargs
    assert (
        call_kwargs["amount_bx"] == 10000
    ), f"Expected catalog amount_bx=10000, got {call_kwargs['amount_bx']}"
    assert call_kwargs["price_cents"] == 499, (
        f"Expected catalog price_cents=499, got {call_kwargs['price_cents']} "
        "(server must NOT use the client-supplied price_cents=1)"
    )


@pytest.mark.django_db
def test_bx_checkout_rejects_unknown_pack(auth_client):
    resp = auth_client.post(
        reverse("api_wallet_checkout"),
        {"pack_id": "does_not_exist"},
        format="json",
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# StripeWebhookView
# --------------------------------------------------------------------------- #
def _post_webhook(api_client, payload):
    return api_client.post(
        reverse("developer_webhook_stripe"),
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_webhook_malformed_payload(api_client):
    """Invalid JSON body -> 400."""
    response = api_client.post(
        reverse("developer_webhook_stripe"),
        data="not-json",
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_webhook_bx_purchase_credits_wallet(api_client, user):
    start_balance = user.profile.wallet_balance
    payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": str(user.id),
                "customer": "cus_123",
                "metadata": {"transaction_type": "bx_purchase", "amount_bx": "5000"},
            }
        },
    }
    response = _post_webhook(api_client, payload)
    assert response.status_code == 200
    user.profile.refresh_from_db()
    assert user.profile.wallet_balance == start_balance + 5000
    assert WalletTransaction.objects.filter(user=user, amount=5000).exists()


@pytest.mark.django_db
def test_webhook_pro_subscription_upgrade(api_client, user):
    payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": str(user.id),
                "customer": "cus_pro",
                "subscription": "sub_pro",
                "metadata": {"transaction_type": "pro_subscription_upgrade"},
            }
        },
    }
    # STRIPE_SECRET_KEY may be unset in test settings -> the stripe.Subscription
    # retrieval branch is skipped; tier upgrade still happens.
    response = _post_webhook(api_client, payload)
    assert response.status_code == 200
    user.profile.refresh_from_db()
    assert user.profile.tier == "pro"
    assert user.profile.stripe_customer_id == "cus_pro"
    assert user.profile.stripe_subscription_id == "sub_pro"


@pytest.mark.django_db
def test_webhook_checkout_unknown_profile_logs_and_200(api_client):
    payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "999999",  # no such user
                "customer": "cus_x",
                "metadata": {"transaction_type": "bx_purchase", "amount_bx": "100"},
            }
        },
    }
    response = _post_webhook(api_client, payload)
    assert response.status_code == 200


@pytest.mark.django_db
def test_webhook_subscription_deleted_downgrades(api_client, user):
    user.profile.tier = "pro"
    user.profile.stripe_customer_id = "cus_down"
    user.profile.stripe_subscription_id = "sub_down"
    user.profile.save()

    payload = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_down", "status": "canceled"}},
    }
    response = _post_webhook(api_client, payload)
    assert response.status_code == 200
    user.profile.refresh_from_db()
    assert user.profile.tier == "free"
    assert user.profile.stripe_subscription_id is None


@pytest.mark.django_db
def test_webhook_unknown_event_type_ignored(api_client):
    payload = {"type": "invoice.paid", "data": {"object": {}}}
    response = _post_webhook(api_client, payload)
    assert response.status_code == 200
