from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


class MockCovertestState:
    def __init__(self):
        self.secret = None
        self.url = None
        self.locale = None
        self.volume = None
        self.guesses = []
        self.game_over = False
        self.is_daily = False


class MockParadoxState:
    def __init__(self):
        self.answer = None
        self.options = []
        self.reasoning = None
        self.scenario = None
        self.media = "Anime"
        self.is_daily = False
        self.game_over = False


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_catalog():
    return {
        "title_to_full_data": {
            "Naruto": {
                "id": 1,
                "title": "Naruto",
                "description": "Ninja anime",
                "image": "http://img.jpg",
                "title_english": "Naruto EN",
                "title_native": "Naruto JP",
            },
            "One Piece": {
                "id": 2,
                "title": "One Piece",
                "description": "Pirate anime",
                "image": "http://img2.jpg",
            },
            "Bleach": {
                "id": 3,
                "title": "Bleach",
                "description": "Soul reaper anime",
                "image": "http://img3.jpg",
            },
        },
        "titles": ["Naruto", "One Piece", "Bleach"],
        "title_to_index": {
            "Naruto": 1,
            "One Piece": 2,
            "Bleach": 3,
        },
        "lookup": [
            {"id": 1, "title": "Naruto"},
            {"id": 2, "title": "One Piece"},
            {"id": 3, "title": "Bleach"},
        ],
    }


@pytest.mark.django_db
def test_emoji_game_state_auto_start(api_client, mock_catalog):
    mock_cat_service = MagicMock()
    mock_cat_service.load_data.return_value = mock_catalog

    mock_em_service = MagicMock()
    mock_em_service.select_secret.return_value = "Naruto"
    mock_em_service.generate_emojis.return_value = ["🦊", "🍥"]

    with (
        container.core.catalog_service.override(providers.Object(mock_cat_service)),
        container.core.emoji_service.override(providers.Object(mock_em_service)),
    ):

        url = reverse("api_emoji_state")
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["emojis"] == ["🦊", "🍥"]
        assert data["media_type"] == "Anime"
        assert data["guesses"] == []
        assert data["game_over"] is False


@pytest.mark.django_db
def test_covertest_game_state_auto_start(api_client, mock_catalog):
    mock_cat_service = MagicMock()
    mock_cat_service.load_data.return_value = mock_catalog

    state = MockCovertestState()
    mock_ct_service = MagicMock()
    mock_ct_service.get_state.return_value = state
    mock_ct_service.get_random_cover.return_value = {
        "manga_title": "Naruto",
        "url": "http://cover.jpg",
        "locale": "fr",
        "volume": "1",
    }

    with (
        container.core.catalog_service.override(providers.Object(mock_cat_service)),
        container.core.cover_test_service.override(providers.Object(mock_ct_service)),
    ):

        url = reverse("api_covertest_state")
        response = api_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["cover_url"] == "http://cover.jpg"
        assert data["locale"] == "fr"
        assert data["volume"] == "1"
        assert data["guesses"] == []
        assert data["game_over"] is False


@pytest.mark.django_db
def test_paradox_game_state_and_guess(api_client, mock_catalog):
    mock_cat_service = MagicMock()
    mock_cat_service.load_data.return_value = mock_catalog

    state = MockParadoxState()
    state.answer = "Naruto"
    state.options = ["Naruto", "One Piece", "Bleach"]
    state.reasoning = "Because ninja"
    state.scenario = "Spot the intruder"

    mock_px_service = MagicMock()
    mock_px_service.get_state.return_value = state

    with (
        container.core.catalog_service.override(providers.Object(mock_cat_service)),
        container.core.paradox_service.override(providers.Object(mock_px_service)),
    ):

        url_state = reverse("api_paradox_state")
        response = api_client.get(url_state)
        assert response.status_code == 200
        data = response.json()
        assert data["scenario"] == "Spot the intruder"
        assert len(data["items"]) == 3
        assert data["items"][0]["title"] == "Naruto"
        assert data["items"][0]["id"] == 1

        url_guess = reverse("api_paradox_guess")
        guess_data = {"intruder_id": 1}
        response = api_client.post(url_guess, guess_data, format="json")
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["is_correct"] is True
        assert res_data["answer"] == "Naruto"


@pytest.mark.django_db
def test_routed_urls_exist(api_client):
    user = User.objects.create_user(username="test_user", password="password")
    api_client.force_authenticate(user=user)

    url = reverse("api_social_dashboard")
    response = api_client.get(url)
    assert response.status_code != 404

    url = reverse("api_social_toggle_follow", kwargs={"pk": user.pk})
    response = api_client.post(url)
    assert response.status_code != 404

    url = reverse("submit_ai_feedback")
    response = api_client.get(url)
    assert response.status_code != 404

    url = reverse("mlops_eval_failures")
    response = api_client.get(url)
    assert response.status_code != 404

    url = reverse("mlops_gold_dataset_list")
    response = api_client.get(url)
    assert response.status_code != 404

    url = reverse("admin_ai_eval_data")
    response = api_client.get(url)
    assert response.status_code != 404
