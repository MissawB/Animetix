"""Behavior tests for AlertService (was 0% covered while being live prod code:
the hourly-health-monitoring Cloud Run job calls check_and_alert)."""

from unittest.mock import MagicMock

import pytest
from core.domain.services.alert_service import AlertService

ADMIN_ID = 42


@pytest.fixture
def notification_port():
    return MagicMock()


@pytest.fixture
def drift_service():
    svc = MagicMock()
    svc.get_drift_report.return_value = {}
    return svc


@pytest.fixture
def obs_service():
    svc = MagicMock()
    svc.get_average_rag_latency.return_value = 0.5
    return svc


@pytest.fixture
def alert_service(notification_port, drift_service, obs_service):
    return AlertService(
        notification_port=notification_port,
        drift_service=drift_service,
        observability_service=obs_service,
    )


def test_healthy_system_sends_no_notification(alert_service, notification_port):
    alert_service.check_and_alert(admin_user_id=ADMIN_ID)
    notification_port.send.assert_not_called()


def test_drift_alert_sent_for_alerting_collection(
    alert_service, drift_service, notification_port
):
    drift_service.get_drift_report.return_value = {
        "anime": {"status": "alert", "p_value": 0.001},
        "manga": {"status": "ok", "p_value": 0.8},
    }

    alert_service.check_and_alert(admin_user_id=ADMIN_ID)

    notification_port.send.assert_called_once()
    kwargs = notification_port.send.call_args.kwargs
    assert kwargs["user_id"] == ADMIN_ID
    assert kwargs["notification_type"] == "alert"
    assert kwargs["link"] == "/admin/mlops"
    assert "ANIME" in kwargs["title"]
    assert "0.001" in kwargs["message"]


def test_drift_alert_per_alerting_collection(
    alert_service, drift_service, notification_port
):
    drift_service.get_drift_report.return_value = {
        "anime": {"status": "alert", "p_value": 0.001},
        "manga": {"status": "alert", "p_value": 0.005},
    }
    alert_service.check_and_alert(admin_user_id=ADMIN_ID)
    assert notification_port.send.call_count == 2


def test_latency_above_threshold_triggers_warning(
    alert_service, obs_service, notification_port
):
    obs_service.get_average_rag_latency.return_value = 6.2

    alert_service.check_and_alert(admin_user_id=ADMIN_ID)

    notification_port.send.assert_called_once()
    kwargs = notification_port.send.call_args.kwargs
    assert kwargs["notification_type"] == "warning"
    assert kwargs["link"] == "/admin/health"
    assert "6.20s" in kwargs["message"]


def test_latency_at_threshold_does_not_alert(
    alert_service, obs_service, notification_port
):
    # Strict comparison: exactly 5.0s must not alert.
    obs_service.get_average_rag_latency.return_value = 5.0
    alert_service.check_and_alert(admin_user_id=ADMIN_ID)
    notification_port.send.assert_not_called()


def test_drift_and_latency_alerts_are_cumulative(
    alert_service, drift_service, obs_service, notification_port
):
    drift_service.get_drift_report.return_value = {
        "anime": {"status": "alert", "p_value": 0.002}
    }
    obs_service.get_average_rag_latency.return_value = 9.9
    alert_service.check_and_alert(admin_user_id=ADMIN_ID)
    assert notification_port.send.call_count == 2


def test_knowledge_drift_above_threshold_notifies_and_returns_true(
    alert_service, notification_port
):
    result = alert_service.process_knowledge_drift(
        {"drift_score": 0.55, "missing_items": ["A", "B", "C"]},
        admin_user_id=ADMIN_ID,
    )

    assert result is True
    kwargs = notification_port.send.call_args.kwargs
    assert kwargs["notification_type"] == "warning"
    assert kwargs["link"] == "/admin/pipeline"
    assert "55%" in kwargs["message"]
    assert "3 titres" in kwargs["message"]


def test_knowledge_drift_below_threshold_is_silent(alert_service, notification_port):
    result = alert_service.process_knowledge_drift(
        {"drift_score": 0.40, "missing_items": []},  # == threshold: strict >
        admin_user_id=ADMIN_ID,
    )
    assert result is False
    notification_port.send.assert_not_called()


def test_knowledge_drift_missing_score_defaults_to_zero(
    alert_service, notification_port
):
    assert alert_service.process_knowledge_drift({}, admin_user_id=ADMIN_ID) is False
    notification_port.send.assert_not_called()
