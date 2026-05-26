import logging
import base64
import os
import tempfile
from io import BytesIO
from typing import Optional, List, Dict, Any
from PIL import Image
from core.ports.inference_port import InferencePort
from core.ports.usage_port import UsagePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
np = lazy_import('numpy')
imageio = lazy_import('imageio')

logger = logging.getLogger("animetix.inference.diffusers")

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
        self.model_id = model_id
        self.use_fp16 = use_fp16
        self.usage_port = usage_port
        self.pipe = None
        self._img2img_pipe = None
        self._depth_pipe = None

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

    def generate_image(self, prompt: str, style: str = "") -> str:
        self._load_txt2img()
        if not self.pipe: return "Erreur: Modèle non chargé."
        try:
            num_steps = 1 if "turbo" in self.model_id.lower() else 30
            guidance_scale = 0.0 if "turbo" in self.model_id.lower() else 7.5
            image = self.pipe(prompt=f"{prompt}, {style}", num_inference_steps=num_steps, guidance_scale=guidance_scale).images[0]
            buffered = BytesIO(); image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            logger.error(f"❌ Image Generation failed: {e}"); return f"Erreur: {e}"

    def estimate_depth(self, image_data: bytes) -> bytes:
        try:
            from transformers import pipeline
            if not self._depth_pipe:
                logger.info("🏗️ Loading Depth Model: LiheYoung/depth-anything-small-hf")
                self._depth_pipe = pipeline("depth-estimation", model="LiheYoung/depth-anything-small-hf", device=0 if torch.cuda.is_available() else -1)
            img = Image.open(BytesIO(image_data))
            result = self._depth_pipe(img)
            buf = BytesIO(); result["depth"].save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"❌ Depth Estimation failed: {e}"); return b""

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
            buf = BytesIO(); res.save(buf, format="JPEG")
            return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Image to Anime failed: {e}"); return ""

    def transform_video_to_anime(self, video_data: bytes, studio_style: str = "", prompt: str = "") -> str:
        try:
            import imageio
            import numpy as np
            self._load_img2img()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
                tmp_in.write(video_data); tmp_in_path = tmp_in.name
            reader = imageio.get_reader(tmp_in_path)
            fps = reader.get_meta_data()['fps']
            frames = []
            max_frames = 10
            for i, frame in enumerate(reader):
                if i >= max_frames: break
                pil_img = Image.fromarray(frame).resize((512, 512))
                styled = self._img2img_pipe(prompt=f"anime style, {studio_style}, {prompt}", image=pil_img, strength=0.5, num_inference_steps=2).images[0]
                frames.append(np.array(styled))
            reader.close(); os.unlink(tmp_in_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                tmp_out_path = tmp_out.name
                writer = imageio.get_writer(tmp_out_path, fps=fps)
                for f in frames: writer.append_data(f)
                writer.close()
            with open(tmp_out_path, "rb") as f:
                res_base64 = base64.b64encode(f.read()).decode("utf-8")
            os.unlink(tmp_out_path)
            return f"data:video/mp4;base64,{res_base64}"
        except Exception as e:
            logger.error(f"❌ Video to Anime failed: {e}"); return ""

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict:
        try:
            import struct
            import numpy as np
            rgb = Image.open(BytesIO(image_data)).convert("RGB").resize((256, 256))
            depth = Image.open(BytesIO(depth_map)).convert("L").resize((256, 256))
            rgb_arr, depth_arr = np.array(rgb), np.array(depth)
            h, w = depth_arr.shape
            points = []
            fx, fy = 200.0, 200.0
            cx, cy = w / 2, h / 2
            for y in range(h):
                for x in range(w):
                    z = float(depth_arr[y, x]) / 255.0
                    if z <= 0.05: continue
                    X, Y, Z = (x - cx) * z / fx, (y - cy) * z / fy, z
                    r, g, b = rgb_arr[y, x]
                    points.append((X, Y, Z, r, g, b))
            header = f"ply\nformat binary_little_endian 1.0\nelement vertex {len(points)}\nproperty float x\nproperty float y\nproperty float z\nproperty uint8 red\nproperty uint8 green\nproperty uint8 blue\nend_header\n"
            ply_data = header.encode('ascii')
            for p in points: ply_data += struct.pack("<fffBBB", *p)
            return {"status": "success", "model_url": f"data:application/octet-stream;base64,{base64.b64encode(ply_data).decode('utf-8')}", "viewer_type": "point_cloud", "point_count": len(points)}
        except Exception as e:
            logger.error(f"❌ 3D Scene failed: {e}"); return {"status": "error", "message": str(e)}

    def health_check(self) -> dict:
        return {"status": "online" if self.pipe or self._img2img_pipe else "offline", "engine": "diffusers", "model": self.model_id}
