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
