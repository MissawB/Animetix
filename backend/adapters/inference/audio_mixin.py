"""Audio processing mixin for Inference adapters."""

import base64  # noqa: E402
import io  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
import wave  # noqa: E402
from typing import TYPE_CHECKING, Any, Dict, Optional  # noqa: E402

from adapters.inference.lazy_load_mixin import LazyLoadMixin  # noqa: E402
from core.domain.exceptions import InferenceError  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402
from core.utils.model_registry import get_verified_revision  # noqa: E402

torch = lazy_import("torch")
np = lazy_import("numpy")

logger = logging.getLogger("animetix.inference.audio_mixin")


class AudioMixin(LazyLoadMixin):
    """
    Mixin providing audio capabilities:
    - Voice Cloning (XTTS/RVC)
    - Soundscapes (AudioLDM)
    - Native S2S (Moshi)
    """

    if TYPE_CHECKING:

        def _log_usage(
            self,
            engine: str,
            input_tokens: int = 0,
            output_tokens: int = 0,
            units: int = 0,
            allocated_budget: int = 0,
        ) -> None: ...

    def _load_xtts(self):
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé."
            )
            raise InferenceError(
                "CUDA GPU is not available. Local audio models loading is disabled."
            )
        self._lazy_load("_tts_model", self._build_xtts, label="XTTS")

    def _build_xtts(self):
        from TTS.api import TTS  # noqa: E402

        # Check for mounted local volume
        mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
        local_model_path = os.path.join(mount_path, "xtts_v2")
        if os.path.exists(local_model_path):
            logger.info(
                f"🎙️ Loading XTTS Model from local FUSE path: {local_model_path}"
            )
            self._tts_model = TTS(model_path=local_model_path)
        else:
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            logger.info(f"🎙️ Loading XTTS Model from Hugging Face: {model_name}")
            self._tts_model = TTS(model_name)

        if torch.cuda.is_available():
            self._tts_model.to("cuda")

    def _load_audioldm(self):
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé."
            )
            raise InferenceError(
                "CUDA GPU is not available. Local audio models loading is disabled."
            )
        self._lazy_load("_audioldm_pipeline", self._build_audioldm, label="AudioLDM")

    def _build_audioldm(self):
        from diffusers import AudioLDMPipeline  # noqa: E402

        logger.info("🎧 Loading AudioLDM for Soundscapes...")
        model_id = "cvssp/audioldm-s-full-v2"
        revision = get_verified_revision(model_id)
        self._audioldm_pipeline = AudioLDMPipeline.from_pretrained(
            model_id,
            revision=revision,
            torch_dtype=(torch.float16 if torch.cuda.is_available() else torch.float32),
        )
        if torch.cuda.is_available():
            self._audioldm_pipeline.to("cuda")

    def _load_moshi(self):
        if not torch.cuda.is_available():
            logger.warning(
                "⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé."
            )
            raise InferenceError(
                "CUDA GPU is not available. Local audio models loading is disabled."
            )
        self._lazy_load("_moshi_model", self._build_moshi, label="Moshi")

    def _build_moshi(self):
        from moshi.models import Moshi  # noqa: E402

        logger.info("🗣️ Loading Kyutai Moshi (S2S)...")
        model_id = "kyutai/moshiko-pytorch-bf16"
        revision = get_verified_revision(model_id)
        self._moshi_model = Moshi.from_pretrained(model_id, revision=revision)
        if torch.cuda.is_available():
            self._moshi_model.to("cuda")

    def clone_voice(
        self, text: str, reference_audio: bytes, language: str = "fr"
    ) -> bytes:
        """Utilise XTTS v2 pour le clonage de voix zero-shot."""
        self._load_xtts()
        if not self._tts_model:
            raise InferenceError("XTTS model not loaded.")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_ref:
                tmp_ref.write(reference_audio)
                tmp_ref_path = tmp_ref.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
                tmp_out_path = tmp_out.name

            self._tts_model.tts_to_file(
                text=text,
                speaker_wav=tmp_ref_path,
                language=language,
                file_path=tmp_out_path,
            )

            with open(tmp_out_path, "rb") as f:
                audio_data = f.read()

            os.unlink(tmp_ref_path)
            os.unlink(tmp_out_path)

            self._log_usage(engine="transformers:xtts_v2", units=1)
            return audio_data
        except Exception as e:
            logger.error(f"❌ Voice Cloning failed: {e}")
            raise InferenceError(f"Voice cloning failed: {str(e)}")

    def generate_soundscape(
        self, video_metadata: Dict[str, Any], prompt: Optional[str] = None
    ) -> str:
        """Génère une ambiance sonore via AudioLDM."""
        self._load_audioldm()
        if not self._audioldm_pipeline:
            raise InferenceError("AudioLDM pipeline not loaded.")
        try:
            import scipy.io.wavfile as wavfile  # noqa: E402

            actions = video_metadata.get("actions", [])
            scene = video_metadata.get("scene", "generic environment")
            base_prompt = f"Soundscape for {scene}, featuring {', '.join(actions) if actions else 'ambient sounds'}."
            final_prompt = f"{prompt}. {base_prompt}" if prompt else base_prompt

            audio_output = self._audioldm_pipeline(
                final_prompt, num_inference_steps=10, audio_length_in_s=5.0
            )
            waveform = audio_output.audios[0]

            buffer = io.BytesIO()
            wavfile.write(buffer, 16000, waveform)

            self._log_usage(engine="transformers:audioldm", units=1)
            return f"data:audio/wav;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Soundscape generation failed: {e}")
            raise InferenceError(f"Soundscape generation failed: {str(e)}")

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Interaction End-to-End Voice via Moshi."""
        if not audio_input:
            raise InferenceError("Audio input is empty")

        self._load_moshi()
        if not self._moshi_model:
            raise InferenceError("Moshi model not loaded.")
        try:
            from pydub import AudioSegment  # noqa: E402

            audio = (
                AudioSegment.from_file(io.BytesIO(audio_input))
                .set_frame_rate(24000)
                .set_channels(1)
            )
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            samples /= float(1 << (8 * audio.sample_width - 1))

            input_tensor = (
                torch.from_numpy(samples).unsqueeze(0).to(self._moshi_model.device)
            )
            with torch.no_grad():
                output_audio_tensor = self._moshi_model.generate(input_tensor)

            output_np = np.clip(
                output_audio_tensor.detach().cpu().numpy().squeeze(), -1.0, 1.0
            )
            output_int16 = (output_np * 32767).astype(np.int16)

            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(output_int16.tobytes())

            self._log_usage(engine="transformers:moshi", units=1)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"❌ S2S failed: {e}")
            raise InferenceError(f"Native S2S failed: {str(e)}")
