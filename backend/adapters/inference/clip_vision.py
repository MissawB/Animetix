"""CLIP and ColPali vision mixin for VisionTransformersAdapter."""

import asyncio  # noqa: E402
import logging  # noqa: E402
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union  # noqa: E402

import httpx  # noqa: E402
from core.config import get_config  # noqa: E402
from core.domain.exceptions import InferenceError  # noqa: E402
from core.utils.lazy_import import lazy_import  # noqa: E402
from core.utils.model_registry import OPEN_CLIP_MODELS  # noqa: E402
from core.utils.security import (
    safe_http_request,  # noqa: E402
    safe_http_request_async,
)

torch = lazy_import("torch")

logger = logging.getLogger("animetix.inference.clip_vision")

_MODEL_CACHE: dict = {}


def _load_open_clip(model_id: str):
    """Charge un modèle CLIP par son id. Deux familles, un seul point d'entrée.

    Le routage se fait sur la table `OPEN_CLIP_MODELS` du registre, PAS sur la
    forme de l'id. La version précédente envoyait chez `hf-hub:` tout id
    contenant un `/` : or le dépôt d'`anime-style-tag-clip` ne publie que des
    poids (ni `open_clip_config.json`, ni tokenizer), donc `hf-hub:` n'avait
    aucune architecture à construire et le SEUL modèle OpenCLIP de la branche
    ne se chargeait pas. L'architecture et le fichier de poids sont des
    propriétés DU modèle : ils vivent avec son nom, dans le registre.

    Les modèles historiques (`clip-ViT-B-32`) restent servis par
    sentence-transformers, inchangés.
    """
    if model_id in _MODEL_CACHE:
        return _MODEL_CACHE[model_id]

    # Les deux familles servent la même interface (encode_image / encode_text) :
    # les appelants ne branchent jamais dessus, et l'annotation le dit.
    wrapped: Union["_OpenClipModel", "_SentenceTransformerModel"]

    recipe = OPEN_CLIP_MODELS.get(model_id)
    if recipe is not None:  # un modèle OpenCLIP déclaré -> poids + architecture
        import open_clip  # noqa: E402
        from huggingface_hub import hf_hub_download  # noqa: E402

        weights = hf_hub_download(model_id, recipe["weights_file"])
        architecture = recipe["architecture"]
        # `preprocess` est la transformation d'image d'open_clip POUR CETTE
        # architecture. On la garde telle quelle : un prétraitement fait main
        # produit des vecteurs qui ont l'air bons et classent mal.
        model, _, preprocess = open_clip.create_model_and_transforms(
            architecture, pretrained=weights
        )
        tokenizer = open_clip.get_tokenizer(architecture)
        model.eval()
        wrapped = _OpenClipModel(
            model=model, preprocess=preprocess, tokenizer=tokenizer
        )
    else:
        from sentence_transformers import SentenceTransformer  # noqa: E402

        wrapped = _SentenceTransformerModel(SentenceTransformer(model_id))

    _MODEL_CACHE[model_id] = wrapped
    return wrapped


class _OpenClipModel:
    def __init__(self, model, preprocess, tokenizer):
        self._model, self._preprocess, self._tokenizer = model, preprocess, tokenizer

    def encode_image(self, img) -> List[float]:
        import torch  # noqa: E402

        with torch.no_grad():
            vec = self._model.encode_image(self._preprocess(img).unsqueeze(0))
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec[0].tolist()

    def encode_text(self, text: str) -> List[float]:
        import torch  # noqa: E402

        with torch.no_grad():
            vec = self._model.encode_text(self._tokenizer([text]))
            vec = vec / vec.norm(dim=-1, keepdim=True)
        return vec[0].tolist()


class _SentenceTransformerModel:
    def __init__(self, model):
        self._model = model

    def encode_image(self, img) -> List[float]:
        return self._model.encode(img).tolist()

    def encode_text(self, text: str) -> List[float]:
        return self._model.encode(text).tolist()


class ClipVisionMixin:
    """Provides CLIP-based similarity, classification, reranking, and ColPali late interaction."""

    if TYPE_CHECKING:

        def _log_usage(
            self,
            engine: str,
            input_tokens: int = 0,
            output_tokens: int = 0,
            units: int = 0,
            allocated_budget: int = 0,
        ) -> None: ...

    def get_image_embedding(
        self, image_data: bytes, model_id: Optional[str] = None
    ) -> List[float]:
        """Encode une image avec le modèle DEMANDÉ.

        L'ancienne version ignorait `model_id` et chargeait toujours
        `clip-ViT-B-32` : un index construit avec un autre modèle aurait été
        interrogé avec celui-ci, et la distance n'aurait rien voulu dire.
        """
        from io import BytesIO  # noqa: E402

        from PIL import Image  # noqa: E402

        name = model_id or get_config().get("CLIP_MODEL_NAME", "clip-ViT-B-32")
        try:
            img = Image.open(BytesIO(image_data)).convert("RGB")
            model = _load_open_clip(name)
            vector = model.encode_image(img)
        except Exception as e:
            # Pas de `return []` : un vecteur vide part ensuite dans la recherche
            # et devient un résultat qui a l'air d'en être un.
            raise InferenceError(f"Image embedding failed ({name}): {e}") from e

        self._log_usage(engine=f"clip:{name}:embedding", units=1)
        return vector

    def get_text_embedding_clip(self, text: str, model_id: str) -> List[float]:
        """La tour TEXTE du même modèle — jamais un encodeur de phrases générique.

        Toute fusion d'un vecteur texte et d'un vecteur image (moyenne, produit)
        n'a de sens que dans un espace joint. Mélanger deux modèles donne soit une
        erreur de dimensions, soit un nombre qui a l'air juste et ne l'est pas.
        """
        try:
            model = _load_open_clip(model_id)
            vector = model.encode_text(text)
        except Exception as e:
            raise InferenceError(f"Text embedding failed ({model_id}): {e}") from e

        self._log_usage(engine=f"clip:{model_id}:text", units=1)
        return vector

    def classify_image(
        self,
        image_data: bytes,
        candidate_labels: List[str],
        model_id: Optional[str] = None,
    ) -> Dict[str, float]:
        try:
            from sentence_transformers import util  # noqa: E402

            img_emb = torch.tensor(self.get_image_embedding(image_data, model_id))
            model_name = model_id or get_config().get(
                "CLIP_MODEL_NAME", "clip-ViT-B-32"
            )
            model = _load_open_clip(model_name)
            text_embs = torch.tensor(
                [model.encode_text(label) for label in candidate_labels]
            )
            scores = util.cos_sim(img_emb, text_embs)[0]
            probs = torch.nn.functional.softmax(scores, dim=0).tolist()

            self._log_usage(engine=f"clip:{model_name}:classify", units=1)

            return {label: p for label, p in zip(candidate_labels, probs)}
        except Exception as e:
            logger.error(f"❌ Image Classification failed: {e}")
            return {}

    def calculate_visual_similarity(
        self, query: str, item_id: str, media_type: str
    ) -> float:
        try:
            from sentence_transformers import util  # noqa: E402

            model_name = get_config().get("CLIP_MODEL_NAME", "clip-ViT-B-32")
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
            self._clip_model = SentenceTransformer(
                get_config().get("CLIP_MODEL_NAME", "clip-ViT-B-32")
            )
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
            from io import BytesIO  # noqa: E402

            from PIL import Image  # noqa: E402

            # Utilisation de safe_http_request_async pour validation SSRF des redirections
            response = await safe_http_request_async("GET", url, timeout=10)
            if response.status_code == 200:
                content = response.content
                return Image.open(BytesIO(content)).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to fetch image {url}: {e}")
        return None

    def _fetch_images_sync(self, urls: List[str]) -> List[Any]:
        from io import BytesIO  # noqa: E402

        from PIL import Image  # noqa: E402

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
            from colpali_engine.models import (
                ColPali,  # noqa: E402
                ColPaliProcessor,
            )

            logger.info("🏗️ Loading ColPali for Late Interaction...")
            model_id = "vidore/colpali-v1.2"

            self._colpali_model = ColPali.from_pretrained(
                model_id,
                torch_dtype=(
                    torch.float16 if torch.cuda.is_available() else torch.float32
                ),
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
            from io import BytesIO  # noqa: E402

            from PIL import Image  # noqa: E402

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
