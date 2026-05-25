import logging
import base64
from io import BytesIO
from typing import Optional, List, Dict, Any
from PIL import Image
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference.diffusers")

class DiffusersAdapter(InferencePort):
    """
    Adaptateur local pour la génération d'images utilisant la bibliothèque Diffusers.
    Optimisé pour SDXL-Turbo (vitesse) ou Animagine (style).
    """
    def __init__(
        self, 
        model_id: str = "stabilityai/sdxl-turbo", 
        use_fp16: bool = True,
        usage_port: Optional[UsagePort] = None
    ):
        self.model_id = model_id
        self.use_fp16 = use_fp16
        self.usage_port = usage_port
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

            # --- LOG USAGE ---
            if self.usage_port:
                try:
                    from animetix.middleware import get_current_user_id
                    user_id = get_current_user_id()
                except (ImportError, Exception):
                    user_id = None
                
                self.usage_port.log_usage(
                    engine=self.model_id,
                    units=1,
                    user_id=user_id
                )
            
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            logger.error(f"❌ Local Image Generation failed: {e}")
            return f"Erreur de génération : {str(e)}"

    def estimate_depth(self, image_data: bytes) -> bytes:
        """Estime la carte de profondeur (Depth Map) d'une image 2D."""
        try:
            from transformers import pipeline
            if not hasattr(self, '_depth_pipe') or self._depth_pipe is None:
                logger.info("🏗️ Loading Depth Estimation Model: LiheYoung/depth-anything-small-hf")
                device = 0 if torch.cuda.is_available() else -1
                self._depth_pipe = pipeline("depth-estimation", model="LiheYoung/depth-anything-small-hf", device=device)
            
            image = Image.open(BytesIO(image_data))
            result = self._depth_pipe(image)
            depth_image = result["depth"]
            
            buffered = BytesIO()
            depth_image.save(buffered, format="PNG")
            return buffered.getvalue()
        except Exception as e:
            logger.error(f"❌ Depth estimation failed: {e}")
            return b""

    def transform_image_to_anime(self, image_data: bytes, studio_style: str = "", prompt: str = "") -> bytes:
        """Mock implementation of transform_image_to_anime."""
        logger.warning("Mock implementation of transform_image_to_anime used")
        return image_data

    def transform_video_to_anime(self, video_data: bytes, studio_style: str = "", prompt: str = "") -> bytes:
        """Mock implementation of transform_video_to_anime."""
        logger.warning("Mock implementation of transform_video_to_anime used")
        return video_data

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Diffusers n'est pas un moteur de texte. On lève une erreur explicite."""
        from core.ports.inference_port import InferenceNotImplementedError
        raise InferenceNotImplementedError("DiffusersAdapter ne supporte pas la génération de texte pure. Utilisez GgufAdapter ou TransformersAdapter.")

    def stream_generate(self, prompt: str, system_prompt: str = "", **kwargs):
        """Diffusers n'est pas un moteur de texte."""
        from core.ports.inference_port import InferenceNotImplementedError
        raise InferenceNotImplementedError("DiffusersAdapter ne supporte pas le streaming de texte.")

    def health_check(self) -> dict:
        return {
            "status": "online" if self.pipe else "offline",
            "engine": "diffusers",
            "model": self.model_id,
            "device": str(next(self.pipe.parameters()).device) if self.pipe else "N/A"
        }

