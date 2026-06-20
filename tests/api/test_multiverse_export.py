import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(api_client, db):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_authenticate(user=user)
    return user


@pytest.mark.django_db
def test_multiverse_export_pdf_success(api_client, authenticated_user, mock_container):
    # Mock Neo4j queries:
    # 1. Universe query
    # 2. Characters query
    # 3. Relations query
    mock_container.graph_persistence_port.execute_query.side_effect = [
        [
            {
                "media": {
                    "name": "Synthetic One Piece",
                    "description": "Pirates and oceans",
                    "cosmology": "Devil fruits",
                },
                "genre": {"name": "Shonen"},
            }
        ],
        [
            {
                "character": {
                    "name": "Luffy",
                    "role": "Protagonist",
                    "power_level": 9000,
                }
            }
        ],
        [
            {
                "rel_type": "PRODUCED_BY",
                "labels": ["Studio"],
                "properties": {"name": "Toei Animation"},
                "is_outgoing": True,
            }
        ],
    ]

    with container.persistence.graph_persistence_port.override(
        providers.Object(mock_container.graph_persistence_port)
    ):
        url = reverse("api_multiverse_export_pdf", args=["Synthetic One Piece"])
        response = api_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "attachment;" in response["Content-Disposition"]
        assert "wiki_Synthetic_One_Piece.pdf" in response["Content-Disposition"]

        # Verify content starts with PDF signature
        pdf_content = b"".join(response.streaming_content)
        assert pdf_content.startswith(b"%PDF")


@pytest.mark.django_db
def test_multiverse_export_pdf_not_found(
    api_client, authenticated_user, mock_container
):
    # Mock Neo4j query returning empty for non-existent universe
    mock_container.graph_persistence_port.execute_query.return_value = []

    with container.persistence.graph_persistence_port.override(
        providers.Object(mock_container.graph_persistence_port)
    ):
        url = reverse("api_multiverse_export_pdf", args=["Nonexistent"])
        response = api_client.get(url)

        assert response.status_code == 404
