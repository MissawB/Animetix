from unittest.mock import MagicMock

import pytest
from animetix.containers import container
from animetix.models import DuelRoom
from dependency_injector import providers
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.fixture(autouse=True)
def stub_catalog():
    """Make the duel endpoints hermetic.

    ``CreateDuelRoomView`` resolves ``catalog_service`` via DI and calls
    ``load_data(media_type)``. Without an override it hits the real singleton,
    which reads a catalog JSON from disk and caches it -- making these tests
    depend on disk data and on the singleton's (suite-order-dependent) state.
    A scoped ``providers.Object`` override returns the mock directly, bypassing
    the persistence sub-container. We scope with ``with`` (never
    ``reset_override()``) per the games conftest guidance.
    """
    cat = MagicMock()
    cat.load_data.return_value = {
        "title_to_full_data": {"Naruto": {"id": 1, "title": "Naruto"}}
    }
    with container.core.catalog_service.override(providers.Object(cat)):
        yield cat


@pytest.fixture
def user1(db):
    return User.objects.create_user(username="player1", password="password")


@pytest.fixture
def user2(db):
    return User.objects.create_user(username="player2", password="password")


@pytest.mark.django_db
def test_create_duel_room(api_client, user1):
    api_client.force_authenticate(user=user1)
    url = reverse("api_duel_create")
    response = api_client.post(url, {"media_type": "Anime"})
    assert response.status_code == 201
    assert "room_code" in response.data
    assert DuelRoom.objects.filter(room_code=response.data["room_code"]).exists()


@pytest.mark.django_db
def test_join_duel_room(api_client, user1, user2):
    # Create room
    api_client.force_authenticate(user=user1)
    url_create = reverse("api_duel_create")
    res_create = api_client.post(url_create, {"media_type": "Anime"})
    room_code = res_create.data["room_code"]

    # Join room
    api_client.force_authenticate(user=user2)
    url_join = reverse("api_duel_join")
    response = api_client.post(url_join, {"room_code": room_code})
    assert response.status_code == 200

    room = DuelRoom.objects.get(room_code=room_code)
    assert room.player2 == user2


@pytest.mark.django_db
def test_matchmaking(api_client, user1, user2):
    # User 1 starts matchmaking (creates a room)
    api_client.force_authenticate(user=user1)
    url = reverse("api_duel_matchmaking")
    res1 = api_client.post(url, {"media_type": "Anime"})
    assert res1.status_code == 201
    room_code = res1.data["room_code"]

    # User 2 starts matchmaking (joins User 1's room)
    api_client.force_authenticate(user=user2)
    res2 = api_client.post(url, {"media_type": "Anime"})
    assert res2.status_code == 200
    assert res2.data["room_code"] == room_code

    room = DuelRoom.objects.get(room_code=room_code)
    assert room.player1 == user1
    assert room.player2 == user2
