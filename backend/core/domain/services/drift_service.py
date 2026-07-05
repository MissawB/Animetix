import io
import logging
from typing import Any, Dict, Optional

import numpy as np
from core.ports.config_port import ConfigPort
from core.ports.vector_store_port import VectorStorePort
from scipy.stats import ks_2samp

logger = logging.getLogger("animetix.mlops.drift")

# Préfixe des baselines dans le stockage par défaut. En prod c'est GCS
# (persistant et partagé entre instances Cloud Run), en dev le système de
# fichiers local — le backend de stockage gère la persistance.
BASELINE_PREFIX = "drift-baselines"
COLLECTIONS = ("anime", "manga", "character")


class DriftService:
    """
    Détection de dérive des embeddings (Embedding Drift).

    Compare la distribution des vecteurs en production à une baseline figée lors
    d'un cycle d'entraînement validé. La baseline est stockée via le stockage par
    défaut de Django (``storage``), ce qui la rend persistante et partagée en prod
    (GCS) au lieu d'un fichier local éphémère.
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        config_port: Optional[ConfigPort] = None,
        storage: Any = None,
    ):
        self.vector_store = vector_store
        # config_port est conservé pour compatibilité d'injection (le container
        # le fournit) mais n'est plus nécessaire depuis le passage au stockage.
        self._storage = storage

    @property
    def storage(self):
        # Résolution paresseuse du default_storage Django (GCS en prod, FS en
        # dev) — évite de coupler ce service du domaine à Django à l'import.
        if self._storage is None:
            from django.core.files.storage import default_storage

            self._storage = default_storage
        return self._storage

    @staticmethod
    def _baseline_name(collection_name: str) -> str:
        return f"{BASELINE_PREFIX}/{collection_name}_baseline.npy"

    def get_drift_report(self) -> Dict[str, Any]:
        """Génère un rapport de dérive pour toutes les collections actives."""
        return {coll: self.check_collection_drift(coll) for coll in COLLECTIONS}

    def check_collection_drift(
        self, collection_name: str, threshold: float = 0.01
    ) -> Dict[str, Any]:
        """Vérifie la dérive d'une collection (KS-test, seuil calibré à 0.01)."""
        name = self._baseline_name(collection_name)
        if not self.storage.exists(name):
            return {"status": "unknown", "message": "No baseline found for comparison"}

        try:
            # 1. Baseline persistée (lue en bytes pour rester agnostique du backend).
            with self.storage.open(name, "rb") as fh:
                baseline_vectors = np.load(io.BytesIO(fh.read()))

            # 2. Échantillon des vecteurs actuels.
            embeddings = self.vector_store.get_embeddings(collection_name, limit=1000)
            if not embeddings:
                return {"status": "error", "message": "Collection is empty"}
            current_vectors = np.array(embeddings)

            # 3. Test de Kolmogorov-Smirnov sur les normes (Distribution Shift).
            baseline_norms = np.linalg.norm(baseline_vectors, axis=1)
            current_norms = np.linalg.norm(current_vectors, axis=1)
            stat, p_value = ks_2samp(baseline_norms, current_norms)

            is_drifting = bool(p_value < threshold)
            return {
                "status": "alert" if is_drifting else "healthy",
                "p_value": round(float(p_value), 4),
                "ks_statistic": round(float(stat), 4),
                "is_drifting": is_drifting,
                "sample_size": len(current_vectors),
            }
        except Exception as e:
            logger.error(f"Drift check failed for {collection_name}: {e}")
            return {"status": "error", "message": str(e)}

    def generate_new_baseline(self, collection_name: str) -> None:
        """Fige l'état actuel comme nouvelle référence (persistée via le stockage)."""
        try:
            embeddings = self.vector_store.get_embeddings(collection_name, limit=5000)
            if not embeddings:
                logger.warning(
                    "No embeddings for %s; baseline not written.", collection_name
                )
                return

            from django.core.files.base import ContentFile

            buffer = io.BytesIO()
            np.save(buffer, np.array(embeddings))
            name = self._baseline_name(collection_name)
            # Écrasement déterministe : sans suppression préalable, Storage.save
            # renommerait le fichier (suffixe) sur certains backends.
            if self.storage.exists(name):
                self.storage.delete(name)
            self.storage.save(name, ContentFile(buffer.getvalue()))
            logger.info("✅ Generated new baseline for %s", collection_name)
        except Exception as e:
            logger.error(f"Failed to generate baseline: {e}")
