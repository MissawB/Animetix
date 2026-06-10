import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.exceptions import AuthenticationFailed
from django.test import RequestFactory

from animetix.models import Profile
from backend.api.animetix.auth import DeveloperApiKeyAuthentication
from backend.api.animetix.stripe_billing import StripeBillingService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def authenticator():
    return DeveloperApiKeyAuthentication()


@pytest.fixture
def user_pro(db):
    user = User.objects.create_user(username="dev_pro", email="pro@animetix.com")
    profile = user.profile
    profile.tier = "pro"
    profile.save()
    return user


@pytest.fixture
def user_free(db):
    user = User.objects.create_user(username="dev_free", email="free@animetix.com")
    # Profile created by signal defaults to 'free'
    return user


@pytest.mark.django_db
def test_api_key_authentication_no_key(rf, authenticator):
    request = rf.get("/api/v1/developer/rag/")
    result = authenticator.authenticate(request)
    assert result is None


@pytest.mark.django_db
def test_api_key_authentication_invalid_format(rf, authenticator):
    request = rf.get("/api/v1/developer/rag/")
    request.META["HTTP_X_API_KEY"] = "invalid_format_key"
    with pytest.raises(AuthenticationFailed) as exc:
        authenticator.authenticate(request)
    assert "Invalid API Key format" in str(exc.value)


@pytest.mark.django_db
def test_api_key_authentication_valid_flow(rf, authenticator, user_pro):
    profile = user_pro.profile
    raw_key = f"ax_pro_{profile.id}_mysecrettoken12345"
    profile.set_api_key(raw_key)
    profile.save()

    request = rf.get("/api/v1/developer/rag/")
    request.META["HTTP_X_API_KEY"] = raw_key
    
    auth_user, auth_key = authenticator.authenticate(request)
    assert auth_user == user_pro
    assert auth_key == raw_key


@pytest.mark.django_db
def test_api_key_authentication_restricted_tier(rf, authenticator, user_free):
    profile = user_free.profile
    raw_key = f"ax_pro_{profile.id}_mysecrettoken12345"
    profile.set_api_key(raw_key)
    profile.save()

    request = rf.get("/api/v1/developer/rag/")
    request.META["HTTP_X_API_KEY"] = raw_key

    with pytest.raises(AuthenticationFailed) as exc:
        authenticator.authenticate(request)
    assert "API access is restricted to Pro tier" in str(exc.value)


@pytest.mark.django_db
def test_api_key_view_lifecycle(api_client, user_pro):
    # Log in user (Session Authentication)
    api_client.force_authenticate(user=user_pro)

    # 1. GET key metadata
    res = api_client.get("/api/v1/developer/api-key/")
    assert res.status_code == 200
    assert res.data["tier"] == "pro"
    assert res.data["has_api_key"] is False

    # 2. Generate API Key
    res = api_client.post("/api/v1/developer/api-key/")
    assert res.status_code == 201
    raw_key = res.data["api_key"]
    assert raw_key.startswith(f"ax_pro_{user_pro.profile.id}_")

    # 3. GET key metadata again
    res = api_client.get("/api/v1/developer/api-key/")
    assert res.status_code == 200
    assert res.data["has_api_key"] is True


@pytest.mark.django_db
@patch("animetix.api.developer.get_container")
@patch("animetix.stripe_billing.StripeBillingService.report_usage")
def test_developer_rag_endpoint(mock_report, mock_container, api_client, user_pro):
    profile = user_pro.profile
    raw_key = f"ax_pro_{profile.id}_mysecrettoken12345"
    profile.set_api_key(raw_key)
    profile.save()

    # Mock RAG agent output
    mock_agent = MagicMock()
    mock_agent.plan_and_solve_stream.return_value = [
        {"type": "thought", "content": "RAG analysis..."},
        {"type": "result", "content": "Mocked RAG response about Naruto"}
    ]
    mock_container.return_value.agentic.agentic_rag.return_value = mock_agent

    # Call view with API Key
    api_client.credentials(HTTP_X_API_KEY=raw_key)
    res = api_client.post("/api/v1/developer/rag/", {"query": "Tell me about Naruto"}, format="json")
    
    assert res.status_code == 200
    assert res.data["answer"] == "Mocked RAG response about Naruto"
    assert res.data["status"] == "success"

    # Verify usage was reported to Stripe
    mock_report.assert_called_once()
    assert mock_report.call_args[0][0].id == profile.id


@pytest.mark.django_db
def test_stripe_webhook_upgrade(api_client, user_free):
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": user_free.id,
                "customer": "cus_test_12345",
                "subscription": "sub_test_12345"
            }
        }
    }
    
    res = api_client.post("/api/v1/developer/webhook/stripe/", webhook_payload, format="json")
    assert res.status_code == 200

    profile = Profile.objects.get(user_id=user_free.id)
    assert profile.tier == "pro"
    assert profile.stripe_customer_id == "cus_test_12345"
    assert profile.stripe_subscription_id == "sub_test_12345"


@pytest.mark.django_db
def test_stripe_webhook_downgrade(api_client, user_pro):
    profile = user_pro.profile
    profile.stripe_customer_id = "cus_test_12345"
    profile.save()

    webhook_payload = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "customer": "cus_test_12345",
                "status": "canceled"
            }
        }
    }
    
    res = api_client.post("/api/v1/developer/webhook/stripe/", webhook_payload, format="json")
    assert res.status_code == 200

    profile.refresh_from_db()
    assert profile.tier == "free"
    assert profile.stripe_subscription_id is None
