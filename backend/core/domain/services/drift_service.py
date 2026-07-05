import logging
from typing import Any, Dict, Optional

import numpy as np
from core.ports.config_port import ConfigPort
from core.ports.vector_store_port import VectorStorePort
from scipy.stats import ks_2samp

logger = logging.getLogger("animetix.mlops.drift")

COLLECTIONS = ("anime", "manga", "character")


class DriftService:
    """
    Détection de dérive des embeddings (Embedding Drift).

    Compare la distribution des vecteurs en production à une baseline figée lors
    d'un cycle d'entraînement validé. La baseline (les NORMES des vecteurs) est
    persistée en base via ``baseline_store`` : partagée entre toutes les
    instances et durable, là où un fichier local serait éphémère sur Cloud Run.
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        config_port: Optional[ConfigPort] = None,
        baseline_store: Any = None,
    ):
        self.vector_store = vector_store
        # config_port conservé pour compatibilité d'injection (le container le
        # fournit) mais inutilisé depuis le passage au stockage en base.
        self._baseline_store = baseline_store

    @property
    def baseline_store(self):
        # Résolution paresseuse du store DB (garde le service découplé de Django
        # à l'import ; injectable pour les tests).
        if self._baseline_store is None:
            from adapters.persistence.django_drift_baseline_store import (
                DjangoDriftBaselineStore,
            )

            self._baseline_store = DjangoDriftBaselineStore()
        return self._baseline_store

    def get_drift_report(self) -> Dict[str, Any]:
        """Génère un rapport de dérive pour toutes les collections actives."""
        return {coll: self.check_collection_drift(coll) for coll in COLLECTIONS}

    def check_collection_drift(
        self, collection_name: str, threshold: float = 0.01
    ) -> Dict[str, Any]:
        """Vérifie la dérive d'une collection (KS-test, seuil calibré à 0.01)."""
        baseline = self.baseline_store.load(collection_name)
        if not baseline:
            return {"status": "unknown", "message": "No baseline found for comparison"}

        try:
            baseline_norms = np.array(baseline, dtype=float)

            embeddings = self.vector_store.get_embeddings(collection_name, limit=1000)
            if not embeddings:
                return {"status": "error", "message": "Collection is empty"}
            current_norms = np.linalg.norm(np.array(embeddings), axis=1)

            # Test de Kolmogorov-Smirnov sur les normes (Distribution Shift).
            stat, p_value = ks_2samp(baseline_norms, current_norms)

            is_drifting = bool(p_value < threshold)
            return {
                "status": "alert" if is_drifting else "healthy",
                "p_value": round(float(p_value), 4),
                "ks_statistic": round(float(stat), 4),
                "is_drifting": is_drifting,
                "sample_size": len(current_norms),
            }
        except Exception as e:
            logger.error(f"Drift check failed for {collection_name}: {e}")
            return {"status": "error", "message": str(e)}

    def generate_new_baseline(self, collection_name: str) -> None:
        """Fige la distribution actuelle (normes) comme nouvelle référence."""
        try:
            embeddings = self.vector_store.get_embeddings(collection_name, limit=5000)
            if not embeddings:
                logger.warning(
                    "No embeddings for %s; baseline not written.", collection_name
                )
                return

            norms = np.linalg.norm(np.array(embeddings), axis=1)
            self.baseline_store.save(
                collection_name, [float(n) for n in norms], len(embeddings)
            )
            logger.info("✅ Generated new baseline for %s", collection_name)
        except Exception as e:
            logger.error(f"Failed to generate baseline: {e}")
