import os

class ModelsRegistry:
    def __init__(self):
        self._text_model = None
        self._vision_model = None
        self._device = None
        # On ne fait rien de lourd ici au démarrage
    
    @property
    def device(self):
        if self._device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"🧠 ModelsRegistry initialized on device: {self._device}")
        return self._device

    @property
    def text_model(self):
        if self._text_model is None:
            from sentence_transformers import SentenceTransformer
            print("📦 Loading text model: paraphrase-multilingual-mpnet-base-v2...")
            self._text_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device=self.device)
        return self._text_model

    @property
    def vision_model(self):
        if self._vision_model is None:
            from sentence_transformers import SentenceTransformer
            print("📦 Loading vision model: clip-ViT-B-32...")
            self._vision_model = SentenceTransformer('clip-ViT-B-32', device=self.device)
        return self._vision_model

# Instance globale (Singleton)
models_registry = ModelsRegistry()
