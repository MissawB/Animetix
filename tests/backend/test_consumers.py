import pytest
from animetix_project.asgi import application
from channels.testing import WebsocketCommunicator


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


@pytest.mark.asyncio
async def test_undercover_vote_logic():
    communicator = WebsocketCommunicator(application, "/ws/undercover/ABC/")
    await communicator.connect()

    await communicator.send_json_to({"action": "vote", "voted_for": "p2"})

    response = await communicator.receive_json_from()
    assert response["type"] == "room_state"
    assert len(response["players"]) > 0

    await communicator.disconnect()
