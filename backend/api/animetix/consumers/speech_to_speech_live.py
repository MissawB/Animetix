import asyncio
import base64
import io
import json
import logging
import wave

from channels.generic.websocket import AsyncWebsocketConsumer
from google import genai
from google.genai import types

logger = logging.getLogger("animetix.consumers.s2s_live")


def process_client_audio(audio_bytes: bytes) -> bytes:
    """
    Converts client audio (any format) to 16kHz, mono, 16-bit PCM little-endian.
    Tries Python's native wave/audioop first to avoid external ffmpeg requirement on WAV inputs.
    """
    try:
        # Try reading as standard WAV first
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            params = wav_file.getparams()
            raw_frames = wav_file.readframes(params.nframes)

            # If already 16kHz, 1 channel, 16-bit, return raw frames
            if (
                params.framerate == 16000
                and params.nchannels == 1
                and params.sampwidth == 2
            ):
                return raw_frames

            # Otherwise, convert/resample using standard library (available in Python 3.12)
            import audioop  # noqa: E402

            data = raw_frames

            # Convert stereo to mono
            if params.nchannels == 2:
                data = audioop.tomono(data, params.sampwidth, 1, 1)

            # Convert sample width to 16-bit (2 bytes)
            if params.sampwidth != 2:
                data = audioop.lin2lin(data, params.sampwidth, 2)

            # Resample to 16000 Hz
            if params.framerate != 16000:
                state = None
                data, state = audioop.ratecv(data, 2, 1, params.framerate, 16000, state)

            return data
    except Exception as e:
        logger.debug(f"Native wave/audioop processing failed: {e}")

    # Fallback to pydub (requires ffmpeg for non-WAV formats like WebM/Opus)
    try:
        from pydub import AudioSegment  # noqa: E402

        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        return audio.raw_data
    except Exception as e:
        logger.error(f"pydub audio conversion failed: {e}")
        raise ValueError(
            f"Audio conversion failed: ffmpeg might be required for compressed formats. Details: {e}"
        )


def pcm_to_wav(
    pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2
) -> bytes:
    """
    Wraps raw PCM bytes in a WAV header.
    """
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


class SpeechToSpeechLiveConsumer(AsyncWebsocketConsumer):
    """
    Consumer for real-time bidirectional Speech-to-Speech interactions
    using Gemini Multimodal Live API via WebSockets.
    """

    async def connect(self):
        await self.accept()
        self.client_connected = True
        self.gemini_session = None
        self.gemini_client = None
        self.receiver_task = None

        # Start the Gemini session in the background
        self.receiver_task = asyncio.create_task(self.run_gemini_session())
        logger.info("SpeechToSpeechLiveConsumer client connected.")

    async def run_gemini_session(self):
        import os  # noqa: E402

        api_key = os.getenv("GEMINI_API_KEY")
        try:
            if not api_key:
                logger.info(
                    "Initializing Google GenAI client with Vertex AI backend for Live API."
                )
                self.gemini_client = genai.Client(
                    vertexai=True,
                    project=os.getenv("GOOGLE_CLOUD_PROJECT", "animetix"),
                    location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west9"),
                )
            else:
                logger.info(
                    "Initializing Google GenAI client with API Key for Live API."
                )
                self.gemini_client = genai.Client(api_key=api_key)

            model = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-exp")
            config = {"response_modalities": ["AUDIO"]}

            logger.info(f"Connecting to Gemini Live API with model {model}...")
            async with self.gemini_client.aio.live.connect(
                model=model, config=config
            ) as session:
                self.gemini_session = session
                logger.info("Successfully connected to Gemini Live session.")

                await self.send(
                    json.dumps(
                        {
                            "type": "session_ready",
                            "message": "Gemini Live session connected.",
                        }
                    )
                )

                async for response in session.receive():
                    if not self.client_connected:
                        break

                    server_content = response.server_content
                    if server_content:
                        if server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if part.inline_data:
                                    # Wrap raw 24kHz PCM into browser-playable WAV
                                    wav_bytes = pcm_to_wav(part.inline_data.data)
                                    audio_b64 = base64.b64encode(wav_bytes).decode(
                                        "utf-8"
                                    )
                                    await self.send(
                                        json.dumps(
                                            {
                                                "type": "audio_chunk",
                                                "audio": audio_b64,
                                                "mime_type": "audio/wav",
                                            }
                                        )
                                    )

                        if server_content.output_transcription:
                            await self.send(
                                json.dumps(
                                    {
                                        "type": "text_chunk",
                                        "text": str(
                                            server_content.output_transcription
                                        ),
                                    }
                                )
                            )
        except asyncio.CancelledError:
            logger.info("Gemini Live session task cancelled.")
        except Exception as e:
            logger.error(f"Error in Gemini Live session: {e}", exc_info=True)
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "message": f"Gemini Live connection failed: {str(e)}",
                    }
                )
            )
            await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                msg_type = data.get("type")
                if msg_type == "text" and self.gemini_session:
                    text_input = data.get("data")
                    await self.gemini_session.send_realtime_input(text=text_input)
                elif msg_type == "audio" and self.gemini_session:
                    audio_b64 = data.get("data")
                    audio_bytes = base64.b64decode(audio_b64)
                    pcm_bytes = process_client_audio(audio_bytes)
                    await self.gemini_session.send_realtime_input(
                        audio=types.Blob(
                            data=pcm_bytes, mime_type="audio/pcm;rate=16000"
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing client message: {e}")

        elif bytes_data and self.gemini_session:
            try:
                pcm_bytes = process_client_audio(bytes_data)
                await self.gemini_session.send_realtime_input(
                    audio=types.Blob(data=pcm_bytes, mime_type="audio/pcm;rate=16000")
                )
            except Exception as e:
                logger.error(f"Error sending binary audio to Gemini: {e}")

    async def disconnect(self, close_code):
        self.client_connected = False
        if self.receiver_task:
            self.receiver_task.cancel()
        logger.info("Client disconnected from SpeechToSpeechLiveConsumer.")
