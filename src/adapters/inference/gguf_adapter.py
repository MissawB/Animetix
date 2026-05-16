import logging
from typing import Optional, List, Dict, Any, Generator
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.gguf")

class GgufAdapter(InferencePort):
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.llm = None

    def _load_model(self):
        if self.llm: return
        try:
            from llama_cpp import Llama
            logger.info(f"🏗️ Loading GGUF Model: {self.model_path}")
            self.llm = Llama(model_path=self.model_path, n_ctx=4096, n_gpu_layers=-1)
        except ImportError:
            logger.warning("⚠️ llama-cpp-python not installed. GGUFAdapter disabled.")
        except Exception as e:
            logger.error(f"❌ Failed to load GGUF model: {e}")

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0) -> str:
        try:
            self._load_model()
            if not self.llm: return "Erreur: GGUF indisponible."
            res = self.llm.create_chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            )
            return res['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"GGUF Generation Error: {e}")
            return f"Erreur GGUF: {e}"

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding via le modèle GGUF si supporté, sinon fallback local."""
        try:
            self._load_model()
            if not self.llm: return []
            # llama-cpp-python supporte les embeddings si n_ctx/embedding=True est configuré
            # Ici on fait un simple fallback vers un modèle SentenceTransformers local pour la stabilité
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
            return model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Embedding Error: {e}")
            return []

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0):
        self._load_model()
        if not self.llm: yield "Erreur: GGUF indisponible."; return
        stream = self.llm.create_chat_completion(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in stream:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta: yield delta['content']

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float: return 0.0
    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]: return []
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]: return {}
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]: return []
    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: return []
    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: return []
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str: return ""
    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str: return ""
    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str: return ""
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes: return b""
    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes: return b""
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]: return {}
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str: return ""
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]: return {"is_safe": True}
    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str: return ""
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: return {}
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: return {}
    def estimate_depth(self, image_data: bytes) -> bytes: return b""
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]: return {}
    
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        return [{"url": url, "score": 1.0} for url in image_urls]
        
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        return []

    def health_check(self) -> dict:
        return {"status": "online" if self.llm else "offline", "engine": "llama.cpp"}
