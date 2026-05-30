import logging
from typing import Dict, Any, List, Optional
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from transformers import pipeline
from core.domain.exceptions import InferenceError

logger = logging.getLogger("animetix.inference")

class MangaOCRAdapter(InferencePort):
    """
    Adaptateur spécialisé pour l'OCR de mangas utilisant LightonOCR.
    """
    def __init__(self, model_id: str = "Remidesbois/LightonOCR-2-1b-poneglyph-bbox", usage_port: Optional[UsagePort] = None):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        try:
            self.ocr_pipeline = pipeline("image-to-text", model=self.model_id, trust_remote_code=True)
        except Exception as e:
            logger.error(f"Failed to load Manga OCR model {model_id}: {e}")
            self.ocr_pipeline = None

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        if not self.ocr_pipeline:
            raise InferenceError("Manga OCR model not loaded.")
        try:
            # Conversion bytes -> PIL Image possible ici si nécessaire
            results = self.ocr_pipeline(image_data)

            # Formatting the output to match MangaFlowService expectations
            main_res = results[0] if isinstance(results, list) else results
            layout = main_res.get('layout', [])

            if not layout and main_res.get('generated_text'):
                 layout = [{"text": main_res.get('generated_text'), "bbox": [10, 10, 500, 500]}]

            self._log_usage(engine="local:manga_ocr", units=1)

            return {
                "text": main_res.get('generated_text', ""), 
                "layout": layout,
                "raw": results,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Manga OCR processing failed: {e}")
            raise InferenceError(f"Manga OCR processing failed: {e}")

    def health_check(self) -> dict: return {"status": "online" if self.ocr_pipeline else "offline", "engine": "LightonOCR"}
