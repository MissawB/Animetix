import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client
from django.urls import reverse


@pytest.fixture
def api_client():
    return Client()


def test_webhook_ignored_when_under_budget(api_client):
    url = reverse("api_billing_webhook")
    from django.urls import resolve

    view_func = resolve(url).func
    while hasattr(view_func, "__wrapped__"):
        view_func = view_func.__wrapped__

    mock_shutdown = MagicMock(return_value=(True, "mocked"))
    original_shutdown = view_func.__globals__.get("shutdown_brain_service")
    view_func.__globals__["shutdown_brain_service"] = mock_shutdown

    try:
        # Budget $100, cost $50
        alert_data = {
            "costAmount": 50.0,
            "budgetAmount": 100.0,
            "budgetDisplayName": "Test Budget",
        }
        encoded_data = base64.b64encode(json.dumps(alert_data).encode("utf-8")).decode(
            "utf-8"
        )

        payload = {"message": {"data": encoded_data}}

        response = api_client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        mock_shutdown.assert_not_called()
    finally:
        if original_shutdown is not None:
            view_func.__globals__["shutdown_brain_service"] = original_shutdown
        else:
            view_func.__globals__["shutdown_brain_service"] = None


def test_webhook_shutdown_when_budget_exceeded(api_client):
    url = reverse("api_billing_webhook")
    from django.urls import resolve

    view_func = resolve(url).func
    while hasattr(view_func, "__wrapped__"):
        view_func = view_func.__wrapped__

    mock_shutdown = MagicMock(return_value=(True, {"status": "ok"}))
    original_shutdown = view_func.__globals__.get("shutdown_brain_service")
    view_func.__globals__["shutdown_brain_service"] = mock_shutdown

    try:
        # Budget $100, cost $105
        alert_data = {
            "costAmount": 105.0,
            "budgetAmount": 100.0,
            "budgetDisplayName": "Test Budget",
        }
        encoded_data = base64.b64encode(json.dumps(alert_data).encode("utf-8")).decode(
            "utf-8"
        )

        payload = {"message": {"data": encoded_data}}

        response = api_client.post(
            url, data=json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "shutdown_triggered"
        mock_shutdown.assert_called_once()
    finally:
        if original_shutdown is not None:
            view_func.__globals__["shutdown_brain_service"] = original_shutdown
        else:
            view_func.__globals__["shutdown_brain_service"] = None


@patch("google.oauth2.id_token.verify_oauth2_token")
def test_webhook_production_oidc_success(mock_verify, api_client):
    from django.conf import settings  # noqa: E402

    url = reverse("api_billing_webhook")
    from django.urls import resolve

    view_func = resolve(url).func
    while hasattr(view_func, "__wrapped__"):
        view_func = view_func.__wrapped__

    mock_shutdown = MagicMock(return_value=(True, {"status": "ok"}))
    original_shutdown = view_func.__globals__.get("shutdown_brain_service")
    view_func.__globals__["shutdown_brain_service"] = mock_shutdown
    mock_verify.return_value = {"email": "pubsub@gcp.com"}

    try:
        alert_data = {
            "costAmount": 105.0,
            "budgetAmount": 100.0,
            "budgetDisplayName": "Test Budget",
        }
        encoded_data = base64.b64encode(json.dumps(alert_data).encode("utf-8")).decode(
            "utf-8"
        )
        payload = {"message": {"data": encoded_data}}

        with patch.object(settings, "IS_PRODUCTION", True):
            response = api_client.post(
                url,
                data=json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer valid-token",
            )

        assert response.status_code == 200
        assert response.json()["status"] == "shutdown_triggered"
        mock_shutdown.assert_called_once()
        mock_verify.assert_called_once()
    finally:
        if original_shutdown is not None:
            view_func.__globals__["shutdown_brain_service"] = original_shutdown
        else:
            view_func.__globals__["shutdown_brain_service"] = None


@patch("google.oauth2.id_token.verify_oauth2_token")
def test_webhook_production_oidc_missing_header(mock_verify, api_client):
    from django.conf import settings  # noqa: E402

    url = reverse("api_billing_webhook")
    with patch.object(settings, "IS_PRODUCTION", True):
        response = api_client.post(
            url, data=json.dumps({}), content_type="application/json"
        )
    assert response.status_code == 401
    mock_verify.assert_not_called()
