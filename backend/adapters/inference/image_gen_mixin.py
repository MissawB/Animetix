"""Image generation and transformation mixin for Inference adapters."""

import base64  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
from io import BytesIO  # noqa: E402
from typing import TYPE_CHECKING, Dict, List  # noqa: E402

from core.domain.exceptions import InferenceError  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402
from core.utils.model_registry import (  # noqa: E402
    resolve_trust_remote_code,
    trusted_revision,
)

torch = lazy_import("torch")
np = lazy_import("numpy")
imageio = lazy_import("imageio")
Image = lazy_import("PIL.Image")
ImageDraw = lazy_import("PIL.ImageDraw")
ImageFont = lazy_import("PIL.ImageFont")

import logging  # noqa: E402

logger = logging.getLogger("animetix.inference.image_gen_mixin")


class CrossFrameAttentionProcessor:
    """Processor for Cross-Frame Attention to maintain appearance consistency."""

    def __init__(self, unet_chunk_size=2):
        self.unet_chunk_size = unet_chunk_size

    def __call__(
        self, attn, hidden_states, encoder_hidden_states=None, attention_mask=None
    ):
        batch_size, sequence_length, _ = hidden_states.shape
        if encoder_hidden_states is None:
            encoder_hidden_states = hidden_states
        if encoder_hidden_states is not None:
            anchor_frame = encoder_hidden_states[0:1].expand(batch_size, -1, -1)
            encoder_hidden_states = torch.cat(
                [encoder_hidden_states, anchor_frame], dim=1
            )
        return attn.processor.__call__(
            attn, hidden_states, encoder_hidden_states, attention_mask
        )


class ImageGenMixin:
    """Provides image generation, transformation, and inpainting capabilities."""

    if TYPE_CHECKING:

        def _log_usage(
            self,
            engine: str,
            input_tokens: int = 0,
            output_tokens: int = 0,
            units: int = 0,
            allocated_budget: int = 0,
        ) -> None: ...

    def _get_dtype(self):
        return torch.float16 if torch.cuda.is_available() else torch.float32

    def _get_variant(self):
        return "fp16" if self._get_dtype() == torch.float16 else None

    def _load_txt2img(self):
        if not torch.cuda.is_available():
            raise InferenceError("CUDA GPU is not available for local diffusion.")
        if hasattr(self, "pipe") and self.pipe:
            return
        try:
            from diffusers import AutoPipelineForText2Image  # noqa: E402

            model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
            logger.info(f"🏗️ Loading Txt2Img: {model_id}")
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                model_id,
                torch_dtype=self._get_dtype(),
                variant=self._get_variant(),
                trust_remote_code=resolve_trust_remote_code(model_id),
                revision=trusted_revision(model_id) or "main",
            )
            self.pipe.to("cuda")
            self.pipe.enable_model_cpu_offload()
            self.pipe.enable_vae_tiling()
        except Exception as e:
            logger.error(f"❌ Failed to load txt2img: {e}")

    def _load_img2img(self):
        if not torch.cuda.is_available():
            raise InferenceError("CUDA GPU is not available for local diffusion.")
        if hasattr(self, "_img2img_pipe") and self._img2img_pipe:
            return
        try:
            from diffusers import AutoPipelineForImage2Image  # noqa: E402

            model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
            logger.info(f"🏗️ Loading Img2Img: {model_id}")
            self._img2img_pipe = AutoPipelineForImage2Image.from_pretrained(
                model_id,
                torch_dtype=self._get_dtype(),
                variant=self._get_variant(),
                trust_remote_code=resolve_trust_remote_code(model_id),
                revision=trusted_revision(model_id) or "main",
            )
            self._img2img_pipe.to("cuda")
            self._img2img_pipe.enable_model_cpu_offload()
        except Exception as e:
            logger.error(f"❌ Failed to load img2img: {e}")

    def _load_inpainting(self):
        if not torch.cuda.is_available():
            raise InferenceError("CUDA GPU is not available for local diffusion.")
        if hasattr(self, "_inpaint_pipe") and self._inpaint_pipe:
            return
        try:
            from diffusers import AutoPipelineForInpainting  # noqa: E402

            model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
            logger.info(f"🏗️ Loading Inpainting: {model_id}")
            self._inpaint_pipe = AutoPipelineForInpainting.from_pretrained(
                model_id,
                torch_dtype=self._get_dtype(),
                variant=self._get_variant(),
                trust_remote_code=resolve_trust_remote_code(model_id),
                revision=trusted_revision(model_id) or "main",
            )
            self._inpaint_pipe.to("cuda")
            self._inpaint_pipe.enable_model_cpu_offload()
        except Exception as e:
            logger.error(f"❌ Failed to load inpainting: {e}")

    def generate_image(self, prompt: str, style: str = "") -> str:
        self._load_txt2img()
        try:
            model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
            num_steps = (
                4
                if "schnell" in model_id.lower()
                else 1 if "turbo" in model_id.lower() else 30
            )
            guidance_scale = (
                0.0
                if "schnell" in model_id.lower() or "turbo" in model_id.lower()
                else 7.5
            )
            image = self.pipe(
                prompt=f"{prompt}, {style}",
                num_inference_steps=num_steps,
                guidance_scale=guidance_scale,
            ).images[0]
            self._log_usage(engine=f"diffusers:{model_id}:txt2img", units=1)
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Image Gen failed: {e}")
            raise InferenceError(f"Image generation failed: {e}")

    def generate_sprite(self, prompt: str, style: str = "") -> str:
        """Génère un sprite de personnage sur fond blanc pour un détourage facile."""
        sprite_prompt = (
            f"character sprite, full body standing, anime style, {prompt}, "
            f"centered, isolated on pure white background, masterpiece, high quality, "
            f"game asset, concept art"
        )
        return self.generate_image(sprite_prompt, style)

    def transform_image_to_anime(
        self, image_data: bytes, studio_style: str = "", prompt: str = ""
    ) -> str:
        self._load_img2img()
        try:
            model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
            pil_img = Image.open(BytesIO(image_data)).convert("RGB").resize((512, 512))
            res = self._img2img_pipe(
                prompt=f"anime style, {studio_style}, {prompt}",
                image=pil_img,
                strength=0.5,
                num_inference_steps=2 if "turbo" in model_id.lower() else 20,
            ).images[0]
            self._log_usage(engine=f"diffusers:{model_id}:img2img", units=1)
            buf = BytesIO()
            res.save(buf, format="JPEG")
            return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Img2Anime failed: {e}")
            return ""

    def transform_video_to_anime(
        self, video_data: bytes, studio_style: str = "", prompt: str = ""
    ) -> str:
        self._load_img2img()
        try:
            from PIL import Image as PILImage  # noqa: E402

            reader = imageio.get_reader(BytesIO(video_data))
            fps = reader.get_meta_data().get("fps", 24)
            frames = [PILImage.fromarray(f).resize((512, 512)) for f in reader]
            reader.close()
            input_frames = frames[:8]
            attn_proc = CrossFrameAttentionProcessor(unet_chunk_size=len(input_frames))
            self._img2img_pipe.unet.set_attn_processor(attn_proc)
            model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
            styled_images = self._img2img_pipe(
                prompt=[f"anime style, {studio_style}, {prompt}"] * len(input_frames),
                image=input_frames,
                strength=0.6,
                num_inference_steps=20,
            ).images
            from diffusers.models.attention_processor import AttnProcessor  # noqa: E402

            self._img2img_pipe.unet.set_attn_processor(AttnProcessor())
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                writer = imageio.get_writer(tmp_out.name, fps=fps)
                for img in styled_images:
                    writer.append_data(np.array(img))
                writer.close()
                with open(tmp_out.name, "rb") as f:
                    res_base64 = base64.b64encode(f.read()).decode("utf-8")
            os.unlink(tmp_out.name)
            self._log_usage(
                engine=f"diffusers:{model_id}:fatezero_lite", units=len(input_frames)
            )
            return f"data:video/mp4;base64,{res_base64}"
        except Exception as e:
            logger.error(f"❌ Video2Anime failed: {e}")
            return ""

    def inpaint_text_bubbles(self, image_data: bytes, bubbles: List[Dict]) -> str:
        from PIL import (
            Image as PILImage,  # noqa: E402
            ImageDraw as PILImageDraw,
            ImageFont as PILImageFont,
        )

        try:
            init_image = PILImage.open(BytesIO(image_data)).convert("RGB")
            w, h = init_image.size
            try:
                self._load_inpainting()
            except Exception as e:
                logger.warning(
                    f"Could not load inpainting model, falling back to basic replacement: {e}"
                )
            if hasattr(self, "_inpaint_pipe") and self._inpaint_pipe:
                mask = PILImage.new("L", (w, h), 0)
                d = PILImageDraw.Draw(mask)
                for b in bubbles:
                    bbox = b.get("bbox")
                    if bbox:
                        d.rectangle(bbox, fill=255)
                model_id = getattr(self, "model_id", "black-forest-labs/FLUX.1-schnell")
                inpainted = self._inpaint_pipe(
                    prompt="clean manga bubble, no text, white background",
                    image=init_image,
                    mask_image=mask,
                    num_inference_steps=4 if "turbo" in model_id.lower() else 25,
                ).images[0]
            else:
                inpainted = init_image.copy()
                d = PILImageDraw.Draw(inpainted)
                for b in bubbles:
                    bbox = b.get("bbox")
                    if bbox:
                        d.rectangle(bbox, fill="white")
            d_final = PILImageDraw.Draw(inpainted)
            try:
                font = PILImageFont.truetype("arial.ttf", 20)
            except Exception:
                font = PILImageFont.load_default()
            for b in bubbles:
                bbox, text = b.get("bbox"), b.get("text")
                if bbox and text:
                    x1, y1, x2, y2 = bbox
                    t_bbox = d_final.textbbox((0, 0), text, font=font)
                    t_w, t_h = t_bbox[2] - t_bbox[0], t_bbox[3] - t_bbox[1]
                    d_final.text(
                        ((x1 + x2) / 2 - t_w / 2, (y1 + y2) / 2 - t_h / 2),
                        text,
                        fill="black",
                        font=font,
                    )
            buf = BytesIO()
            inpainted.save(buf, format="JPEG", quality=85)
            self._log_usage(engine="vision:inpaint", units=1)
            return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Inpaint failed: {e}")
            raise InferenceError(f"Inpainting failed: {e}")
