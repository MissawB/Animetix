# -*- coding: utf-8 -*-
"""
Neuromorphic Synaptic Plasticity Service for Animetix.
Implements dynamic weight adjustment via STDP and Hebbian learning rules.
"""

import logging
import math
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger("animetix.neuromorphic.plasticity")

class SynapticPlasticityService:
    def __init__(self, num_concepts: int = 10, tau_plus: float = 20.0, tau_minus: float = 20.0):
        """
        Initialise le service de plasticité synaptique.
        :param num_concepts: Nombre de concepts sémantiques ou nœuds d'attention simulés.
        :param tau_plus: Constante de temps pour la potentiation à long terme (LTP).
        :param tau_minus: Constante de temps pour la dépression à long terme (LTD).
        """
        self.num_concepts = num_concepts
        self.tau_plus = tau_plus
        self.tau_minus = tau_minus
        
        # Matrice de poids synaptiques W
        self.W = np.random.uniform(0.1, 0.5, (num_concepts, num_concepts))
        np.fill_diagonal(self.W, 0.0)
        
        # Horodatage du dernier spike/activation pour chaque concept
        self.last_spike_times = np.zeros(num_concepts)

    def trigger_spikes(self, active_indices: List[int], current_time: float):
        """
        Enregistre l'activation (spike) de certains concepts à un instant donné.
        """
        for idx in active_indices:
            if 0 <= idx < self.num_concepts:
                self.last_spike_times[idx] = current_time

    def update_hebbian(self, activations: List[float], learning_rate: float = 0.01) -> np.ndarray:
        """
        Met à jour la matrice de poids selon la règle classique de Hebb.
        """
        act_arr = np.array(activations)[:self.num_concepts]
        if len(act_arr) < self.num_concepts:
            act_arr = np.pad(act_arr, (0, self.num_concepts - len(act_arr)))
            
        dW = learning_rate * np.outer(act_arr, act_arr)
        
        self.W = np.clip(self.W + dW, 0.0, 1.0)
        np.fill_diagonal(self.W, 0.0)
        
        logger.info(f"🧠 Hebbian update completed. Synaptic weight mean: {np.mean(self.W):.4f}")
        return self.W

    def update_stdp(self, pre_idx: int, post_idx: int, learning_rate: float = 0.05) -> float:
        """
        Met à jour le poids synaptique spécifique entre un neurone pré-synaptique et post-synaptique
        en se basant sur la règle STDP.
        """
        if not (0 <= pre_idx < self.num_concepts) or not (0 <= post_idx < self.num_concepts):
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
        
        logger.info(f"⚡ STDP: Connection [{pre_idx} -> {post_idx}] updated by {dW:+.4f} (old: {old_w:.4f}, new: {self.W[pre_idx, post_idx]:.4f})")
        return dW

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'état pour persistance."""
        return {
            "W": self.W.tolist(),
            "last_spike_times": self.last_spike_times.tolist(),
            "num_concepts": self.num_concepts,
            "tau_plus": self.tau_plus,
            "tau_minus": self.tau_minus
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SynapticPlasticityService':
        """Restaure un service à partir de données sérialisées."""
        instance = cls(
            num_concepts=data["num_concepts"],
            tau_plus=data["tau_plus"],
            tau_minus=data["tau_minus"]
        )
        instance.W = np.array(data["W"])
        instance.last_spike_times = np.array(data["last_spike_times"])
        return instance
