import logging
import os
from io import BytesIO
from typing import Any, Dict

from adapters.inference.components.context import InferenceComponentContext
from core.utils.lazy_import import lazy_import

torch = lazy_import("torch")
transformers = lazy_import("transformers")

logger = logging.getLogger("animetix.inference.manga_ocr_component")


class MangaOcrComponent:
    """Manga page OCR / text extraction, composable.

    Logic copied verbatim from MangaOcrMixin; ``self._log_usage`` is replaced by
    the injected context and the lazy pipeline cache lives on the component.
    """

    def __init__(self, ctx: InferenceComponentContext):
        self._ctx = ctx
        self._pipeline: Any = None

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        try:
            from PIL import Image  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")

            model_id = "microsoft/trocr-base-handwritten"
            if self._pipeline is None:
                logger.info(
                    "🏗️ Loading Manga OCR (fallback to generic OCR if specialized unavailable)..."
                )
                mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
                local_model_path = os.path.join(mount_path, "manga-ocr")
                if os.path.exists(local_model_path):
                    logger.info(
                        f"📚 Loading Manga OCR from local FUSE path: {local_model_path}"
                    )
                    model_id = local_model_path

                self._pipeline = transformers.pipeline(
                    "image-to-text",
                    model=model_id,
                    device=0 if torch.cuda.is_available() else -1,
                )

            result = self._pipeline(img)
            extracted_text = result[0]["generated_text"] if result else ""

            self._ctx.log_usage(engine=f"transformers:{model_id}:ocr", units=1)

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
