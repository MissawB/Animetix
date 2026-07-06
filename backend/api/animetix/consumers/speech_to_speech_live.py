import asyncio
import base64
import io
import json
import logging
import os
import wave

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from core.utils.gemini_models import GEMINI_LIVE
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
        user = await self._resolve_user()
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.user = user

        # GPU facturé : déduction forfaitaire par session (règle « GPU = Bx »).
        if not await self._charge_session():
            await self.close(code=4402)
            return

        # Echo the negotiated subprotocol so browsers accept the handshake when the
        # Firebase token was passed via Sec-WebSocket-Protocol (see _resolve_user).
        subprotocols = self.scope.get("subprotocols", [])
        if subprotocols and subprotocols[0] == "bearer":
            await self.accept(subprotocol="bearer")
        else:
            await self.accept()
        self.client_connected = True
        self.gemini_session = None
        self.gemini_client = None
        self.receiver_task = None

        from urllib.parse import parse_qs

        query_string = self.scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        profile_id_str = query_params.get("voice_profile_id", [None])[0]
        self.voice_profile_id = (
            int(profile_id_str)
            if (profile_id_str and profile_id_str.isdigit())
            else None
        )

        # Borne le coût Gemini : coupe la session après 10 min.
        self.deadline_task = asyncio.create_task(self._enforce_deadline())
        self.receiver_task = asyncio.create_task(self.run_gemini_session())
        logger.info(
            "SpeechToSpeechLiveConsumer client connected (user=%s).", self.user.id
        )

    async def _resolve_user(self):
        # 1) Session (AuthMiddlewareStack) ; 2) token Firebase via le
        # sous-protocole Sec-WebSocket-Protocol (["bearer", "<id_token>"]).
        # On NE lit PAS le token depuis l'URL : un token en query string finirait
        # dans les logs d'accès (proxy/Cloud Run). Le navigateur ne pouvant pas
        # poser d'en-tête Authorization sur un handshake WS, le sous-protocole est
        # le canal standard pour transmettre le token hors de l'URL.
        user = self.scope.get("user")
        if user is not None and user.is_authenticated:
            return user
        subprotocols = self.scope.get("subprotocols", [])
        if subprotocols and subprotocols[0] == "bearer" and len(subprotocols) > 1:
            return await self._verify_firebase_token(subprotocols[1])
        return None

    @database_sync_to_async
    def _verify_firebase_token(self, token):
        from rest_framework.exceptions import AuthenticationFailed

        from animetix.auth import GoogleIdentityAuthentication

        # Réutilise le vérificateur DRF : on fabrique une pseudo-requête portant
        # l'Authorization Bearer attendu par authenticate().
        class _Req:
            META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        try:
            result = GoogleIdentityAuthentication().authenticate(_Req())
        except AuthenticationFailed:
            return None
        return result[0] if result else None

    @database_sync_to_async
    def _charge_session(self):
        from core.domain.services.berrix_economy import FEATURE_BX_COSTS

        from animetix.api.billing import PaymentRequired, deduct_berrix

        try:
            deduct_berrix(
                self.user,
                FEATURE_BX_COSTS["s2s_live"],
                "Speech-to-Speech Live (session)",
            )
            return True
        except PaymentRequired:
            # Expected: not authenticated / insufficient balance → 4402.
            return False
        except Exception:
            # Unexpected (DB/transient) errors must not masquerade as "no balance":
            # log them, but still fail closed (deny the paid GPU session).
            logger.exception(
                "S2S charge failed unexpectedly (user=%s)",
                getattr(self.user, "id", None),
            )
            return False

    async def _enforce_deadline(self):
        await asyncio.sleep(600)  # 10 minutes
        logger.info(
            "S2S session deadline reached (user=%s), closing.",
            getattr(self, "user", None),
        )
        await self.close(code=4408)

    @database_sync_to_async
    def get_voice_profile_data(self, profile_id):
        from animetix.models import VoiceProfile

        try:
            profile = VoiceProfile.objects.get(id=profile_id)
            return {
                "name": profile.name,
                "language": profile.language,
                "roles": profile.roles,
                "sample_url": profile.sample_url,
                "sample_file_path": (
                    profile.sample_file.path if profile.sample_file else None
                ),
            }
        except VoiceProfile.DoesNotExist:
            return None

    async def run_gemini_session(self):
        from animetix.containers import get_container

        container = get_container()
        self.voice_cloning_service = container.core.voice_cloning_service()

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

            # If a voice profile is selected, we configure Gemini Live for roleplay and text-only response
            voice_profile_data = None
            if self.voice_profile_id:
                voice_profile_data = await self.get_voice_profile_data(
                    self.voice_profile_id
                )

            model = GEMINI_LIVE
            config = {"response_modalities": ["AUDIO"]}
            system_prompt = "You are a helpful AI assistant."

            if voice_profile_data:
                config["response_modalities"] = ["TEXT"]
                system_prompt = (
                    f"You are roleplaying as {voice_profile_data['name']}. "
                    f"Your roles/traits: {voice_profile_data['roles'] or 'unknown'}. "
                    "Respond to the user with the personality, tone, and traits of this character. "
                    "Make your answers short, expressive, and conversational."
                )

            config["system_instruction"] = {"parts": [{"text": system_prompt}]}

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

                accumulated_text = ""

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

                                if part.text:
                                    accumulated_text += part.text
                                    await self.send(
                                        json.dumps(
                                            {
                                                "type": "text_chunk",
                                                "text": part.text,
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

                        if getattr(server_content, "turn_complete", False):
                            if accumulated_text and voice_profile_data:
                                try:
                                    logger.info(
                                        f"Generating cloned voice for: {accumulated_text}"
                                    )
                                    ref_audio_bytes = None
                                    if voice_profile_data[
                                        "sample_file_path"
                                    ] and os.path.exists(
                                        voice_profile_data["sample_file_path"]
                                    ):
                                        with open(
                                            voice_profile_data["sample_file_path"], "rb"
                                        ) as f:
                                            ref_audio_bytes = f.read()
                                    else:
                                        # Use safe requests/httpx here
                                        from core.utils.security import (
                                            safe_http_request,
                                        )

                                        resp = safe_http_request(
                                            "GET",
                                            voice_profile_data["sample_url"],
                                            timeout=10,
                                        )
                                        if resp.status_code == 200:
                                            ref_audio_bytes = resp.content

                                    if ref_audio_bytes:
                                        loop = asyncio.get_running_loop()
                                        cloned_audio = await loop.run_in_executor(
                                            None,
                                            self.voice_cloning_service.clone,
                                            ref_audio_bytes,
                                            accumulated_text,
                                            0,
                                            "rvc_v2",
                                            0.75,
                                        )
                                        audio_b64 = base64.b64encode(
                                            cloned_audio
                                        ).decode("utf-8")
                                        await self.send(
                                            json.dumps(
                                                {
                                                    "type": "audio_chunk",
                                                    "audio": audio_b64,
                                                    "mime_type": "audio/wav",
                                                }
                                            )
                                        )
                                except Exception as ex:
                                    logger.error(
                                        f"Failed to clone voice in live turn: {ex}"
                                    )
                                accumulated_text = ""

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
        if getattr(self, "receiver_task", None):
            self.receiver_task.cancel()
        if getattr(self, "deadline_task", None):
            self.deadline_task.cancel()
        logger.info("Client disconnected from SpeechToSpeechLiveConsumer.")
