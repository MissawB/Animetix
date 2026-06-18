"""CLIP and ColPali vision mixin for VisionTransformersAdapter."""

import logging  # noqa: E402
import httpx  # noqa: E402
import asyncio  # noqa: E402
from typing import Optional, List, Dict, Any  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402
from core.domain.exceptions import InferenceError  # noqa: E402
from core.utils.security import safe_http_request, safe_http_request_async  # noqa: E402

torch = lazy_import("torch")

logger = logging.getLogger("animetix.inference.clip_vision")


class ClipVisionMixin:
    """Provides CLIP-based similarity, classification, reranking, and ColPali late interaction."""

    def get_image_embedding(
        self, image_data: bytes, model_id: Optional[str] = None
    ) -> List[float]:
        try:
            from PIL import Image  # noqa: E402
            from io import BytesIO  # noqa: E402
            from sentence_transformers import SentenceTransformer  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")
            model_name = "clip-ViT-B-32"
            if not hasattr(self, "_clip_model"):
                self._clip_model = SentenceTransformer(model_name)

            self._log_usage(engine=f"transformers:{model_name}:embedding", units=1)

            return self._clip_model.encode(img).tolist()
        except Exception as e:
            logger.error(f"❌ Image Embedding failed: {e}")
            return []

    def classify_image(
        self,
        image_data: bytes,
        candidate_labels: List[str],
        model_id: Optional[str] = None,
    ) -> Dict[str, float]:
        try:
            from sentence_transformers import util  # noqa: E402

            img_emb = torch.tensor(self.get_image_embedding(image_data))
            model_name = "clip-ViT-B-32"
            if not hasattr(self, "_clip_model"):
                from sentence_transformers import SentenceTransformer  # noqa: E402

                self._clip_model = SentenceTransformer(model_name)
            text_embs = torch.tensor(self._clip_model.encode(candidate_labels))
            scores = util.cos_sim(img_emb, text_embs)[0]
            probs = torch.nn.functional.softmax(scores, dim=0).tolist()

            self._log_usage(engine=f"transformers:{model_name}:classify", units=1)

            return {label: p for label, p in zip(candidate_labels, probs)}
        except Exception as e:
            logger.error(f"❌ Image Classification failed: {e}")
            return {}

    def calculate_visual_similarity(
        self, query: str, item_id: str, media_type: str
    ) -> float:
        try:
            from sentence_transformers import util  # noqa: E402

            model_name = "clip-ViT-B-32"
            if not hasattr(self, "_clip_model"):
                from sentence_transformers import SentenceTransformer  # noqa: E402

                self._clip_model = SentenceTransformer(model_name)

            query_emb = self._clip_model.encode(query, convert_to_tensor=True)
            item_emb = self._clip_model.encode(item_id, convert_to_tensor=True)

            similarity = util.cos_sim(query_emb, item_emb).item()

            self._log_usage(engine=f"transformers:{model_name}:similarity", units=1)

            return float(similarity)
        except Exception as e:
            logger.error(f"❌ Visual similarity calculation failed: {e}")
            return (
                1.0
                if query.lower() in item_id.lower() or item_id.lower() in query.lower()
                else 0.5
            )

    def _load_clip_model(self):
        if hasattr(self, "_clip_model"):
            return
        try:
            from sentence_transformers import SentenceTransformer  # noqa: E402

            logger.info("🏗️ Loading CLIP for reranking...")
            self._clip_model = SentenceTransformer("clip-ViT-B-32")
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP: {e}")
            raise InferenceError(f"Critical failure during CLIP loading: {str(e)}")

    async def _fetch_images(self, urls: List[str]) -> List[Any]:
        tasks = [self._fetch_single_image(None, url) for url in urls]
        return await asyncio.gather(*tasks)

    async def _fetch_single_image(
        self, client: Optional[httpx.AsyncClient], url: str
    ) -> Optional[Any]:
        try:
            from PIL import Image  # noqa: E402
            from io import BytesIO  # noqa: E402

            # Utilisation de safe_http_request_async pour validation SSRF des redirections
            response = await safe_http_request_async("GET", url, timeout=10)
            if response.status_code == 200:
                content = response.content
                return Image.open(BytesIO(content)).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to fetch image {url}: {e}")
        return None

    def _fetch_images_sync(self, urls: List[str]) -> List[Any]:
        from PIL import Image  # noqa: E402
        from io import BytesIO  # noqa: E402

        results = []
        for url in urls:
            try:
                # Utilisation de safe_http_request pour validation SSRF des redirections
                res = safe_http_request("GET", url, timeout=10)
                if res.status_code == 200:
                    results.append(Image.open(BytesIO(res.content)).convert("RGB"))
                else:
                    results.append(None)
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                results.append(None)
        return results

    def visual_rerank(
        self, query: str, image_urls: List[str], system_prompt: str = ""
    ) -> List[Dict[str, Any]]:
        """Reranking visuel via CLIP (Sync)."""
        from sentence_transformers import util  # noqa: E402

        self._load_clip_model()
        images = self._fetch_images_sync(image_urls)

        valid_images = [img for img in images if img is not None]
        # Image URLs mapping
        valid_idx_to_orig_idx = [i for i, img in enumerate(images) if img is not None]

        if not valid_images:
            return []

        query_emb = self._clip_model.encode(query, convert_to_tensor=True)
        img_embs = self._clip_model.encode(valid_images, convert_to_tensor=True)

        scores = util.cos_sim(query_emb, img_embs)[0]

        self._log_usage(engine="transformers:clip:visual_rerank", units=1)

        results = []
        for i, score_tensor in enumerate(scores):
            orig_idx = valid_idx_to_orig_idx[i]
            results.append(
                {
                    "index": orig_idx,
                    "url": image_urls[orig_idx],
                    "score": float(score_tensor),
                }
            )

        return sorted(results, key=lambda x: x["score"], reverse=True)

    def _load_colpali_engine(self):
        """Chargement paresseux de ColPali."""
        if hasattr(self, "_colpali_model"):
            return
        try:
            from colpali_engine.models import ColPali, ColPaliProcessor  # noqa: E402

            logger.info("🏗️ Loading ColPali for Late Interaction...")
            model_id = "vidore/colpali-v1.2"

            self._colpali_model = ColPali.from_pretrained(
                model_id,
                torch_dtype=torch.float16
                if torch.cuda.is_available()
                else torch.float32,
                device_map="auto",
            )
            self._colpali_processor = ColPaliProcessor.from_pretrained(model_id)
            logger.info("✅ ColPali engine loaded.")
        except Exception as e:
            logger.error(f"❌ Failed to load ColPali: {e}")
            raise InferenceError(f"ColPali engine loading failed: {str(e)}")

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Implémentation réelle ColPali late interaction."""
        try:
            from PIL import Image  # noqa: E402
            from io import BytesIO  # noqa: E402

            self._load_colpali_engine()
            img = Image.open(BytesIO(image_data)).convert("RGB")

            with torch.no_grad():
                batch = self._colpali_processor.process_images([img]).to(
                    self._colpali_model.device
                )
                embeddings = self._colpali_model(**batch)

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self._log_usage(engine="transformers:colpali:late_interaction", units=1)

            return embeddings.cpu().tolist()
        except Exception as e:
            logger.error(f"❌ ColPali inference failed: {e}")
            raise InferenceError(f"ColPali inference failed: {str(e)}")
