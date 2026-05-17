import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from core.domain.services.health_dashboard_service import HealthDashboardService
from core.ports.donation_port import DonationPort
from core.ports.usage_port import UsagePort

@pytest.fixture
def mock_donation_port():
    port = MagicMock(spec=DonationPort)
    port.get_total_donations.return_value = 100.0
    port.get_recent_donations.return_value = []
    return port

@pytest.fixture
def mock_usage_port():
    port = MagicMock(spec=UsagePort)
    port.get_total_cost.return_value = 200.0
    return port

def test_health_dashboard_stats(mock_donation_port, mock_usage_port):
    service = HealthDashboardService(mock_donation_port, mock_usage_port)
    stats = service.get_health_stats()
    
    assert stats["total_donations"] == 100.0
    assert stats["total_costs"] == 200.0
    assert stats["health_percentage"] == 50.0
    assert stats["is_sustainable"] is False

def test_health_dashboard_sustainability(mock_donation_port, mock_usage_port):
    mock_donation_port.get_total_donations.return_value = 300.0
    service = HealthDashboardService(mock_donation_port, mock_usage_port)
    stats = service.get_health_stats()
    
    assert stats["is_sustainable"] is True
    assert stats["health_percentage"] == 100.0 # Capped at 100
