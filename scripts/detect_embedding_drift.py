import os
import sys

import numpy as np
from scipy.stats import ks_2samp

# Ajout du dossier root au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.vector_client import vector_manager  # noqa: E402


class DriftDetector:
    def __init__(self, baseline_path):
        self.baseline_vectors = np.load(baseline_path)

    def check_drift(self, collection_name, threshold=0.05):
        collection = vector_manager.get_collection(collection_name)
        data = collection.get(include=["embeddings"])
        current_vectors = np.array(data["embeddings"])

        # Simple KS test sur la norme des vecteurs pour détecter une dérive de distribution
        baseline_norms = np.linalg.norm(self.baseline_vectors, axis=1)
        current_norms = np.linalg.norm(current_vectors, axis=1)

        stat, p_value = ks_2samp(baseline_norms, current_norms)

        print(f"📊 Drift Check for {collection_name}: p-value={p_value:.4f}")
        return p_value < threshold


if __name__ == "__main__":
    # À exécuter dans le pipeline
    pass
