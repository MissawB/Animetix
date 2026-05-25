import os
import logging
import tempfile
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference.xtts")

class XTTSAdapter(InferencePort):
    """
    Adaptateur dédié au clonage de voix via Coqui XTTS v2.
    Gère le chargement paresseux du modèle pour économiser les ressources.
    """
    def __init__(
        self, 
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        usage_port: Optional[UsagePort] = None
    ):
        self.model_name = model_name
        self.usage_port = usage_port
        self._tts_model = None

    def _load_model(self):
        if self._tts_model:
            return
        try:
            from TTS.api import TTS
            logger.info(f"🎙️ Loading XTTS Model: {self.model_name}")
            self._tts_model = TTS(self.model_name)
            if torch.cuda.is_available():
                self._tts_model.to("cuda")
            else:
                logger.warning("⚠️ CUDA not available. XTTS will run on CPU.")
        except ImportError:
            logger.error("❌ Coqui TTS not installed. XTTSAdapter disabled.")
        except Exception as e:
            logger.error(f"❌ Failed to load XTTS model: {e}")

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """
        Génère de l'audio à partir de texte en clonant une voix de référence.
        """
        self._load_model()
        if not self._tts_model:
            return b""

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_ref:
                tmp_ref.write(reference_audio)
                tmp_ref_path = tmp_ref.name
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
                tmp_out_path = tmp_out.name

            # XTTS v2 supporte nativement le zero-shot cloning
            self._tts_model.tts_to_file(
                text=text,
                speaker_wav=tmp_ref_path,
                language=language,
                file_path=tmp_out_path
            )

            with open(tmp_out_path, "rb") as f:
                audio_data = f.read()

            # Nettoyage des fichiers temporaires
            if os.path.exists(tmp_ref_path): os.unlink(tmp_ref_path)
            if os.path.exists(tmp_out_path): os.unlink(tmp_out_path)

            # --- LOG USAGE ---
            if self.usage_port:
                try:
                    from animetix.middleware import get_current_user_id
                    user_id = get_current_user_id()
                except (ImportError, Exception):
                    user_id = None
                
                # XTTS v2 costs are tracked per request (unit)
                self.usage_port.log_usage(
                    engine="xtts-v2",
                    units=1,
                    user_id=user_id
                )

            return audio_data

        except Exception as e:
            logger.error(f"❌ Voice Cloning failed in XTTSAdapter: {e}")
            return b""

    def generate_soundscape(self, prompt: str, duration: int = 10) -> bytes:
        import wave
        import io
        logger.warning("Mock implementation of generate_soundscape used")
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
        return buffer.getvalue()

    def speech_to_speech(self, audio_data: bytes, target_voice: bytes) -> bytes:
        logger.warning("Mock implementation of speech_to_speech used")
        return audio_data

    def health_check(self) -> dict:
        return {
            "status": "online" if self._tts_model else "offline",
            "engine": "XTTS v2",
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
