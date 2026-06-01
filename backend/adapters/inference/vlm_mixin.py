"""VLM (Visual Language Model) and Object Detection mixin for Inference adapters."""
import logging
from typing import Optional, List, Dict, Any
from core.utils.lazy_import import lazy_import
from core.domain.exceptions import InferenceError

torch = lazy_import('torch')
transformers = lazy_import('transformers')
pipeline = lazy_import('transformers.pipeline')

logger = logging.getLogger("animetix.inference.vlm_mixin")

class VlmMixin:
    """Provides local VLM description and object detection capabilities."""

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """Détecte des objets via OwlViT."""
        try:
            from PIL import Image
            from io import BytesIO
            from transformers import pipeline
            img = Image.open(BytesIO(image_data)).convert("RGB")
            detector_id = model_id or "google/owlvit-base-patch32"
            
            if not hasattr(self, '_detector_pipeline'):
                logger.info(f"🏗️ Loading Object Detector: {detector_id}")
                self._detector_pipeline = pipeline(
                    "zero-shot-object-detection", 
                    model=detector_id, 
                    device=0 if torch.cuda.is_available() else -1
                )
            
            results = self._detector_pipeline(img, candidate_labels=candidate_queries, threshold=0.05)
            self._log_usage(engine=f"transformers:{detector_id}", units=1)

            return [
                {
                    "label": res["label"], 
                    "score": res["score"], 
                    "box": [res["box"]["xmin"], res["box"]["ymin"], res["box"]["xmax"], res["box"]["ymax"]]
                } for res in results
            ]
        except Exception as e:
            logger.error(f"❌ Local Object Detection failed: {e}")
            return []

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime.") -> str:
        """Génère une description d'image via Moondream2."""
        try:
            from PIL import Image
            from io import BytesIO
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            img = Image.open(BytesIO(image_data)).convert("RGB")
            vlm_id = "vikhyatk/moondream2"
            
            if not hasattr(self, '_vlm_model'):
                logger.info(f"🏗️ Loading Local VLM: {vlm_id}")
                self._vlm_tokenizer = AutoTokenizer.from_pretrained(vlm_id)
                self._vlm_model = AutoModelForCausalLM.from_pretrained(
                    vlm_id, trust_remote_code=True
                ).to("cuda" if torch.cuda.is_available() else "cpu")
            
            enc_image = self._vlm_model.encode_image(img)
            res = self._vlm_model.answer_question(enc_image, prompt, self._vlm_tokenizer)

            self._log_usage(engine=f"transformers:{vlm_id}", units=1)
            return res
        except Exception as e:
            logger.error(f"❌ Local Image description failed: {e}")
            return "Échec description locale."
