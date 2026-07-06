"""Real-behavior unit tests for the Speech-to-Speech Live consumer module.

Complements ``tests/backend/test_speech_to_speech_live.py`` (an end-to-end
Channels ``WebsocketCommunicator`` flow) with focused, deterministic unit
tests:

* The pure audio helpers ``pcm_to_wav`` / ``process_client_audio`` are asserted
  against real byte buffers built/parsed with the stdlib ``wave`` module — exact
  output length, WAV header fields, resampling math, format conversions and
  edge cases (empty / odd-length / non-WAV input).
* The ``SpeechToSpeechLiveConsumer`` async methods are driven directly (no live
  server) with ``self.send`` / ``self.accept`` / ``self.close`` mocked and the
  Gemini live session replaced by an in-memory async-context-manager mock. We
  assert the consumer forwards the *processed* (16 kHz mono PCM) bytes, routes
  text vs audio correctly, emits the ``session_ready`` handshake, and tears the
  background task down on disconnect — verifying real outcomes, not bare calls.

No real Gemini / network / audio hardware is touched.
"""

import asyncio
import audioop
import base64
import io
import json
import struct
import wave
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from animetix.consumers import speech_to_speech_live as s2s

# --------------------------------------------------------------------------- #
# Helpers to build/parse real WAV buffers
# --------------------------------------------------------------------------- #


def _make_wav(pcm: bytes, *, rate: int, channels: int, width: int) -> bytes:
    """Wrap raw PCM in a real WAV container using the stdlib."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _wav_params(wav_bytes: bytes):
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        return w.getparams(), w.readframes(w.getnframes())


# A deterministic 16-bit mono sample buffer (20 frames of a small ramp).
_RAMP_16K_MONO = struct.pack("<20h", *range(0, 20))


# --------------------------------------------------------------------------- #
# pcm_to_wav
# --------------------------------------------------------------------------- #


def test_pcm_to_wav_roundtrips_and_preserves_payload():
    """WAV output must be parseable and yield back the exact PCM payload."""
    pcm = _RAMP_16K_MONO
    out = s2s.pcm_to_wav(pcm)  # defaults: 24kHz, mono, 16-bit

    params, frames = _wav_params(out)
    assert frames == pcm  # payload preserved byte-for-byte
    assert params.framerate == 24000
    assert params.nchannels == 1
    assert params.sampwidth == 2
    # 24kHz / mono / 16-bit -> 20 frames
    assert params.nframes == len(pcm) // 2


def test_pcm_to_wav_header_is_riff_wave_and_correct_length():
    """The container must start with a RIFF/WAVE header sized for the payload."""
    pcm = b"\x01\x02" * 50  # 100 bytes
    out = s2s.pcm_to_wav(pcm)

    assert out[:4] == b"RIFF"
    assert out[8:12] == b"WAVE"
    # Standard 44-byte canonical WAV header + payload.
    assert len(out) == 44 + len(pcm)
    # RIFF chunk size field = total file size - 8.
    riff_size = struct.unpack("<I", out[4:8])[0]
    assert riff_size == len(out) - 8


@pytest.mark.parametrize(
    "rate,channels,width",
    [(16000, 1, 2), (24000, 1, 2), (48000, 2, 2), (8000, 1, 1)],
)
def test_pcm_to_wav_respects_format_args(rate, channels, width):
    pcm = b"\x00" * (channels * width * 10)  # 10 frames
    out = s2s.pcm_to_wav(pcm, sample_rate=rate, channels=channels, sample_width=width)
    params, frames = _wav_params(out)
    assert params.framerate == rate
    assert params.nchannels == channels
    assert params.sampwidth == width
    assert params.nframes == 10
    assert frames == pcm


def test_pcm_to_wav_empty_payload_still_valid_header():
    out = s2s.pcm_to_wav(b"")
    params, frames = _wav_params(out)
    assert frames == b""
    assert params.nframes == 0
    assert len(out) == 44  # header only


# --------------------------------------------------------------------------- #
# process_client_audio  — native wave/audioop path
# --------------------------------------------------------------------------- #


def test_process_client_audio_passthrough_16k_mono_16bit():
    """Already-canonical input returns raw frames untouched (no resample)."""
    pcm = _RAMP_16K_MONO
    wav = _make_wav(pcm, rate=16000, channels=1, width=2)

    out = s2s.process_client_audio(wav)

    assert out == pcm  # exact passthrough


def test_process_client_audio_downmixes_stereo_to_mono():
    """Stereo 16k/16-bit input is averaged to mono with preserved length math."""
    # 5 stereo frames: L,R interleaved 16-bit. tomono(L=1,R=1) averages channels.
    frames = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # 5 (L,R) pairs
    stereo_pcm = struct.pack("<10h", *frames)
    wav = _make_wav(stereo_pcm, rate=16000, channels=2, width=2)

    out = s2s.process_client_audio(wav)

    # Reference: stdlib audioop.tomono with equal weights -> mono.
    expected = audioop.tomono(stereo_pcm, 2, 1, 1)
    assert out == expected
    # 5 mono 16-bit frames -> 10 bytes.
    assert len(out) == 10


def test_process_client_audio_widens_8bit_to_16bit():
    """8-bit (sampwidth 1) input is converted up to 16-bit at 16kHz mono."""
    pcm8 = bytes(range(0, 20))  # 20 frames of 8-bit mono
    wav = _make_wav(pcm8, rate=16000, channels=1, width=1)

    out = s2s.process_client_audio(wav)

    expected = audioop.lin2lin(pcm8, 1, 2)
    assert out == expected
    assert len(out) == 2 * len(pcm8)  # width doubled


def test_process_client_audio_resamples_8k_to_16k():
    """8kHz mono input is upsampled to 16kHz, roughly doubling frame count."""
    pcm = struct.pack("<40h", *range(40))  # 40 frames @ 8kHz
    wav = _make_wav(pcm, rate=8000, channels=1, width=2)

    out = s2s.process_client_audio(wav)

    # Reference resample with the same single-shot ratecv call the module uses.
    expected, _ = audioop.ratecv(pcm, 2, 1, 8000, 16000, None)
    assert out == expected
    # Upsampling 8k->16k ~doubles the number of 16-bit frames.
    assert len(out) == len(expected)
    assert abs(len(out) - 2 * len(pcm)) <= 8  # within a small ratecv boundary slop


def test_process_client_audio_empty_input_raises_value_error():
    """Empty buffer is neither valid WAV nor decodable -> ValueError fallback."""
    with pytest.raises(ValueError):
        s2s.process_client_audio(b"")


def test_process_client_audio_garbage_input_raises_value_error():
    """Non-WAV/non-decodable bytes fall through both paths to a ValueError."""
    with pytest.raises(ValueError):
        s2s.process_client_audio(b"not-a-wav-file-at-all")


def test_process_client_audio_odd_length_raw_pcm_raises():
    """An odd-length non-WAV buffer cannot be parsed and surfaces ValueError."""
    with pytest.raises(ValueError):
        s2s.process_client_audio(b"\x01\x02\x03")  # 3 bytes, no RIFF header


# --------------------------------------------------------------------------- #
# Consumer fixtures / helpers
# --------------------------------------------------------------------------- #


class FakeLiveSession:
    """In-memory stand-in for a Gemini live session (async-context-manager)."""

    def __init__(self):
        self.sent = []  # list of kwargs passed to send_realtime_input
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, *exc):
        self.exited = True
        return False

    async def send_realtime_input(self, **kwargs):
        self.sent.append(kwargs)

    async def receive(self):
        # No model turns; idle until cancelled so run_gemini_session stays alive.
        if False:  # pragma: no cover - makes this an async generator
            yield None
        await asyncio.sleep(3600)


def _make_consumer(query_string=b""):
    """Instantiate the consumer with async I/O mocked and a fake live session."""
    consumer = s2s.SpeechToSpeechLiveConsumer()
    authed_user = MagicMock()
    authed_user.is_authenticated = True
    authed_user.id = 1
    consumer.scope = {
        "type": "websocket",
        "query_string": query_string,
        "user": authed_user,
        "subprotocols": [],
    }
    consumer.accept = AsyncMock()
    consumer.send = AsyncMock()
    consumer.close = AsyncMock()
    # Auth + billing are covered end-to-end in test_s2s_live_security.py; here we
    # bypass the flat Bx charge and the 10-min deadline so connect() reaches its
    # state-init path deterministically without a real wallet or a 600s task.
    consumer._charge_session = AsyncMock(return_value=True)
    consumer._enforce_deadline = AsyncMock()
    return consumer


# --------------------------------------------------------------------------- #
# connect  /  query-param parsing
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_connect_accepts_and_initializes_state():
    consumer = _make_consumer()
    # Stop run_gemini_session from doing real work; just record that it's spawned.
    with patch.object(consumer, "run_gemini_session", new=AsyncMock()):
        await consumer.connect()

    consumer.accept.assert_awaited_once()
    assert consumer.client_connected is True
    assert consumer.gemini_session is None
    assert consumer.voice_profile_id is None
    assert consumer.receiver_task is not None
    # Clean up the spawned background task.
    consumer.client_connected = False
    consumer.receiver_task.cancel()
    try:
        await consumer.receiver_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_connect_parses_voice_profile_id_from_query():
    consumer = _make_consumer(query_string=b"voice_profile_id=42&x=1")
    with patch.object(consumer, "run_gemini_session", new=AsyncMock()):
        await consumer.connect()
    assert consumer.voice_profile_id == 42
    consumer.receiver_task.cancel()


@pytest.mark.asyncio
async def test_connect_ignores_non_numeric_profile_id():
    consumer = _make_consumer(query_string=b"voice_profile_id=abc")
    with patch.object(consumer, "run_gemini_session", new=AsyncMock()):
        await consumer.connect()
    assert consumer.voice_profile_id is None
    consumer.receiver_task.cancel()


# --------------------------------------------------------------------------- #
# receive  — routing of text vs audio
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_receive_text_forwards_to_session():
    consumer = _make_consumer()
    consumer.gemini_session = FakeLiveSession()

    await consumer.receive(text_data=json.dumps({"type": "text", "data": "hi there"}))

    assert consumer.gemini_session.sent == [{"text": "hi there"}]


@pytest.mark.asyncio
async def test_receive_text_audio_forwards_processed_pcm():
    """A base64 WAV in a text 'audio' message is decoded, processed, and the
    *processed 16k mono PCM* (not the original WAV) is forwarded as a Blob."""
    consumer = _make_consumer()
    consumer.gemini_session = FakeLiveSession()

    pcm = _RAMP_16K_MONO
    wav = _make_wav(pcm, rate=16000, channels=1, width=2)
    b64 = base64.b64encode(wav).decode()

    await consumer.receive(text_data=json.dumps({"type": "audio", "data": b64}))

    assert len(consumer.gemini_session.sent) == 1
    blob = consumer.gemini_session.sent[0]["audio"]
    assert blob.data == pcm  # processed passthrough, not the WAV bytes
    assert blob.data != wav
    assert blob.mime_type == "audio/pcm;rate=16000"


@pytest.mark.asyncio
async def test_receive_binary_audio_forwards_processed_pcm():
    consumer = _make_consumer()
    consumer.gemini_session = FakeLiveSession()

    pcm = struct.pack("<10h", *range(10))
    wav = _make_wav(pcm, rate=16000, channels=1, width=2)

    await consumer.receive(bytes_data=wav)

    assert len(consumer.gemini_session.sent) == 1
    blob = consumer.gemini_session.sent[0]["audio"]
    assert blob.data == pcm
    assert blob.mime_type == "audio/pcm;rate=16000"


@pytest.mark.asyncio
async def test_receive_binary_resampled_audio_forwards_16k():
    """Binary 8kHz WAV is upsampled to 16k PCM before being forwarded."""
    consumer = _make_consumer()
    consumer.gemini_session = FakeLiveSession()

    pcm = struct.pack("<40h", *range(40))
    wav = _make_wav(pcm, rate=8000, channels=1, width=2)

    await consumer.receive(bytes_data=wav)

    expected, _ = audioop.ratecv(pcm, 2, 1, 8000, 16000, None)
    blob = consumer.gemini_session.sent[0]["audio"]
    assert blob.data == expected


@pytest.mark.asyncio
async def test_receive_without_session_is_noop():
    """No live session yet -> messages are dropped, no crash."""
    consumer = _make_consumer()
    consumer.gemini_session = None
    # Both branches must be harmless.
    await consumer.receive(text_data=json.dumps({"type": "text", "data": "x"}))
    await consumer.receive(
        bytes_data=_make_wav(_RAMP_16K_MONO, rate=16000, channels=1, width=2)
    )
    # send is never called as a side effect here.
    consumer.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_receive_bad_audio_is_swallowed():
    """A processing error during binary audio is caught (logged, not raised)."""
    consumer = _make_consumer()
    session = FakeLiveSession()
    consumer.gemini_session = session

    await consumer.receive(bytes_data=b"not-a-wav")  # process_client_audio raises

    assert session.sent == []  # nothing forwarded


@pytest.mark.asyncio
async def test_receive_invalid_json_text_is_swallowed():
    consumer = _make_consumer()
    consumer.gemini_session = FakeLiveSession()
    # Malformed JSON must be caught inside receive, not propagate.
    await consumer.receive(text_data="{not json")
    assert consumer.gemini_session.sent == []


# --------------------------------------------------------------------------- #
# run_gemini_session  — handshake + voice-profile config
# --------------------------------------------------------------------------- #


def _patch_container(monkeypatch):
    """Patch animetix.containers.get_container used inside run_gemini_session."""
    fake_container = MagicMock()
    fake_container.core.voice_cloning_service.return_value = MagicMock()
    import animetix.containers as containers_mod

    monkeypatch.setattr(containers_mod, "get_container", lambda: fake_container)
    return fake_container


@pytest.mark.asyncio
async def test_run_gemini_session_emits_session_ready(monkeypatch):
    """The session handshake sends a 'session_ready' message to the client."""
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.gemini_session = None
    consumer.voice_profile_id = None

    _patch_container(monkeypatch)

    session = FakeLiveSession()

    # genai.Client().aio.live.connect(...) returns our async-ctx session.
    fake_client = MagicMock()
    fake_client.aio.live.connect.return_value = session

    with patch.object(s2s.genai, "Client", return_value=fake_client):
        task = asyncio.create_task(consumer.run_gemini_session())
        # Let it reach the `async for response in session.receive()` idle point.
        for _ in range(50):
            if consumer.gemini_session is session:
                break
            await asyncio.sleep(0.02)
        consumer.client_connected = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # The client was built and connect() called with AUDIO modality (no profile).
    assert consumer.gemini_session is session
    _, kwargs = fake_client.aio.live.connect.call_args
    assert kwargs["config"]["response_modalities"] == ["AUDIO"]

    sent = [json.loads(c.args[0]) for c in consumer.send.await_args_list]
    assert any(m["type"] == "session_ready" for m in sent)


@pytest.mark.asyncio
async def test_run_gemini_session_uses_text_modality_with_voice_profile(monkeypatch):
    """When a voice profile is present, Gemini is configured for TEXT responses
    and the system prompt embeds the character name."""
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.gemini_session = None
    consumer.voice_profile_id = 7

    _patch_container(monkeypatch)

    session = FakeLiveSession()
    fake_client = MagicMock()
    fake_client.aio.live.connect.return_value = session

    profile = {
        "name": "Naruto",
        "language": "en",
        "roles": "ninja, hero",
        "sample_url": "http://x/sample.wav",
        "sample_file_path": None,
    }

    with (
        patch.object(s2s.genai, "Client", return_value=fake_client),
        patch.object(
            consumer, "get_voice_profile_data", new=AsyncMock(return_value=profile)
        ),
    ):
        task = asyncio.create_task(consumer.run_gemini_session())
        for _ in range(50):
            if consumer.gemini_session is session:
                break
            await asyncio.sleep(0.02)
        consumer.client_connected = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    _, kwargs = fake_client.aio.live.connect.call_args
    cfg = kwargs["config"]
    assert cfg["response_modalities"] == ["TEXT"]
    prompt_text = cfg["system_instruction"]["parts"][0]["text"]
    assert "Naruto" in prompt_text
    assert "ninja, hero" in prompt_text


@pytest.mark.asyncio
async def test_run_gemini_session_reports_error_and_closes(monkeypatch):
    """A connection failure is surfaced to the client as an 'error' message and
    the socket is closed."""
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.gemini_session = None
    consumer.voice_profile_id = None

    _patch_container(monkeypatch)

    fake_client = MagicMock()
    fake_client.aio.live.connect.side_effect = RuntimeError("connect boom")

    with patch.object(s2s.genai, "Client", return_value=fake_client):
        await consumer.run_gemini_session()

    sent = [json.loads(c.args[0]) for c in consumer.send.await_args_list]
    err = [m for m in sent if m["type"] == "error"]
    assert err and "connect boom" in err[0]["message"]
    consumer.close.assert_awaited_once()


# --------------------------------------------------------------------------- #
# run_gemini_session  — server response handling loop
# --------------------------------------------------------------------------- #


def _model_response(
    *, audio_pcm=None, text=None, transcription=None, turn_complete=False
):
    """Build a MagicMock shaped like a Gemini live ``response`` object."""
    resp = MagicMock()
    sc = resp.server_content

    if audio_pcm is None and text is None:
        sc.model_turn = None
    else:
        part = MagicMock()
        if audio_pcm is not None:
            part.inline_data = MagicMock()
            part.inline_data.data = audio_pcm
        else:
            part.inline_data = None
        part.text = text
        sc.model_turn.parts = [part]

    sc.output_transcription = transcription
    sc.turn_complete = turn_complete
    return resp


class ScriptedLiveSession(FakeLiveSession):
    """Live session that yields a fixed list of responses then idles."""

    def __init__(self, responses):
        super().__init__()
        self._responses = responses

    async def receive(self):
        for r in self._responses:
            yield r
        await asyncio.sleep(3600)


async def _drive_session(consumer, fake_client, *, settle=0.15):
    """Run run_gemini_session until the response loop has been pumped, then cancel."""
    with patch.object(s2s.genai, "Client", return_value=fake_client):
        task = asyncio.create_task(consumer.run_gemini_session())
        await asyncio.sleep(settle)
        consumer.client_connected = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_run_gemini_session_emits_audio_and_text_chunks(monkeypatch):
    """Inline audio is wrapped to WAV/base64 and text parts are streamed back."""
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.gemini_session = None
    consumer.voice_profile_id = None
    _patch_container(monkeypatch)

    pcm = b"\x00\x01" * 240  # raw 24kHz PCM chunk
    responses = [
        _model_response(audio_pcm=pcm),
        _model_response(text="Hello "),
        _model_response(text="world", turn_complete=True),
    ]
    session = ScriptedLiveSession(responses)
    fake_client = MagicMock()
    fake_client.aio.live.connect.return_value = session

    await _drive_session(consumer, fake_client)

    sent = [json.loads(c.args[0]) for c in consumer.send.await_args_list]
    audio_msgs = [m for m in sent if m["type"] == "audio_chunk"]
    text_msgs = [m for m in sent if m["type"] == "text_chunk"]

    assert audio_msgs, "expected an audio_chunk message"
    assert audio_msgs[0]["mime_type"] == "audio/wav"
    # The forwarded audio decodes to a valid WAV whose payload is the raw PCM.
    wav_bytes = base64.b64decode(audio_msgs[0]["audio"])
    _, frames = _wav_params(wav_bytes)
    assert frames == pcm

    assert [m["text"] for m in text_msgs] == ["Hello ", "world"]


@pytest.mark.asyncio
async def test_run_gemini_session_streams_output_transcription(monkeypatch):
    """``output_transcription`` is forwarded as a text_chunk."""
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.gemini_session = None
    consumer.voice_profile_id = None
    _patch_container(monkeypatch)

    session = ScriptedLiveSession([_model_response(transcription="transcribed text")])
    fake_client = MagicMock()
    fake_client.aio.live.connect.return_value = session

    await _drive_session(consumer, fake_client)

    sent = [json.loads(c.args[0]) for c in consumer.send.await_args_list]
    texts = [m["text"] for m in sent if m["type"] == "text_chunk"]
    assert any("transcribed text" in t for t in texts)


@pytest.mark.asyncio
async def test_run_gemini_session_clones_voice_on_turn_complete(monkeypatch):
    """With a voice profile + accumulated text, turn_complete triggers the
    voice-cloning service and the cloned audio is sent to the client."""
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.gemini_session = None
    consumer.voice_profile_id = 7

    container = _patch_container(monkeypatch)
    cloning = container.core.voice_cloning_service.return_value
    cloning.clone.return_value = b"CLONED-AUDIO-BYTES"

    profile = {
        "name": "Luffy",
        "language": "en",
        "roles": "captain",
        "sample_url": "http://x/s.wav",
        "sample_file_path": None,
    }

    session = ScriptedLiveSession([_model_response(text="ahoy", turn_complete=True)])
    fake_client = MagicMock()
    fake_client.aio.live.connect.return_value = session

    # Profile present but no local file -> falls back to safe_http_request download.
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.content = b"REF-AUDIO"

    with (
        patch.object(
            consumer, "get_voice_profile_data", new=AsyncMock(return_value=profile)
        ),
        patch("core.utils.security.safe_http_request", return_value=fake_resp),
    ):
        await _drive_session(consumer, fake_client, settle=0.25)

    cloning.clone.assert_called_once()
    # The accumulated text from the turn was passed to the cloner.
    assert cloning.clone.call_args.args[1] == "ahoy"

    sent = [json.loads(c.args[0]) for c in consumer.send.await_args_list]
    audio_msgs = [m for m in sent if m["type"] == "audio_chunk"]
    assert any(
        base64.b64decode(m["audio"]) == b"CLONED-AUDIO-BYTES" for m in audio_msgs
    )


# --------------------------------------------------------------------------- #
# get_voice_profile_data  — DB access (database_sync_to_async)
# --------------------------------------------------------------------------- #


def test_get_voice_profile_data_returns_none_for_missing(mocker):
    """Missing profile -> None. The ORM is mocked so this needs no live DB
    (a real ``@django_db`` test would activate pytest-django's connection
    blocker and pollute the sibling Channels end-to-end test)."""
    from animetix.models import VoiceProfile

    mocker.patch.object(
        VoiceProfile.objects,
        "get",
        side_effect=VoiceProfile.DoesNotExist,
    )
    consumer = _make_consumer()
    # Call the undecorated function body directly (skip database_sync_to_async).
    result = consumer.get_voice_profile_data.__wrapped__(consumer, 999999)
    assert result is None


def test_get_voice_profile_data_serializes_existing_profile(mocker):
    """Existing profile -> dict view with name/language/roles/sample_url and the
    on-disk sample path (None when no file)."""
    from animetix.models import VoiceProfile

    fake = MagicMock()
    fake.name = "Zoro"
    fake.language = "japanese"
    fake.roles = "swordsman"
    fake.sample_url = "http://x/z.wav"
    fake.sample_file = None  # -> sample_file_path None
    mocker.patch.object(VoiceProfile.objects, "get", return_value=fake)

    consumer = _make_consumer()
    data = consumer.get_voice_profile_data.__wrapped__(consumer, 5)

    assert data == {
        "name": "Zoro",
        "language": "japanese",
        "roles": "swordsman",
        "sample_url": "http://x/z.wav",
        "sample_file_path": None,
    }


# --------------------------------------------------------------------------- #
# disconnect  — background task cleanup
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_disconnect_cancels_receiver_task():
    consumer = _make_consumer()
    consumer.client_connected = True

    async def _idle():
        await asyncio.sleep(3600)

    consumer.receiver_task = asyncio.create_task(_idle())

    await consumer.disconnect(close_code=1000)

    assert consumer.client_connected is False
    # The cancellation is requested; await to let it settle.
    with pytest.raises(asyncio.CancelledError):
        await consumer.receiver_task
    assert consumer.receiver_task.cancelled()


@pytest.mark.asyncio
async def test_disconnect_without_task_is_safe():
    consumer = _make_consumer()
    consumer.client_connected = True
    consumer.receiver_task = None
    await consumer.disconnect(close_code=1001)
    assert consumer.client_connected is False
