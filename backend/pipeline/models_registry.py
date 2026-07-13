import logging
import os

from core.utils.model_registry import (
    EMBEDDING_VERSIONS,
    ModelIntegrityVerifier,
    get_verified_revision,
    resolve_text_embedding_version,
    resolve_trust_remote_code,
)

logger = logging.getLogger("animetix." + __name__)


class ModelsRegistry:
    def __init__(self):
        self._text_model = None
        self._vision_model = None
        self._device = None
        self.active_text_version = resolve_text_embedding_version()
        # v2 (siglip2) par défaut, pas v3 : le code distant de Qwen3-VL-Embedding-8B
        # importe `sentence_transformers.base`, un module qui n'existe plus dans la
        # version installée (3.3.1) -- le vectoriseur mourait dessus avant d'écrire
        # une seule ligne. v3 reste accessible par MODEL_VERSION_VISION pour qui a
        # le GPU et la bonne pile.
        self.active_vision_version = os.getenv("MODEL_VERSION_VISION", "v2")
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
