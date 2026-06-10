import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("animetix." + __name__)

class ModelIntegrityVerifier:
    """
    Assure que les modèles chargés depuis le Hub Hugging Face sont intègres
    et proviennent de sources de confiance.
    """
    @staticmethod
    def verify(model_id: str, revision: Optional[str] = None) -> str:
        try:
            from huggingface_hub import model_info
            info = model_info(model_id, revision=revision)
            
            # Vérification de l'auteur/organisation
            author = getattr(info, "author", "unknown")
            if author not in ["jinaai", "google", "sentence-transformers", "BAAI", "nomic-ai"]:
                 logger.warning(f"⚠️ Modèle '{model_id}' provient d'un auteur non listé comme 'Premium Trust': {author}")
            
            # Vérification de la présence de fichiers sécurisés (safetensors)
            has_safetensors = any(f.rfilename.endswith(".safetensors") for f in info.siblings)
            if not has_safetensors:
                logger.error(f"❌ Sécurité: Le modèle {model_id} ne contient pas de fichiers .safetensors (Risque RCE via Pickle).")
                if os.getenv("STRICT_MODEL_SECURITY", "true") == "true":
                    raise ValueError(f"Blocking insecure model: {model_id}")

            logger.info(f"✅ Modèle vérifié: {model_id} (Revision: {info.sha[:8]})")
            return info.sha
        except Exception as e:
            logger.error(f"❌ Échec de la vérification d'intégrité pour {model_id}: {e}")
            if os.getenv("STRICT_MODEL_SECURITY", "true") == "true":
                raise
            return revision or "main"

class ModelsRegistry:
    def __init__(self):
        self._text_model = None
        self._vision_model = None
        self._device = None
        self.manifest = self._load_manifest()
        self.active_text_version = os.getenv("MODEL_VERSION_TEXT", "v3")
        self.verifier = ModelIntegrityVerifier()
    
    def _load_manifest(self):
        manifest_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "models", "manifest.json")
        try:
            with open(manifest_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load models manifest, using fallback: {e}")
            # Fallback avec révisions épinglées (Pinned SHAs for Security)
            return {
                "text": {
                    "v3": {
                        "id": "jinaai/jina-embeddings-v3",
                        "revision": "4955745f4705a61a0b33c7f12e8c257ca46797a7"
                    }
                },
                "vision": {
                    "id": "google/siglip2-so400m-patch14-384",
                    "revision": "e8e4872"
                }
            }

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
            config = self.manifest["text"].get(self.active_text_version)
            if isinstance(config, str): # Legacy support
                model_id = config
                revision = None
            else:
                model_id = config["id"]
                revision = config.get("revision")

            # Vérification avant chargement
            self.verifier.verify(model_id, revision=revision)
            
            logger.info(f"📦 Loading text model: {model_id} (version: {self.active_text_version})...")
            # On n'active trust_remote_code que pour les modèles vérifiés si nécessaire
            self._text_model = SentenceTransformer(
                model_id, 
                device=self.device, 
                revision=revision,
                trust_remote_code=True if "jina" in model_id else False
            )
        return self._text_model

    @property
    def vision_model(self):
        if self._vision_model is None:
            from sentence_transformers import SentenceTransformer
            config = self.manifest.get("vision", {"id": "google/siglip2-so400m-patch14-384"})
            model_id = config["id"]
            revision = config.get("revision", "main")

            # Vérification
            self.verifier.verify(model_id, revision=revision)

            logger.info(f"📦 Loading vision model: {model_id}...")
            self._vision_model = SentenceTransformer(
                model_id, 
                device=self.device,
                revision=revision
            )
        return self._vision_model

# Instance globale
models_registry = ModelsRegistry()
