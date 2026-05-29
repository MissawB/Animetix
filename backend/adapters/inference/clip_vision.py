"""CLIP and ColPali vision mixin for VisionTransformersAdapter."""
import logging
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from core.utils.lazy_import import lazy_import
from core.domain.exceptions import InferenceError

torch = lazy_import('torch')

logger = logging.getLogger("animetix.inference.clip_vision")


class ClipVisionMixin:
    """Provides CLIP-based similarity, classification, reranking, and ColPali late interaction."""

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        try:
            from PIL import Image
            from io import BytesIO
            from sentence_transformers import SentenceTransformer
            img = Image.open(BytesIO(image_data)).convert("RGB")
            model_name = 'clip-ViT-B-32'
            if not hasattr(self, '_clip_model'):
                self._clip_model = SentenceTransformer(model_name)

            self._log_usage(engine=f"transformers:{model_name}:embedding", units=1)

            return self._clip_model.encode(img).tolist()
        except Exception as e:
            logger.error(f"❌ Image Embedding failed: {e}")
            return []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        try:
            from sentence_transformers import util
            img_emb = torch.tensor(self.get_image_embedding(image_data))
            model_name = 'clip-ViT-B-32'
            if not hasattr(self, '_clip_model'):
                from sentence_transformers import SentenceTransformer
                self._clip_model = SentenceTransformer(model_name)
            text_embs = torch.tensor(self._clip_model.encode(candidate_labels))
            scores = util.cos_sim(img_emb, text_embs)[0]
            probs = torch.nn.functional.softmax(scores, dim=0).tolist()

            self._log_usage(engine=f"transformers:{model_name}:classify", units=1)

            return {l: p for l, p in zip(candidate_labels, probs)}
        except Exception as e:
            logger.error(f"❌ Image Classification failed: {e}")
            return {}

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        try:
            from sentence_transformers import util
            model_name = 'clip-ViT-B-32'
            if not hasattr(self, '_clip_model'):
                from sentence_transformers import SentenceTransformer
                self._clip_model = SentenceTransformer(model_name)

            query_emb = self._clip_model.encode(query, convert_to_tensor=True)
            item_emb = self._clip_model.encode(item_id, convert_to_tensor=True)

            similarity = util.cos_sim(query_emb, item_emb).item()

            self._log_usage(engine=f"transformers:{model_name}:similarity", units=1)

            return float(similarity)
        except Exception as e:
            logger.error(f"❌ Visual similarity calculation failed: {e}")
            return 1.0 if query.lower() in item_id.lower() or item_id.lower() in query.lower() else 0.5

    def _load_clip_model(self):
        if hasattr(self, '_clip_model'):
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("🏗️ Loading CLIP for reranking...")
            self._clip_model = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP: {e}")
            raise InferenceError(f"Critical failure during CLIP loading: {str(e)}")

    async def _fetch_images(self, urls: List[str]) -> List[Any]:
        session = await self._get_session()
        tasks = [self._fetch_single_image(session, url) for url in urls]
        return await asyncio.gather(*tasks)

    async def _fetch_single_image(self, client: httpx.AsyncClient, url: str) -> Optional[Any]:
        try:
            from PIL import Image
            from io import BytesIO
            response = await client.get(url, timeout=10, follow_redirects=True)
            if response.status_code == 200:
                content = response.content
                return Image.open(BytesIO(content)).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to fetch image {url}: {e}")
        return None

    def _fetch_images_sync(self, urls: List[str]) -> List[Any]:
        from PIL import Image
        from io import BytesIO

        results = []
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            for url in urls:
                try:
                    res = client.get(url)
                    if res.status_code == 200:
                        results.append(Image.open(BytesIO(res.content)).convert("RGB"))
                    else:
                        results.append(None)
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                    results.append(None)
        return results

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]:
        """Reranking visuel via CLIP (Sync)."""
        from sentence_transformers import util

        self._load_clip_model()
        images = self._fetch_images_sync(image_urls)

        valid_images = [img for img in images if img is not None]
        valid_urls = [url for url, img in zip(image_urls, images) if img is not None]

        if not valid_images:
            return []

        query_emb = self._clip_model.encode(query, convert_to_tensor=True)
        img_embs = self._clip_model.encode(valid_images, convert_to_tensor=True)

        scores = util.cos_sim(query_emb, img_embs)[0]

        self._log_usage(engine="transformers:clip:visual_rerank", units=1)

        results = []
        valid_idx = 0
        for orig_idx, img in enumerate(images):
            if img is not None:
                score = float(scores[valid_idx])
                results.append({"index": orig_idx, "url": image_urls[orig_idx], "score": score})
                valid_idx += 1

        return sorted(results, key=lambda x: x["score"], reverse=True)

    def _load_colpali_engine(self):
        """Chargement paresseux de ColPali."""
        if hasattr(self, '_colpali_model'):
            return
        try:
            from colpali_engine.models import ColPali, ColPaliProcessor
            logger.info("🏗️ Loading ColPali for Late Interaction...")
            model_id = "vidore/colpali-v1.2"

            self._colpali_model = ColPali.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            self._colpali_processor = ColPaliProcessor.from_pretrained(model_id)
            logger.info("✅ ColPali engine loaded.")
        except Exception as e:
            logger.error(f"❌ Failed to load ColPali: {e}")
            raise InferenceError(f"ColPali engine loading failed: {str(e)}")

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Implémentation réelle ColPali late interaction."""
        try:
            from PIL import Image
            from io import BytesIO

            self._load_colpali_engine()
            img = Image.open(BytesIO(image_data)).convert("RGB")

            with torch.no_grad():
                batch = self._colpali_processor.process_images([img]).to(self._colpali_model.device)
                embeddings = self._colpali_model(**batch)

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self._log_usage(engine="transformers:colpali:late_interaction", units=1)

            return embeddings.cpu().tolist()
        except Exception as e:
            logger.error(f"❌ ColPali inference failed: {e}")
            raise InferenceError(f"ColPali inference failed: {str(e)}")
