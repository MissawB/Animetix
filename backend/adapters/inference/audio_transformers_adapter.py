import os
import logging
import tempfile
import io
import wave
import base64
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
np = lazy_import('numpy')

logger = logging.getLogger("animetix.inference.audio_transformers")

class AudioTransformersAdapter(InferencePort):
    """
    Adaptateur spécialisé pour les tâches audio : 
    - Clonage de voix (XTTS/RVC)
    - Ambiances sonores (AudioLDM)
    - Speech-to-Speech natif (Moshi/Qwen2-Audio)
    """
    def __init__(
        self, 
        xtts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        usage_port: Optional[UsagePort] = None
    ):
        self.xtts_model_name = xtts_model_name
        self.usage_port = usage_port
        self._tts_model = None
        self._audioldm_pipeline = None
        self._moshi_model = None

    def _load_xtts(self):
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé pour éviter une surcharge CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local audio models loading is disabled.")
        if self._tts_model: return
        try:
            from TTS.api import TTS
            logger.info(f"🎙️ Loading XTTS Model: {self.xtts_model_name}")
            self._tts_model = TTS(self.xtts_model_name)
            if torch.cuda.is_available(): self._tts_model.to("cuda")
        except Exception as e:
            logger.error(f"❌ Failed to load XTTS: {e}")

    def _load_audioldm(self):
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé pour éviter une surcharge CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local audio models loading is disabled.")
        if self._audioldm_pipeline: return
        try:
            from diffusers import AudioLDMPipeline
            logger.info("🎧 Loading AudioLDM for Soundscapes...")
            self._audioldm_pipeline = AudioLDMPipeline.from_pretrained(
                "cvssp/audioldm-s-full-v2", 
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            if torch.cuda.is_available(): self._audioldm_pipeline.to("cuda")
        except Exception as e:
            logger.error(f"❌ Failed to load AudioLDM: {e}")

    def _load_moshi(self):
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU CUDA non détecté. Chargement local des modèles audio désactivé pour éviter une surcharge CPU/OOM.")
            raise InferenceError("CUDA GPU is not available. Local audio models loading is disabled.")
        if self._moshi_model: return
        try:
            from moshi.models import Moshi
            logger.info("🗣️ Loading Kyutai Moshi (S2S)...")
            self._moshi_model = Moshi.from_pretrained("kyutai/moshi-1b-preview")
            if torch.cuda.is_available(): self._moshi_model.to("cuda")
        except ImportError as e:
            logger.error(f"❌ Failed to load Moshi due to missing package: {e}")
            raise InferenceError("Library 'moshi' or dependencies missing.") from e
        except Exception as e:
            logger.error(f"❌ Failed to load Moshi: {e}")

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
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
                file_path=tmp_out_path
            )
            
            with open(tmp_out_path, "rb") as f: 
                audio_data = f.read()
            
            os.unlink(tmp_ref_path)
            os.unlink(tmp_out_path)
            return audio_data
        except Exception as e:
            logger.error(f"❌ Voice Cloning failed: {e}")
            raise InferenceError(f"Voice cloning failed: {str(e)}")

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Génère une ambiance sonore via AudioLDM."""
        self._load_audioldm()
        if not self._audioldm_pipeline:
            raise InferenceError("AudioLDM pipeline not loaded.")
        try:
            import scipy.io.wavfile as wavfile
            actions = video_metadata.get("actions", [])
            scene = video_metadata.get("scene", "generic environment")
            base_prompt = f"Soundscape for {scene}, featuring {', '.join(actions) if actions else 'ambient sounds'}."
            final_prompt = f"{prompt}. {base_prompt}" if prompt else base_prompt
            
            audio_output = self._audioldm_pipeline(final_prompt, num_inference_steps=10, audio_length_in_s=5.0)
            waveform = audio_output.audios[0]
            
            buffer = io.BytesIO()
            wavfile.write(buffer, 16000, waveform)
            return f"data:audio/wav;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Soundscape generation failed: {e}")
            raise InferenceError(f"Soundscape generation failed: {str(e)}")

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Interaction End-to-End Voice via Moshi."""
        if not audio_input:
            raise InferenceError("Audio input is empty.")
        self._load_moshi()
        if not self._moshi_model:
            raise InferenceError("Moshi model not loaded.")
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_input)).set_frame_rate(24000).set_channels(1)
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            samples /= float(1 << (8 * audio.sample_width - 1))
            
            input_tensor = torch.from_numpy(samples).unsqueeze(0).to(self._moshi_model.device)
            with torch.no_grad(): 
                output_audio_tensor = self._moshi_model.generate(input_tensor)
            
            output_np = np.clip(output_audio_tensor.detach().cpu().numpy().squeeze(), -1.0, 1.0)
            output_int16 = (output_np * 32767).astype(np.int16)
            
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(output_int16.tobytes())
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"❌ S2S failed: {e}")
            raise InferenceError(f"Native S2S failed: {str(e)}")

    def health_check(self) -> dict: 
        return {
            "status": "online" if self._tts_model or self._audioldm_pipeline else "offline", 
            "engine": "audio_transformers"
        }
