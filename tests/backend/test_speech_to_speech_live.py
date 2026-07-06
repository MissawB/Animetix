import asyncio
import base64
from unittest.mock import MagicMock, patch

import pytest
from animetix_project.asgi import application
from channels.testing import WebsocketCommunicator


# Mock structures for testing
class MockLiveSession:
    def __init__(self):
        self.sent_inputs = []
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.closed = True

    async def send_realtime_input(self, **kwargs):
        self.sent_inputs.append(kwargs)

    async def receive(self):
        # Yield one model response containing audio and text transcript
        mock_response = MagicMock()
        mock_response.server_content = MagicMock()
        mock_response.server_content.model_turn = MagicMock()

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        # Raw 24kHz PCM simulation bytes
        mock_part.inline_data.data = b"\x00" * 480
        mock_part.inline_data.mime_type = "audio/pcm"
        mock_part.text = None

        mock_response.server_content.model_turn.parts = [mock_part]
        mock_response.server_content.output_transcription = "Simulation de réponse"

        yield mock_response

        # Idle/sleep to keep the task alive until cancel
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass


@pytest.fixture
def _mock_voice_cloning():
    """Override the heavy ``voice_cloning_service`` Singleton with a mock.

    The consumer eagerly instantiates ``container.core.voice_cloning_service()`` on
    every connection (before it emits ``session_ready``), which transitively builds
    the real ``inference_engine`` + LNN simulator. Whether that Singleton is already
    cached depends on suite ordering, so the first response could take far longer
    than the 5s ``receive_json_from`` timeout -- the source of this test's flakiness.
    Mocking it keeps the handshake instant and deterministic (the cloning path is
    never exercised here anyway: no voice_profile_id is provided).
    """
    from animetix.containers import container
    from dependency_injector import providers

    with container.core.voice_cloning_service.override(providers.Object(MagicMock())):
        yield


async def _wait_until(predicate, timeout=10.0, interval=0.05):
    """Poll ``predicate`` until true or ``timeout`` elapses (returns the result).

    A wall-clock budget rather than a fixed iteration count: when the whole suite
    runs the shared event loop is contended, so the consumer's ``receive()`` handler
    can be scheduled noticeably later than in an isolated run. The generous budget
    only costs extra time on genuine failure, never on the happy path.
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return predicate()


# transaction=True: the ASGI auth-middleware stack and the consumer resolve scope
# data through the DB across the channels thread executor. Without the django_db
# mark that access raises "Database access not allowed" from the background task --
# in isolation the task is cancelled before it gets there, so the failure only
# surfaced under the full-suite ordering (the historical flakiness). transaction=True
# (vs the transactional wrapper) is what lets the executor thread see the same DB.
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@patch(
    "animetix.consumers.speech_to_speech_live.process_client_audio",
    return_value=b"\x00" * 320,
)
@patch("google.genai.Client")
async def test_speech_to_speech_live_consumer(
    mock_client_class, mock_process_audio, _mock_voice_cloning, monkeypatch
):
    # Deterministic client path: force the API-key branch so a leaked/cleared
    # GEMINI_API_KEY from an earlier test can't push the consumer onto the Vertex
    # branch (both branches resolve to the same mock, but this keeps the log/flow
    # stable and documents intent).
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-s2s")

    # Setup mock Client and aio.live.connect
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_session = MockLiveSession()
    mock_client.aio.live.connect.return_value = mock_session

    # The consumer now requires an authenticated, funded user (auth + flat Bx
    # charge). Create one and attach it to the WS scope (session-auth path).
    from animetix.models import Profile
    from channels.db import database_sync_to_async
    from django.contrib.auth.models import User

    user = await database_sync_to_async(User.objects.create_user)(
        username="s2s-e2e-user", password="pw"
    )
    await database_sync_to_async(Profile.objects.filter(user=user).update)(
        wallet_balance=1000
    )

    # Establish connection via Channels test communicator
    communicator = WebsocketCommunicator(application, "/ws/labs/s2s/live/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect(timeout=10)
    assert connected

    # Wait for the session_ready notification from the consumer's background task.
    response = await communicator.receive_json_from(timeout=10)
    assert response["type"] == "session_ready"
    assert "connected" in response["message"]

    # Send a text message from the client
    await communicator.send_json_to({"type": "text", "data": "Hello Live Gemini"})

    # Wait for the consumer's receive() handler to forward it to the (mock) session.
    assert await _wait_until(lambda: len(mock_session.sent_inputs) > 0)
    assert mock_session.sent_inputs[0]["text"] == "Hello Live Gemini"

    # Send an audio message from the client (Base64 WAV simulation). The consumer's
    # process_client_audio is mocked above so the path doesn't depend on ffmpeg/pydub.
    simulated_wav_data = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    b64_audio = base64.b64encode(simulated_wav_data).decode("utf-8")

    await communicator.send_json_to({"type": "audio", "data": b64_audio})

    # Wait for the audio input to be forwarded to the session.
    assert await _wait_until(lambda: len(mock_session.sent_inputs) > 1)
    assert "audio" in mock_session.sent_inputs[1]

    # Check that the consumer sent back audio and text chunks to the client
    received_msg_1 = await communicator.receive_json_from(timeout=10)
    assert received_msg_1["type"] in ["audio_chunk", "text_chunk"]

    received_msg_2 = await communicator.receive_json_from(timeout=10)
    assert received_msg_2["type"] in ["audio_chunk", "text_chunk"]

    # Disconnect client
    await communicator.disconnect()

    # Wait for the background task's async-context teardown to run.
    assert await _wait_until(lambda: mock_session.closed, timeout=5)
