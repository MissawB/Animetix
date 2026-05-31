import logging
from typing import Optional, List, Dict
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from adapters.inference.image_gen_mixin import ImageGenMixin

logger = logging.getLogger("animetix.inference.diffusers")

class DiffusersAdapter(ImageGenMixin, InferencePort):
    """
    Dedicated image generation adapter using local diffusion models via ImageGenMixin.
    """
    def __init__(
        self, 
        model_id: str = "stabilityai/sdxl-turbo", 
        use_fp16: bool = True,
        usage_port: Optional[UsagePort] = None
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        self.use_fp16 = use_fp16
        self.pipe = None
        self._img2img_pipe = None
        self._inpaint_pipe = None

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """
        Génère un sprite de personnage sur fond blanc et tente de le rendre transparent.
        Delegates base generation to ImageGenMixin.
        """
        import base64
        from io import BytesIO
        from PIL import Image
        
        sprite_prompt = f"{prompt}, full body portrait on pure white background, anime character sheet style"
        image_data_url = self.generate_image(sprite_prompt, style)
        
        if image_data_url.startswith("data:image"):
            try:
                # Tentative de rendre le fond blanc transparent
                header, encoded = image_data_url.split(",", 1)
                img_data = base64.b64decode(encoded)
                img = Image.open(BytesIO(img_data)).convert("RGBA")
                
                # Algorithme simple de suppression du fond blanc
                datas = img.getdata()
                new_data = []
                for item in datas:
                    # Si le pixel est presque blanc, on le rend transparent
                    if item[0] > 240 and item[1] > 240 and item[2] > 240:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                img.putdata(new_data)
                
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                return f"data:image/png;base64,{img_str}"
            except Exception as e:
                logger.error(f"❌ Sprite transparency processing failed: {e}")
                return image_data_url
        return image_data_url

    def health_check(self) -> dict:
        return {
            "status": "online" if self.pipe or self._img2img_pipe or self._inpaint_pipe else "offline", 
            "engine": "diffusers", 
            "model": self.model_id
        }
