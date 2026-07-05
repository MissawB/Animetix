import pytest
from animetix_project.asgi import application
from channels.testing import WebsocketCommunicator

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


async def _connect(path):
    comm = WebsocketCommunicator(application, path)
    connected, code = await comm.connect()
    await comm.disconnect()
    return connected, code


async def test_anonymous_connection_is_rejected():
    connected, code = await _connect("/ws/labs/s2s/live/")
    assert connected is False
    assert code == 4401


async def test_authenticated_no_balance_is_rejected():
    from animetix.models import Profile
    from channels.db import database_sync_to_async
    from django.contrib.auth.models import User

    user = await database_sync_to_async(User.objects.create_user)(
        username="brokeuser", password="password"
    )
    await database_sync_to_async(Profile.objects.filter(user=user).update)(
        wallet_balance=0
    )

    comm = WebsocketCommunicator(application, "/ws/labs/s2s/live/")
    comm.scope["user"] = user

    connected, code = await comm.connect()
    await comm.disconnect()

    assert connected is False
    assert code == 4402


async def test_token_in_query_string_is_not_accepted():
    # Security: a token in the URL would leak into access logs. _resolve_user must
    # ignore the query string and only accept the Sec-WebSocket-Protocol channel.
    from animetix.consumers.speech_to_speech_live import SpeechToSpeechLiveConsumer
    from django.contrib.auth.models import AnonymousUser

    consumer = SpeechToSpeechLiveConsumer()
    consumer.scope = {
        "user": AnonymousUser(),
        "query_string": b"token=some-jwt&voice_profile_id=1",
        "subprotocols": [],
    }
    assert await consumer._resolve_user() is None


async def test_bearer_subprotocol_token_is_verified():
    # The Firebase token passed as the "bearer" subprotocol is what authenticates.
    from animetix.consumers.speech_to_speech_live import SpeechToSpeechLiveConsumer
    from django.contrib.auth.models import AnonymousUser

    sentinel_user = object()

    async def _fake_verify(token):
        assert token == "jwt-123"
        return sentinel_user

    consumer = SpeechToSpeechLiveConsumer()
    consumer._verify_firebase_token = _fake_verify
    consumer.scope = {
        "user": AnonymousUser(),
        "query_string": b"",
        "subprotocols": ["bearer", "jwt-123"],
    }
    assert await consumer._resolve_user() is sentinel_user
