try:
    from animetix_project.logging_config import get_logger
except ImportError:
    import logging
    def get_logger(name: str = __name__) -> logging.Logger:
        return logging.getLogger(name)

import base64
import os
import tempfile
from io import BytesIO
from typing import Optional, List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
np = lazy_import('numpy')
imageio = lazy_import('imageio')

logger = get_logger(__name__)

class DiffusersAdapter(InferencePort):
    """
    Adaptateur local pour la génération d'images utilisant la bibliothèque Diffusers.
    Supporte Text-to-Image, Image-to-Image, Video-to-Anime et Estimation de Profondeur.
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
        self._depth_pipe = None
        self._inpaint_pipe = None

    def _get_dtype(self):
        return torch.float16 if (self.use_fp16 and torch.cuda.is_available()) else torch.float32

    def _get_variant(self):
        return "fp16" if self._get_dtype() == torch.float16 else None

    def _load_txt2img(self):
        if self.pipe: return
        try:
            from diffusers import AutoPipelineForText2Image
            logger.info(f"🏗️ Loading Local Diffusion Model (Txt2Img): {self.model_id}")
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                self.model_id, 
                torch_dtype=self._get_dtype(), 
                variant=self._get_variant(),
                trust_remote_code=True
            )
            if torch.cuda.is_available():
                self.pipe.to("cuda")
                self.pipe.enable_model_cpu_offload()
                self.pipe.enable_vae_tiling()
        except Exception as e:
            logger.error(f"❌ Failed to load txt2img model: {e}")

    def _load_img2img(self):
        if self._img2img_pipe: return
        try:
            from diffusers import AutoPipelineForImage2Image
            logger.info(f"🏗️ Loading Local Diffusion Model (Img2Img): {self.model_id}")
            self._img2img_pipe = AutoPipelineForImage2Image.from_pretrained(
                self.model_id, 
                torch_dtype=self._get_dtype(), 
                variant=self._get_variant(),
                trust_remote_code=True
            )
            if torch.cuda.is_available():
                self._img2img_pipe.to("cuda")
                self._img2img_pipe.enable_model_cpu_offload()
        except Exception as e:
            logger.error(f"❌ Failed to load img2img model: {e}")

    def _load_inpainting(self):
        if self._inpaint_pipe: return
        try:
            from diffusers import AutoPipelineForInpainting
            logger.info(f"🏗️ Loading Local Diffusion Model (Inpainting): {self.model_id}")
            self._inpaint_pipe = AutoPipelineForInpainting.from_pretrained(
                self.model_id, 
                torch_dtype=self._get_dtype(), 
                variant=self._get_variant(),
                trust_remote_code=True
            )
            if torch.cuda.is_available():
                self._inpaint_pipe.to("cuda")
                self._inpaint_pipe.enable_model_cpu_offload()
                self._inpaint_pipe.enable_vae_tiling()
        except Exception as e:
            logger.error(f"❌ Failed to load inpainting model: {e}")

    def generate_image(self, prompt: str, style: str = "") -> str:
        self._load_txt2img()
        if not self.pipe:
            raise InferenceError("Model not loaded for txt2img generation.")
        try:
            num_steps = 1 if "turbo" in self.model_id.lower() else 30
            guidance_scale = 0.0 if "turbo" in self.model_id.lower() else 7.5
            image = self.pipe(prompt=f"{prompt}, {style}", num_inference_steps=num_steps, guidance_scale=guidance_scale).images[0]
            
            self._log_usage(engine=f"diffusers:{self.model_id}:txt2img", units=1)
            
            buffered = BytesIO(); image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            logger.error(f"❌ Image Generation failed: {e}"); return f"Erreur: {e}"

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """
        Génère un sprite de personnage sur fond blanc et tente de le rendre transparent.
        """
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

    def estimate_depth(self, image_data: bytes) -> bytes:
        try:
            from transformers import pipeline
            model_id = "LiheYoung/depth-anything-small-hf"
            if not self._depth_pipe:
                logger.info(f"🏗️ Loading Depth Model: {model_id}")
                self._depth_pipe = pipeline("depth-estimation", model=model_id, device=0 if torch.cuda.is_available() else -1)
            img = Image.open(BytesIO(image_data))
            result = self._depth_pipe(img)
            
            self._log_usage(engine=f"transformers:{model_id}", units=1)
            
            buf = BytesIO(); result["depth"].save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"❌ Depth Estimation failed: {e}"); raise InferenceError(f"Depth estimation failed: {e}")

    def transform_image_to_anime(self, image_data: bytes, studio_style: str = "", prompt: str = "") -> str:
        try:
            self._load_img2img()
            pil_img = Image.open(BytesIO(image_data)).convert("RGB").resize((512, 512))
            res = self._img2img_pipe(
                prompt=f"anime style, {studio_style}, {prompt}", 
                image=pil_img, 
                strength=0.5, 
                num_inference_steps=2 if "turbo" in self.model_id.lower() else 20
            ).images[0]
            
            self._log_usage(engine=f"diffusers:{self.model_id}:img2img", units=1)
            
            buf = BytesIO(); res.save(buf, format="JPEG")
            return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Image to Anime failed: {e}"); return ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str = "", prompt: str = "") -> str:
        """SOTA Video-to-Anime with simulated temporal consistency."""
        try:
            import imageio
            import numpy as np
            self._load_img2img()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
                tmp_in.write(video_data)
                tmp_in_path = tmp_in.name

            reader = imageio.get_reader(tmp_in_path)
            fps = reader.get_meta_data()['fps']
            frames = []
            max_frames = 10

            # Simulated Temporal Consistency: reuse a base latent or seed
            generator = torch.Generator(device=self._img2img_pipe.device).manual_set(42)

            for i, frame in enumerate(reader):
                if i >= max_frames: break
                pil_img = Image.fromarray(frame).resize((512, 512))
                # Using the same generator seed helps consistency across similar frames in img2img
                styled = self._img2img_pipe(
                    prompt=f"anime style, masterpiece, {studio_style}, {prompt}",
                    image=pil_img,
                    strength=0.5,
                    num_inference_steps=2,
                    generator=generator
                ).images[0]
                frames.append(np.array(styled))

            reader.close()
            os.unlink(tmp_in_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                tmp_out_path = tmp_out.name
                writer = imageio.get_writer(tmp_out_path, fps=fps)
                for f in frames: writer.append_data(f)
                writer.close()

            with open(tmp_out_path, "rb") as f:
                res_base64 = base64.b64encode(f.read()).decode("utf-8")
            os.unlink(tmp_out_path)

            self._log_usage(engine=f"diffusers:{self.model_id}:vid2anime_sota", units=1)
            return f"data:video/mp4;base64,{res_base64}"
        except Exception as e:
            logger.error(f"❌ Video to Anime failed: {e}")
            return ""

    def inpaint_text_bubbles(self, image_data: bytes, bubbles: List[Dict]) -> str:
        """
        Nettoie les bulles de texte via inpainting et réinscrit le nouveau texte.
        """
        try:
            self._load_inpainting()
            if not self._inpaint_pipe: return "Erreur: Modèle d'inpainting non chargé."
            
            init_image = Image.open(BytesIO(image_data)).convert("RGB")
            width, height = init_image.size
            
            # 1. Création du masque d'inpainting
            mask_image = Image.new("L", (width, height), 0)
            draw_mask = ImageDraw.Draw(mask_image)
            for bubble in bubbles:
                bbox = bubble.get('bbox') # [x1, y1, x2, y2]
                if bbox:
                    # On ajoute une petite marge pour bien couvrir le texte
                    draw_mask.rectangle(bbox, fill=255)
            
            # 2. Inpainting pour effacer le texte existant
            num_steps = 4 if "turbo" in self.model_id.lower() else 25
            inpainted_image = self._inpaint_pipe(
                prompt="clean manga bubble, no text, white background",
                image=init_image,
                mask_image=mask_image,
                num_inference_steps=num_steps
            ).images[0]
            
            # 3. Dessin du nouveau texte
            draw_final = ImageDraw.Draw(inpainted_image)
            try:
                # Tentative de chargement d'une police systeme
                font = ImageFont.truetype("arial.ttf", 20)
            except Exception:
                logger.info("System font 'arial.ttf' not found, falling back to default image font.")
                font = ImageFont.load_default()

            for bubble in bubbles:
                bbox = bubble.get('bbox')
                text = bubble.get('text')
                if bbox and text:
                    x1, y1, x2, y2 = bbox
                    # Calcul pour centrer le texte dans la bubble
                    t_bbox = draw_final.textbbox((0, 0), text, font=font)
                    t_w, t_h = t_bbox[2] - t_bbox[0], t_bbox[3] - t_bbox[1]
                    pos_x = (x1 + x2) / 2 - t_w / 2
                    pos_y = (y1 + y2) / 2 - t_h / 2
                    draw_final.text((pos_x, pos_y), text, fill="black", font=font)

            # --- Accounting ---
            self._log_usage(engine=f"diffusers:{self.model_id}:inpaint", units=1)

            buffered = BytesIO()
            inpainted_image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{img_str}"

        except Exception as e:
            logger.error(f"❌ Inpaint Text Bubbles failed: {e}")
            return f"Erreur: {e}"


    def health_check(self) -> dict:
        return {"status": "online" if self.pipe or self._img2img_pipe else "offline", "engine": "diffusers", "model": self.model_id}
