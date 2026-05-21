import logging
import base64
from io import BytesIO
from typing import Optional, List, Dict, Any
from PIL import Image
from core.ports.inference_port import InferencePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference.diffusers")

class DiffusersAdapter(InferencePort):
    """
    Adaptateur local pour la génération d'images utilisant la bibliothèque Diffusers.
    Optimisé pour SDXL-Turbo (vitesse) ou Animagine (style).
    """
    def __init__(self, model_id: str = "stabilityai/sdxl-turbo", use_fp16: bool = True):
        self.model_id = model_id
        self.use_fp16 = use_fp16
        self.pipe = None

    def _load_model(self):
        if self.pipe:
            return
        try:
            from diffusers import AutoPipelineForText2Image
            logger.info(f"🏗️ Loading Local Diffusion Model: {self.model_id}")
            
            dtype = torch.float16 if (self.use_fp16 and torch.cuda.is_available()) else torch.float32
            variant = "fp16" if dtype == torch.float16 else None
            
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                self.model_id, 
                torch_dtype=dtype, 
                variant=variant,
                trust_remote_code=True
            )
            
            if torch.cuda.is_available():
                # Optimisations VRAM
                self.pipe.to("cuda")
                self.pipe.enable_model_cpu_offload()
                self.pipe.enable_vae_tiling()
            else:
                logger.warning("⚠️ CUDA not available. Running Diffusion on CPU (will be slow).")
                self.pipe.to("cpu")
                
        except Exception as e:
            logger.error(f"❌ Failed to load diffusers model: {e}")

    def generate_image(self, prompt: str, style: str = "") -> str:
        """Génère une image et la renvoie en format Base64 URI."""
        self._load_model()
        if not self.pipe:
            return "Erreur: Modèle de diffusion non chargé."
        
        full_prompt = f"{prompt}, {style}".strip()
        logger.info(f"🎨 Generating image for prompt: {full_prompt[:50]}...")
        
        try:
            # Paramètres optimisés pour SDXL-Turbo (vitesse max)
            # Si on change de modèle, il faudra peut-être ajuster num_inference_steps
            num_steps = 1 if "turbo" in self.model_id.lower() else 30
            guidance_scale = 0.0 if "turbo" in self.model_id.lower() else 7.5
            
            image = self.pipe(
                prompt=full_prompt, 
                num_inference_steps=num_steps, 
                guidance_scale=guidance_scale
            ).images[0]
            
            # Encodage en Base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            logger.error(f"❌ Local Image Generation failed: {e}")
            return f"Erreur de génération : {str(e)}"

    # Les autres méthodes du port ne sont pas implémentées ici (déjà gérées par TransformersAdapter ou autres)
    def generate(self, *args, **kwargs): pass
    def stream_generate(self, *args, **kwargs): pass
    def calculate_visual_similarity(self, *args, **kwargs): return 0.0
    def get_image_embedding(self, *args, **kwargs): return []
    def classify_image(self, *args, **kwargs): return {}
    def detect_objects(self, *args, **kwargs): return []
    def get_video_temporal_embeddings(self, *args, **kwargs): return []
    def localize_video_actions(self, *args, **kwargs): return []
    def transform_image_to_anime(self, *args, **kwargs): return ""
    def transform_video_to_anime(self, *args, **kwargs): return ""
    def generate_soundscape(self, *args, **kwargs): return ""
    def clone_voice(self, *args, **kwargs): return b""
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

    def health_check(self) -> dict:
        return {
            "status": "online" if self.pipe else "offline",
            "engine": "diffusers",
            "model": self.model_id,
            "device": str(next(self.pipe.parameters()).device) if self.pipe else "N/A"
        }
