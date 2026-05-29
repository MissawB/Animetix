import os
import json
import logging

logger = logging.getLogger("animetix." + __name__)

class ModelsRegistry:
    def __init__(self):
        self._text_model = None
        self._vision_model = None
        self._device = None
        self.manifest = self._load_manifest()
        self.active_text_version = os.getenv("MODEL_VERSION_TEXT", "v3")
    
    def _load_manifest(self):
        manifest_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "models", "manifest.json")
        try:
            with open(manifest_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load models manifest, using fallback: {e}")
            return {"text": {"v3": "jinaai/jina-embeddings-v3"}}

    @property
    def device(self):
        if self._device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    @property
    def text_model(self):
        if self._text_model is None:
            from sentence_transformers import SentenceTransformer
            model_name = self.manifest["text"].get(self.active_text_version, "jinaai/jina-embeddings-v3")
            logger.info(f"📦 Loading text model: {model_name} (version: {self.active_text_version})...")
            self._text_model = SentenceTransformer(model_name, device=self.device, trust_remote_code=True)
        return self._text_model

    @property
    def vision_model(self):
        if self._vision_model is None:
            from sentence_transformers import SentenceTransformer
            # Mise à jour vers SigLIP-2 pour une meilleure compréhension visuelle SOTA
            self._vision_model = SentenceTransformer('google/siglip2-so400m-patch14-384', device=self.device)
        return self._vision_model

# Instance globale
models_registry = ModelsRegistry()
