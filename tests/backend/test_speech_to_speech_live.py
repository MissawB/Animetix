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


@pytest.mark.asyncio
@patch("google.genai.Client")
async def test_speech_to_speech_live_consumer(mock_client_class):
    # Setup mock Client and aio.live.connect
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_session = MockLiveSession()
    mock_client.aio.live.connect.return_value = mock_session

    # Establish connection via Channels test communicator
    communicator = WebsocketCommunicator(application, "/ws/labs/s2s/live/")
    connected, _ = await communicator.connect(timeout=5)
    assert connected

    # Wait for the session_ready notification from consumer.
    # Generous timeouts (default is 1s): the consumer's background gemini-session
    # task can be slow to produce output when the suite runs under load, which
    # otherwise makes this Channels test flaky.
    response = await communicator.receive_json_from(timeout=5)
    assert response["type"] == "session_ready"
    assert "connected" in response["message"]

    # Send a text message from the client
    await communicator.send_json_to({"type": "text", "data": "Hello Live Gemini"})

    # Wait for async tasks to process the input
    for _ in range(40):
        if len(mock_session.sent_inputs) > 0:
            break
        await asyncio.sleep(0.05)

    # Assert the session received the text input
    assert len(mock_session.sent_inputs) > 0
    assert mock_session.sent_inputs[0]["text"] == "Hello Live Gemini"

    # Send an audio message from the client (Base64 WAV simulation)
    # 1 second of silence, single channel, 16-bit, 16kHz
    simulated_wav_data = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    b64_audio = base64.b64encode(simulated_wav_data).decode("utf-8")

    await communicator.send_json_to({"type": "audio", "data": b64_audio})

    # Wait for audio processing
    for _ in range(40):
        if len(mock_session.sent_inputs) > 1:
            break
        await asyncio.sleep(0.05)

    # Assert the session received the audio input
    assert len(mock_session.sent_inputs) > 1
    assert "audio" in mock_session.sent_inputs[1]

    # Check that the consumer sent back audio and text chunks to the client
    # First message: text or audio chunk
    received_msg_1 = await communicator.receive_json_from(timeout=5)
    assert received_msg_1["type"] in ["audio_chunk", "text_chunk"]

    received_msg_2 = await communicator.receive_json_from(timeout=5)
    assert received_msg_2["type"] in ["audio_chunk", "text_chunk"]

    # Disconnect client
    await communicator.disconnect()

    # Wait briefly for teardown
    await asyncio.sleep(0.1)
    assert mock_session.closed
