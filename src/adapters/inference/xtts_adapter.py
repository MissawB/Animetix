import os
import logging
import tempfile
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference.xtts")

class XTTSAdapter(InferencePort):
    """
    Adaptateur dédié au clonage de voix via Coqui XTTS v2.
    Gère le chargement paresseux du modèle pour économiser les ressources.
    """
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        self.model_name = model_name
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

            return audio_data

        except Exception as e:
            logger.error(f"❌ Voice Cloning failed in XTTSAdapter: {e}")
            return b""

    # Méthodes du port non implémentées par cet adaptateur spécifique
    def generate(self, *args, **kwargs): return ""
    def stream_generate(self, *args, **kwargs): yield ""
    def calculate_visual_similarity(self, *args, **kwargs): return 0.0
    def get_image_embedding(self, *args, **kwargs): return []
    def classify_image(self, *args, **kwargs): return {}
    def detect_objects(self, *args, **kwargs): return []
    def get_video_temporal_embeddings(self, *args, **kwargs): return []
    def localize_video_actions(self, *args, **kwargs): return []
    def transform_image_to_anime(self, *args, **kwargs): return ""
    def transform_video_to_anime(self, *args, **kwargs): return ""
    def generate_soundscape(self, *args, **kwargs): return ""
    def speech_to_speech(self, *args, **kwargs): return b""
    def estimate_depth(self, *args, **kwargs): return b""
    def generate_3d_scene(self, *args, **kwargs): return {}
    def process_manga_page(self, *args, **kwargs): return {}
    def translate_manga_page(self, *args, **kwargs): return {}
    def inpaint_text_bubbles(self, *args, **kwargs): return ""
    def moderate_content(self, *args, **kwargs): return {"is_safe": True}
    def generate_image_description(self, *args, **kwargs): return ""
    def get_diagnostics(self, *args, **kwargs): return {}
    def calculate_uncertainty(self, *args, **kwargs): return {}
    def visual_rerank(self, *args, **kwargs): return []
    def get_multimodal_late_interaction(self, *args, **kwargs): return []
    def generate_image(self, *args, **kwargs): return ""

    def health_check(self) -> dict:
        return {
            "status": "online" if self._tts_model else "offline",
            "engine": "XTTS v2",
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
