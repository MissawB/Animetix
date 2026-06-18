"""VLM (Visual Language Model) and Object Detection mixin for Inference adapters."""

import logging  # noqa: E402
from typing import Optional, List, Dict  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402

torch = lazy_import("torch")
transformers = lazy_import("transformers")
pipeline = lazy_import("transformers.pipeline")

logger = logging.getLogger("animetix.inference.vlm_mixin")


class VlmMixin:
    """Provides local VLM description and object detection capabilities."""

    def detect_objects(
        self,
        image_data: bytes,
        candidate_queries: List[str],
        model_id: Optional[str] = None,
    ) -> List[Dict]:
        """Détecte des objets via OwlViT."""
        try:
            from PIL import Image  # noqa: E402
            from io import BytesIO  # noqa: E402
            from transformers import pipeline  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")
            detector_id = model_id or "google/owlv2-base-patch16-ensemble"

            if not hasattr(self, "_detector_pipeline"):
                logger.info(f"🏗️ Loading Object Detector: {detector_id}")
                self._detector_pipeline = pipeline(
                    "zero-shot-object-detection",
                    model=detector_id,
                    device=0 if torch.cuda.is_available() else -1,
                )

            results = self._detector_pipeline(
                img, candidate_labels=candidate_queries, threshold=0.05
            )
            self._log_usage(engine=f"transformers:{detector_id}", units=1)

            return [
                {
                    "label": res["label"],
                    "score": res["score"],
                    "box": [
                        res["box"]["xmin"],
                        res["box"]["ymin"],
                        res["box"]["xmax"],
                        res["box"]["ymax"],
                    ],
                }
                for res in results
            ]
        except Exception as e:
            logger.error(f"❌ Local Object Detection failed: {e}")
            return []

    def generate_image_description(
        self, image_data: bytes, prompt: str = "Décris cette image d'anime."
    ) -> str:
        """Génère une description d'image via SmolVLM."""
        try:
            from PIL import Image  # noqa: E402
            from io import BytesIO  # noqa: E402
            from transformers import AutoModelForVision2Seq, AutoProcessor  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")
            vlm_id = "HuggingFaceTB/SmolVLM-Instruct"

            if not hasattr(self, "_vlm_model"):
                logger.info(f"🏗️ Loading Local VLM: {vlm_id}")
                self._vlm_processor = AutoProcessor.from_pretrained(
                    vlm_id, revision="main"
                )  # nosec B615
                self._vlm_model = AutoModelForVision2Seq.from_pretrained(
                    vlm_id,
                    revision="main",
                    trust_remote_code=True,  # nosec B615
                    torch_dtype=torch.bfloat16
                    if torch.cuda.is_available()
                    else torch.float32,
                ).to("cuda" if torch.cuda.is_available() else "cpu")

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "image"}, {"type": "text", "text": prompt}],
                }
            ]

            text = self._vlm_processor.apply_chat_template(
                messages, add_generation_prompt=True
            )
            inputs = self._vlm_processor(
                text=text, images=[img], return_tensors="pt"
            ).to(self._vlm_model.device)

            generated_ids = self._vlm_model.generate(**inputs, max_new_tokens=512)
            res = self._vlm_processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

            if "Assistant:" in res:
                res = res.split("Assistant:")[-1].strip()

            self._log_usage(engine=f"transformers:{vlm_id}", units=1)
            return res
        except Exception as e:
            logger.error(f"❌ Local Image description failed: {e}")
            return "Échec description locale."
