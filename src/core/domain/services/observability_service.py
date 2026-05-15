import os
import logging
from typing import Dict, Any, Optional
import wandb
import time

logger = logging.getLogger('animetix.observability')

class ObservabilityService:
    """
    Gère le monitoring des performances et de la qualité IA via Weights & Biases.
    Suit la latence, la dérive sémantique et l'utilisation des modèles.
    """
    def __init__(self, project_name: str = "animetix-prod"):
        self.project_name = project_name
        self.api_key = os.getenv("WANDB_API_KEY")
        self.enabled = bool(self.api_key)
        self._run = None

        if self.enabled:
            try:
                wandb.login(key=self.api_key)
                self._run = wandb.init(
                    project=self.project_name,
                    job_type="production-monitoring",
                    resume="allow"
                )
                logger.info(f"🚀 W&B Monitoring initialized for project {self.project_name}")
            except Exception as e:
                logger.error(f"Failed to initialize W&B: {e}")
                self.enabled = False

    def log_inference(self, model_id: str, latency: float, tokens: int, metadata: Optional[Dict] = None):
        """Logue les métriques d'une inférence LLM."""
        if not self.enabled: return
        
        data = {
            "inference/latency": latency,
            "inference/tokens": tokens,
            "inference/tokens_per_sec": tokens / latency if latency > 0 else 0,
            "model_id": model_id
        }
        if metadata:
            data.update(metadata)
            
        wandb.log(data)

    def log_rag_quality(self, query: str, similarity_score: float, faithfulness: float = 0.0):
        """Logue la qualité des résultats du RAG."""
        if not self.enabled: return
        
        wandb.log({
            "rag/similarity_score": similarity_score,
            "rag/faithfulness": faithfulness,
            "rag/query_length": len(query)
        })

    def log_error(self, error_type: str, message: str):
        """Logue une erreur critique de l'infrastructure IA."""
        if not self.enabled: return
        wandb.log({
            "errors/count": 1,
            "errors/type": error_type,
            "errors/message": message
        })

    def finish(self):
        if self._run:
            self._run.finish()
