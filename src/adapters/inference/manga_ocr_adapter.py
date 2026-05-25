import logging
from typing import Dict, Any, List
from core.ports.inference_port import InferencePort
from transformers import pipeline

logger = logging.getLogger("animetix.inference")

class MangaOCRAdapter(InferencePort):
    """
    Adaptateur spécialisé pour l'OCR de mangas utilisant LightonOCR.
    """
    def __init__(self, model_id: str = "Remidesbois/LightonOCR-2-1b-poneglyph-bbox"):
        self.model_id = model_id
        try:
            self.ocr_pipeline = pipeline("image-to-text", model=self.model_id, trust_remote_code=True)
        except Exception as e:
            logger.error(f"Failed to load Manga OCR model {model_id}: {e}")
            self.ocr_pipeline = None

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        if not self.ocr_pipeline:
            return {"error": "OCR model not loaded"}
        try:
            # Conversion bytes -> PIL Image possible ici si nécessaire
            results = self.ocr_pipeline(image_data)
            return {"text": results[0].get('generated_text', ""), "raw": results}
        except Exception as e:
            logger.error(f"Manga OCR processing failed: {e}")
            return {"error": str(e)}

    def health_check(self) -> dict: return {"status": "online" if self.ocr_pipeline else "offline", "engine": "LightonOCR"}
