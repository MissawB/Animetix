import logging
import os
from typing import Optional

from core.utils.model_registry import (
    EMBEDDING_VERSIONS,
    get_verified_revision,
    resolve_trust_remote_code,
)

logger = logging.getLogger("animetix." + __name__)


class ModelIntegrityVerifier:
    """
    Assure que les modèles chargés depuis le Hub Hugging Face sont intègres
    (présence de fichiers safetensors — garde-fou anti-pickle/RCE).
    """

    @staticmethod
    def verify(model_id: str, revision: Optional[str] = None) -> str:
        try:
            from huggingface_hub import model_info  # noqa: E402

            info = model_info(model_id, revision=revision)

            author = getattr(info, "author", "unknown")
            if author not in [
                "jinaai",
                "google",
                "sentence-transformers",
                "BAAI",
                "nomic-ai",
            ]:
                logger.warning(
                    f"⚠️ Modèle '{model_id}' provient d'un auteur non listé comme 'Premium Trust': {author}"
                )

            has_safetensors = any(
                f.rfilename.endswith(".safetensors") for f in info.siblings
            )
            if not has_safetensors:
                logger.error(
                    f"❌ Sécurité: Le modèle {model_id} ne contient pas de fichiers .safetensors (Risque RCE via Pickle)."
                )
                if os.getenv("STRICT_MODEL_SECURITY", "true") == "true":
                    raise ValueError(f"Blocking insecure model: {model_id}")

            logger.info(f"✅ Modèle vérifié: {model_id} (Revision: {info.sha[:8]})")
            return info.sha
        except Exception as e:
            logger.error(
                f"❌ Échec de la vérification d'intégrité pour {model_id}: {e}"
            )
            if os.getenv("STRICT_MODEL_SECURITY", "true") == "true":
                raise
            return revision or "main"


class ModelsRegistry:
    def __init__(self):
        self._text_model = None
        self._vision_model = None
        self._device = None
        self.active_text_version = os.getenv("MODEL_VERSION_TEXT", "v4")
        self.active_vision_version = os.getenv("MODEL_VERSION_VISION", "v3")
        self.verifier = ModelIntegrityVerifier()

    @property
    def device(self):
        if self._device is None:
            import torch  # noqa: E402

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    def _load_embedding(self, kind: str, version: str):
        from sentence_transformers import SentenceTransformer  # noqa: E402

        model_id = EMBEDDING_VERSIONS[kind][version]
        revision = get_verified_revision(model_id)  # single SHA source of truth

        self.verifier.verify(model_id, revision=revision)  # safetensors guard

        logger.info(f"📦 Loading {kind} model: {model_id} (version: {version})...")
        return SentenceTransformer(
            model_id,
            device=self.device,
            revision=revision,
            trust_remote_code=resolve_trust_remote_code(model_id),
        )

    @property
    def text_model(self):
        if self._text_model is None:
            self._text_model = self._load_embedding("text", self.active_text_version)
        return self._text_model

    @property
    def vision_model(self):
        if self._vision_model is None:
            self._vision_model = self._load_embedding(
                "vision", self.active_vision_version
            )
        return self._vision_model


# Instance globale
models_registry = ModelsRegistry()
