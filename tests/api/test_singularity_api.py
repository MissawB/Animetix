import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(api_client, db):
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_authenticate(user=user)
    return user


@pytest.mark.django_db
def test_singularity_synthesize_success(api_client, authenticated_user):
    url = "/api/v1/singularity-lab/"
    payload = {
        "action": "synthesize",
        "universe_name": "NeonGenesisX",
        "genre": "Sci-Fi",
    }

    with patch("animetix.api.labs.get_container") as mock_get_container:
        mock_container = MagicMock()
        mock_synthesizer = MagicMock()

        # Mock universe data
        universe_data = {
            "name": "NeonGenesisX",
            "genre": "Sci-Fi",
            "characters": [{"name": "Shinji"}],
            "episodes": [{"summary": "Test episode"}],
        }
        mock_synthesizer.synthesize_multiverse.return_value = universe_data
        mock_synthesizer.persist_universe_to_graph.return_value = True

        # Mock evaluation
        evaluation = {
            "is_worthy": True,
            "ai_score": 0.85,
            "community_score": 0.8,
            "reasoning": "Highly coherent.",
        }
        mock_synthesizer.evaluate_coherence_and_interest.return_value = evaluation

        mock_container.core.autonomous_domain_synthesizer.return_value = (
            mock_synthesizer
        )
        mock_get_container.return_value = mock_container

        with patch("animetix.api.labs.deduct_berrix") as mock_deduct:
            response = api_client.post(url, payload, format="json")

            assert response.status_code == 200
            assert response.data["status"] == "success"
            assert response.data["universe"]["name"] == "NeonGenesisX"
            assert response.data["evaluation"]["is_worthy"] is True
            assert response.data["persisted"] is True
            assert "synthétisé et stagé pour validation" in response.data["message"]

            # Verify calls
            mock_deduct.assert_called_once_with(
                authenticated_user, 100, "Singularity: Synthèse Multivers"
            )
            mock_synthesizer.synthesize_multiverse.assert_called_once_with(
                universe_name="NeonGenesisX", primary_genre="Sci-Fi"
            )
            mock_synthesizer.persist_universe_to_graph.assert_called_once_with(
                universe_data
            )
            mock_synthesizer.evaluate_coherence_and_interest.assert_called_once_with(
                universe_data
            )


@pytest.mark.django_db
def test_singularity_synthesize_error(api_client, authenticated_user):
    url = "/api/v1/singularity-lab/"
    payload = {"action": "synthesize", "universe_name": "NeonGenesisX"}

    with patch("animetix.api.labs.get_container") as mock_get_container:
        mock_container = MagicMock()
        mock_synthesizer = MagicMock()

        mock_synthesizer.synthesize_multiverse.side_effect = Exception(
            "Synthesis failed"
        )
        mock_container.core.autonomous_domain_synthesizer.return_value = (
            mock_synthesizer
        )
        mock_get_container.return_value = mock_container

        with patch("animetix.api.labs.deduct_berrix"):
            response = api_client.post(url, payload, format="json")

            assert response.status_code == 500
            assert response.data["error"] == "Synthesis failed"


@pytest.mark.django_db
def test_singularity_unknown_action(api_client, authenticated_user):
    url = "/api/v1/singularity-lab/"
    payload = {"action": "invalid"}
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 400
    assert response.data["error"] == "Action inconnue"
