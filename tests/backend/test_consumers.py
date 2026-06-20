import pytest
from animetix_project.asgi import application
from channels.testing import WebsocketCommunicator


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_undercover_consumer_logic():
    """Vérifie la connexion et la logique de base du salon Undercover."""
    communicator = WebsocketCommunicator(application, "/ws/undercover/ABC/")

    # 1. Test connexion
    connected, _ = await communicator.connect()
    assert connected

    # 2. Test set_name
    await communicator.send_json_to({"action": "set_name", "name": "Player 1"})

    response = await communicator.receive_json_from()
    assert response["type"] == "room_state"
    # Verification of player name based on the structure sent
    assert response["players"][0]["name"] == "Player 1"

    # 3. Test chat
    await communicator.send_json_to({"action": "chat", "message": "Hello!"})

    # Receive the broadcasted chat message
    chat_response = await communicator.receive_json_from()
    # If the consumer broadcasts state after chat, ignore it or assert both
    if chat_response["type"] == "room_state":
        chat_response = await communicator.receive_json_from()

    assert chat_response["type"] == "chat_message"
    assert chat_response["message"]["text"] == "Hello!"

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_undercover_vote_logic():
    communicator = WebsocketCommunicator(application, "/ws/undercover/ABC/")
    await communicator.connect()

    await communicator.send_json_to({"action": "vote", "voted_for": "p2"})

    response = await communicator.receive_json_from()
    assert response["type"] == "room_state"
    assert len(response["players"]) > 0

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_club_consumer_authenticated_member():
    from animetix.models import ClubMembership, DiscoveryClub
    from channels.db import database_sync_to_async
    from django.contrib.auth.models import User

    # Create user, club, membership in DB
    user = await database_sync_to_async(User.objects.create_user)(
        username="member1", password="password"
    )
    club = await database_sync_to_async(DiscoveryClub.objects.create)(
        name="Club A", description="Desc", creator=user
    )
    await database_sync_to_async(ClubMembership.objects.create)(
        user=user, club=club, role="Member"
    )

    # Setup communicator
    communicator = WebsocketCommunicator(application, f"/ws/club/{club.id}/")
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    assert connected

    # Send message
    await communicator.send_json_to({"message": "Hello members!"})

    # Wait for broadcast
    response = await communicator.receive_json_from()
    assert response["text"] == "Hello members!"
    assert response["username"] == "member1"
    assert response["type"] == "chat"
    assert int(response["club_id"]) == club.id

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_club_consumer_non_member_rejected():
    from animetix.models import DiscoveryClub
    from channels.db import database_sync_to_async
    from django.contrib.auth.models import User

    user = await database_sync_to_async(User.objects.create_user)(
        username="nonmember", password="password"
    )
    creator = await database_sync_to_async(User.objects.create_user)(
        username="creator", password="password"
    )
    club = await database_sync_to_async(DiscoveryClub.objects.create)(
        name="Club B", description="Desc", creator=creator
    )

    communicator = WebsocketCommunicator(application, f"/ws/club/{club.id}/")
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    assert not connected


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_club_consumer_anonymous_rejected():
    from animetix.models import DiscoveryClub
    from channels.db import database_sync_to_async
    from django.contrib.auth.models import AnonymousUser, User

    creator = await database_sync_to_async(User.objects.create_user)(
        username="creator2", password="password"
    )
    club = await database_sync_to_async(DiscoveryClub.objects.create)(
        name="Club C", description="Desc", creator=creator
    )

    communicator = WebsocketCommunicator(application, f"/ws/club/{club.id}/")
    communicator.scope["user"] = AnonymousUser()

    connected, _ = await communicator.connect()
    assert not connected
