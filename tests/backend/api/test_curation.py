import pytest
from animetix.models import DataCurationTicket
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", password="password", email="admin@example.com"
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(username="user", password="password")


@pytest.fixture
def curation_tickets(db):
    DataCurationTicket.objects.create(
        item_title="Anime 1",
        issue_description="Contradiction in release year",
        source_pg={"year": 2000},
        source_neo4j={"year": 2001},
        is_resolved=False,
    )
    DataCurationTicket.objects.create(
        item_title="Anime 2", issue_description="Duplicate characters", is_resolved=True
    )
    return DataCurationTicket.objects.all()


@pytest.mark.django_db
def test_curation_dashboard_access_denied(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)
    url = reverse("curation-list")
    response = api_client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_curation_dashboard_stats(api_client, admin_user, curation_tickets):
    api_client.force_authenticate(user=admin_user)
    url = reverse("curation-stats")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["total_tickets"] == 2
    assert response.data["pending_tickets"] == 1
    assert response.data["resolved_tickets"] == 1
    assert response.data["health_score"] == 50.0


@pytest.mark.django_db
def test_curation_resolve_ticket(api_client, admin_user, curation_tickets):
    api_client.force_authenticate(user=admin_user)
    ticket = curation_tickets.filter(is_resolved=False).first()
    url = reverse("curation-resolve", args=[ticket.id])
    response = api_client.post(url)
    assert response.status_code == 200

    ticket.refresh_from_db()
    assert ticket.is_resolved is True
