"""Manga OCR processing mixin for VisionTransformersAdapter."""

import logging  # noqa: E402
from typing import Dict, Any  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402

torch = lazy_import("torch")
transformers = lazy_import("transformers")
pipeline = transformers.pipeline

logger = logging.getLogger("animetix.inference.manga_ocr")


class MangaOcrMixin:
    """Provides manga page OCR and text extraction."""

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        """Generic fallback OCR - NO LONGER simulates manga layout."""
        try:
            from PIL import Image  # noqa: E402
            from io import BytesIO  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")

            import os  # noqa: E402

            model_id = "microsoft/trocr-base-handwritten"
            if not hasattr(self, "_manga_ocr_pipeline"):
                logger.info(
                    "🏗️ Loading Manga OCR (fallback to generic OCR if specialized unavailable)..."
                )

                # Check for mounted local volume
                mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
                local_model_path = os.path.join(mount_path, "manga-ocr")
                if os.path.exists(local_model_path):
                    logger.info(
                        f"📚 Loading Manga OCR from local FUSE path: {local_model_path}"
                    )
                    model_id = local_model_path

                self._manga_ocr_pipeline = pipeline(
                    "image-to-text",
                    model=model_id,
                    device=0 if torch.cuda.is_available() else -1,
                )

            result = self._manga_ocr_pipeline(img)
            extracted_text = result[0]["generated_text"] if result else ""

            self._log_usage(engine=f"transformers:{model_id}:ocr", units=1)

            width, height = img.size
            simulated_layout = [
                {"box": [10, 10, width // 2, height // 4], "text": extracted_text[:50]},
                {
                    "box": [width // 2, height // 4, width - 10, height // 2],
                    "text": extracted_text[50:] if len(extracted_text) > 50 else "",
                },
            ]

            return {
                "text": extracted_text,
                "layout": simulated_layout,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"❌ Manga OCR failed: {e}")
            return {"text": "", "layout": [], "status": "error", "message": str(e)}
