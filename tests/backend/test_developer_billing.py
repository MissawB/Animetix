import pytest
from animetix.auth import DeveloperApiKeyAuthentication
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


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
