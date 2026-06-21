import logging
import os
from typing import Any, Dict, Optional

import numpy as np
from core.config import get_config
from core.ports.config_port import ConfigPort
from core.ports.vector_store_port import VectorStorePort
from scipy.stats import ks_2samp

logger = logging.getLogger("animetix.mlops.drift")


class DriftService:
    """
    Service pour détecter la dérive des embeddings (Embedding Drift).
    Vérifie si les vecteurs en production s'éloignent de la baseline d'entraînement.
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        config_port: Optional[ConfigPort] = None,
    ):
        self.vector_store = vector_store
        self.config = config_port or get_config()
        # Chemins des baselines (normalement générées lors du dernier cycle de training)
        project_root = self.config.get("BASE_DIR").parent.parent
        self.baseline_dir = project_root / "data" / "artifacts" / "baselines"
        if not os.path.exists(self.baseline_dir):
            os.makedirs(self.baseline_dir, exist_ok=True)

    def get_drift_report(self) -> Dict[str, Any]:
        """Génère un rapport de dérive pour toutes les collections actives."""
        report = {}
        collections = ["anime", "manga", "character"]

        for coll in collections:
            report[coll] = self.check_collection_drift(coll)

        return report

    def check_collection_drift(
        self, collection_name: str, threshold: float = 0.01
    ) -> Dict[str, Any]:
        """Vérifie la dérive pour une collection spécifique (KS-test threshold calibré à 0.01)."""
        baseline_path = self.baseline_dir / f"{collection_name}_baseline.npy"

        if not os.path.exists(baseline_path):
            return {"status": "unknown", "message": "No baseline found for comparison"}

        try:
            # 1. Chargement de la baseline
            baseline_vectors = np.load(baseline_path)

            # 2. Récupération des vecteurs actuels (échantillon pour performance)
            embeddings = self.vector_store.get_embeddings(collection_name, limit=1000)
            if not embeddings:
                return {"status": "error", "message": "Collection is empty"}

            current_vectors = np.array(embeddings)

            # 3. Test de Kolmogorov-Smirnov sur les normes (Distribution Shift)
            baseline_norms = np.linalg.norm(baseline_vectors, axis=1)
            current_norms = np.linalg.norm(current_vectors, axis=1)

            stat, p_value = ks_2samp(baseline_norms, current_norms)

            is_drifting = p_value < threshold
            status = "alert" if is_drifting else "healthy"

            return {
                "status": status,
                "p_value": round(p_value, 4),
                "ks_statistic": round(stat, 4),
                "is_drifting": is_drifting,
                "sample_size": len(current_vectors),
            }
        except Exception as e:
            logger.error(f"Drift check failed for {collection_name}: {e}")
            return {"status": "error", "message": str(e)}

    def generate_new_baseline(self, collection_name: str):
        """Prend un instantané de l'état actuel pour servir de nouvelle référence."""
        try:
            embeddings = self.vector_store.get_embeddings(collection_name, limit=5000)
            if embeddings:
                path = self.baseline_dir / f"{collection_name}_baseline.npy"
                np.save(path, np.array(embeddings))
                logger.info(f"✅ Generated new baseline for {collection_name}")
        except Exception as e:
            logger.error(f"Failed to generate baseline: {e}")
