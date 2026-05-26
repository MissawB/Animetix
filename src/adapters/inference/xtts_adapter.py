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

logger = logging.getLogger("animetix.inference.xtts")

class XTTSAdapter(InferencePort):
    """
    Adaptateur dédié au clonage de voix (XTTS), ambiances sonores (AudioLDM) 
    et Speech-to-Speech natif (Moshi).
    """
    def __init__(
        self, 
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        usage_port: Optional[UsagePort] = None
    ):
        self.model_name = model_name
        self.usage_port = usage_port
        self._tts_model = None
        self._audioldm_pipeline = None
        self._moshi_model = None

    def _load_xtts(self):
        if self._tts_model: return
        try:
            from TTS.api import TTS
            logger.info(f"🎙️ Loading XTTS Model: {self.model_name}")
            self._tts_model = TTS(self.model_name)
            if torch.cuda.is_available(): self._tts_model.to("cuda")
        except Exception as e:
            logger.error(f"❌ Failed to load XTTS: {e}")

    def _load_audioldm(self):
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
        if self._moshi_model: return
        try:
            from moshi.models import Moshi
            logger.info("🗣️ Loading Kyutai Moshi (S2S)...")
            self._moshi_model = Moshi.from_pretrained("kyutai/moshi-1b-preview")
            if torch.cuda.is_available(): self._moshi_model.to("cuda")
        except Exception as e:
            logger.error(f"❌ Failed to load Moshi: {e}")

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        self._load_xtts()
        if not self._tts_model: return b""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_ref:
                tmp_ref.write(reference_audio); tmp_ref_path = tmp_ref.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
                tmp_out_path = tmp_out.name
            self._tts_model.tts_to_file(text=text, speaker_wav=tmp_ref_path, language=language, file_path=tmp_out_path)
            with open(tmp_out_path, "rb") as f: audio_data = f.read()
            os.unlink(tmp_ref_path); os.unlink(tmp_out_path)
            return audio_data
        except Exception as e:
            logger.error(f"❌ Voice Cloning failed: {e}"); return b""

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        self._load_audioldm()
        if not self._audioldm_pipeline: return ""
        try:
            import scipy.io.wavfile as wavfile
            actions = video_metadata.get("actions", [])
            scene = video_metadata.get("scene", "generic environment")
            base_prompt = f"Soundscape for {scene}, featuring {', '.join(actions) if actions else 'ambient sounds'}."
            final_prompt = f"{prompt}. {base_prompt}" if prompt else base_prompt
            audio_output = self._audioldm_pipeline(final_prompt, num_inference_steps=10, audio_length_in_s=5.0)
            waveform = audio_output.audios[0]
            buffer = io.BytesIO(); wavfile.write(buffer, 16000, waveform)
            return f"data:audio/wav;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Soundscape failed: {e}"); return ""

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        self._load_moshi()
        if not self._moshi_model: return b""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_input)).set_frame_rate(24000).set_channels(1)
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            samples /= float(1 << (8 * audio.sample_width - 1))
            input_tensor = torch.from_numpy(samples).unsqueeze(0).to(self._moshi_model.device)
            with torch.no_grad(): output_audio_tensor = self._moshi_model.generate(input_tensor)
            output_np = np.clip(output_audio_tensor.detach().cpu().numpy().squeeze(), -1.0, 1.0)
            output_int16 = (output_np * 32767).astype(np.int16)
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(output_int16.tobytes())
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"❌ S2S failed: {e}"); return b""

    def health_check(self) -> dict:
        return {"status": "online" if self._tts_model else "offline", "engine": "XTTS/AudioLDM/Moshi"}
