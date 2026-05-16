import torch
import logging
from typing import Optional, List, Dict, Any, Generator
from transformers import AutoModelForCausalLM, AutoTokenizer
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.transformers")

class TransformersAdapter(InferencePort):
    """
    Adaptateur utilisant la bibliothèque Transformers standard pour l'inférence locale.
    Plus lent que GGUF mais garanti de fonctionner sur toutes les plateformes (fallback robuste).
    """
    def __init__(self, model_id: str, use_4bit: bool = True):
        self.model_id = model_id
        self.use_4bit = use_4bit
        self.model = None
        self.tokenizer = None

    def _load_model(self):
        if self.model is not None: return
        
        logger.info(f"⏳ Loading Transformers Model: {self.model_id}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Configuration chargement
            kwargs = {
                "trust_remote_code": True,
                "device_map": "auto" if device == "cuda" else None,
                "torch_dtype": torch.float16 if device == "cuda" else torch.float32
            }
            
            if self.use_4bit and device == "cuda":
                from transformers import BitsAndBytesConfig
                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4"
                )

            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, **kwargs)
            logger.info("✅ Transformers Model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load model {self.model_id}: {e}")
            raise e

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0) -> str:
        try:
            self._load_model()
            logger.info(f"🚀 [Transformers] Generating for prompt: {prompt[:50]}...")
            
            # Formatage simplifié ChatML (supporté par Qwen et beaucoup d'autres)
            full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.3,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
            decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # On ne garde que la partie après l'assistant
            answer = decoded
            if "assistant" in decoded:
                answer = decoded.split("assistant")[-1].strip()
            
            logger.info(f"✅ [Transformers] Generation successful: {answer[:50]}...")
            return answer.strip()
            
        except Exception as e:
            logger.error(f"❌ [Transformers] Generation failed: {e}")
            return f"Erreur Transformers: {e}"

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0):
        # Implementation simple pour l'interface
        yield self.generate(prompt, system_prompt, thinking_budget)

    def get_text_embedding(self, text: str) -> List[float]:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        return model.encode(text).tolist()

    # Default implementations
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
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]: return []
    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]: return []

    def health_check(self) -> dict:
        return {"status": "online" if self.model else "offline", "engine": "transformers"}
