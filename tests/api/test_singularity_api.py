from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
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


@pytest.mark.django_db
def test_singularity_lab_get_unified_state(api_client, authenticated_user):
    import numpy as np

    url = "/api/v1/singularity-lab/"

    with patch("animetix.api.labs.get_container") as mock_get_container:
        mock_container = MagicMock()
        mock_plasticity = MagicMock()
        mock_drift = MagicMock()

        mock_plasticity.W = np.zeros((10, 10))
        mock_plasticity.tau_plus = 20.0
        mock_plasticity.tau_minus = 20.0
        mock_plasticity.num_concepts = 10

        mock_drift_config = MagicMock()
        mock_drift_config.archetype_id = "shonen_hero"
        mock_drift_config.primary_accent = "#FD7706"
        mock_drift_config.aura_type = "none"
        mock_drift_config.aura_intensity = 0.0
        mock_drift_config.font_vibe = "default"

        mock_drift.calculate_drift.return_value = mock_drift_config

        mock_container.core.synaptic_plasticity_simulator.return_value = mock_plasticity
        mock_container.core.archetype_drift_service.return_value = mock_drift
        mock_get_container.return_value = mock_container

        response = api_client.get(url)
        assert response.status_code == 200
        assert "weights" in response.data
        assert "plasticity_config" in response.data
        assert "personalization_settings" in response.data
        assert response.data["current_archetype"]["id"] == "shonen_hero"


@pytest.mark.django_db
def test_singularity_lab_update_config(api_client, authenticated_user):
    import numpy as np

    url = "/api/v1/singularity-lab/"
    payload = {
        "action": "update_config",
        "tau_plus": 35.0,
        "tau_minus": 15.0,
        "mode": "manual",
        "manual_archetype": "cyberpunk_rebel",
        "intensity_multiplier": 1.5,
        "features": {"aura": True, "font": False, "accent": True},
    }

    # Verify profile exists
    profile = authenticated_user.profile

    with patch("animetix.api.labs.get_container") as mock_get_container:
        mock_container = MagicMock()
        mock_plasticity = MagicMock()
        mock_drift = MagicMock()

        mock_plasticity.W = np.zeros((10, 10))
        mock_plasticity.tau_plus = 20.0
        mock_plasticity.tau_minus = 20.0
        mock_plasticity.num_concepts = 10

        mock_drift_config = MagicMock()
        mock_drift_config.archetype_id = "cyberpunk_rebel"
        mock_drift_config.primary_accent = "#FF00FF"
        mock_drift_config.aura_type = "electric"
        mock_drift_config.aura_intensity = 1.5
        mock_drift_config.font_vibe = "cyber"

        mock_drift.calculate_drift.return_value = mock_drift_config

        mock_container.core.synaptic_plasticity_simulator.return_value = mock_plasticity
        mock_container.core.archetype_drift_service.return_value = mock_drift
        mock_get_container.return_value = mock_container

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200

        # Verify plasticity mock parameters were set
        assert mock_plasticity.tau_plus == 35.0
        assert mock_plasticity.tau_minus == 15.0

        # Verify profile settings updated in DB
        profile.refresh_from_db()
        assert profile.personalization_settings["mode"] == "manual"
        assert profile.personalization_settings["manual_archetype"] == "cyberpunk_rebel"
        assert profile.personalization_settings["intensity_multiplier"] == 1.5
        assert profile.personalization_settings["features"]["font"] is False
