# -*- coding: utf-8 -*-
"""
Neuromorphic Synaptic Plasticity Service for Animetix.
Implements dynamic weight adjustment via STDP and Hebbian learning rules.
"""

import logging  # noqa: E402
import math  # noqa: E402
import os
from typing import Any, Dict, List, Optional  # noqa: E402

import numpy as np  # noqa: E402

logger = logging.getLogger("animetix.neuromorphic.plasticity")


class SynapticPlasticityService:
    def __init__(
        self,
        num_concepts: int = 10,
        tau_plus: float = 20.0,
        tau_minus: float = 20.0,
        inference_engine: Optional[Any] = None,
        checkpoint_path: Optional[str] = None,
    ):
        """
        Initialise le service de plasticité synaptique.
        :param num_concepts: Nombre de concepts sémantiques ou nœuds d'attention simulés.
        :param tau_plus: Constante de temps pour la potentiation à long terme (LTP).
        :param tau_minus: Constante de temps pour la dépression à long terme (LTD).
        :param inference_engine: Optional inference engine for plasticity interactions.
        :param checkpoint_path: Path to save/load synaptic state.
        """
        self.num_concepts = num_concepts
        self.tau_plus = tau_plus
        self.tau_minus = tau_minus
        self.inference_engine = inference_engine
        self.checkpoint_path = checkpoint_path

        # Matrice de poids synaptiques W
        self.W = np.random.uniform(0.1, 0.5, (num_concepts, num_concepts))
        np.fill_diagonal(self.W, 0.0)

        # Horodatage du dernier spike/activation pour chaque concept
        self.last_spike_times = np.zeros(num_concepts)

        # Tentative de chargement du checkpoint si disponible
        if checkpoint_path:
            self.load_checkpoint()

    def reset_matrix(self):
        """Réinitialise la matrice de poids synaptiques."""
        self.W = np.random.uniform(0.1, 0.5, (self.num_concepts, self.num_concepts))
        np.fill_diagonal(self.W, 0.0)
        self.last_spike_times = np.zeros(self.num_concepts)
        logger.info("🧠 Synaptic weights reset to initial state.")
        if self.checkpoint_path:
            self.save_checkpoint()

    def save_checkpoint(self):
        """Sauvegarde l'état actuel des synapses sur disque."""
        if not self.checkpoint_path:
            return
        try:
            import json  # noqa: E402

            data = self.to_dict()
            with open(self.checkpoint_path, "w") as f:
                json.dump(data, f)
            logger.info(f"💾 Synaptic checkpoint saved to {self.checkpoint_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save synaptic checkpoint: {e}")

    def load_checkpoint(self):
        """Charge l'état des synapses depuis le disque."""
        if not self.checkpoint_path or not os.path.exists(self.checkpoint_path):
            return
        try:
            import json  # noqa: E402

            with open(self.checkpoint_path, "r") as f:
                data = json.load(f)
            self.W = np.array(data["W"])
            self.last_spike_times = np.array(data["last_spike_times"])
            if "tau_plus" in data:
                self.tau_plus = float(data["tau_plus"])
            if "tau_minus" in data:
                self.tau_minus = float(data["tau_minus"])
            logger.info(f"📂 Synaptic checkpoint loaded from {self.checkpoint_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load synaptic checkpoint: {e}")

    def apply_plasticity(self, data: Dict[str, Any]):
        """
        Applies plasticity updates and triggers inference if engine is available.
        """
        if self.inference_engine:
            self.inference_engine.run(data)

    def trigger_spikes(self, active_indices: List[int], current_time: float):
        """
        Enregistre l'activation (spike) de certains concepts à un instant donné.
        """
        for idx in active_indices:
            if 0 <= idx < self.num_concepts:
                self.last_spike_times[idx] = current_time

    def update_hebbian(
        self, activations: List[float], learning_rate: float = 0.01
    ) -> np.ndarray:
        """
        Met à jour la matrice de poids selon la règle classique de Hebb.
        """
        act_arr = np.array(activations)[: self.num_concepts]
        if len(act_arr) < self.num_concepts:
            act_arr = np.pad(act_arr, (0, self.num_concepts - len(act_arr)))

        dW = learning_rate * np.outer(act_arr, act_arr)

        self.W = np.clip(self.W + dW, 0.0, 1.0)
        np.fill_diagonal(self.W, 0.0)

        logger.info(
            f"🧠 Hebbian update completed. Synaptic weight mean: {np.mean(self.W):.4f}"
        )
        return self.W

    def update_stdp(
        self, pre_idx: int, post_idx: int, learning_rate: float = 0.05
    ) -> float:
        """
        Met à jour le poids synaptique spécifique entre un neurone pré-synaptique et post-synaptique
        en se basant sur la règle STDP.
        """
        if not (0 <= pre_idx < self.num_concepts) or not (
            0 <= post_idx < self.num_concepts
        ):
            return 0.0

        if pre_idx == post_idx:
            return 0.0

        t_pre = self.last_spike_times[pre_idx]
        t_post = self.last_spike_times[post_idx]

        delta_t = t_post - t_pre

        if delta_t > 0:
            dW = learning_rate * math.exp(-delta_t / self.tau_plus)
        elif delta_t < 0:
            dW = -learning_rate * math.exp(delta_t / self.tau_minus)
        else:
            dW = 0.0

        old_w = self.W[pre_idx, post_idx]
        self.W[pre_idx, post_idx] = np.clip(old_w + dW, 0.0, 1.0)

        logger.info(
            f"⚡ STDP: Connection [{pre_idx} -> {post_idx}] updated by {dW:+.4f} (old: {old_w:.4f}, new: {self.W[pre_idx, post_idx]:.4f})"
        )
        return dW

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'état pour persistance."""
        return {
            "W": self.W.tolist(),
            "last_spike_times": self.last_spike_times.tolist(),
            "num_concepts": self.num_concepts,
            "tau_plus": self.tau_plus,
            "tau_minus": self.tau_minus,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SynapticPlasticityService":
        """Restaure un service à partir de données sérialisées."""
        instance = cls(
            num_concepts=data["num_concepts"],
            tau_plus=data["tau_plus"],
            tau_minus=data["tau_minus"],
        )
        instance.W = np.array(data["W"])
        instance.last_spike_times = np.array(data["last_spike_times"])
        return instance
