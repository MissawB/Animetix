# -*- coding: utf-8 -*-
"""
Synaptic Plasticity Simulator for Animetix.
Simulates Spike-Timing-Dependent Plasticity (STDP) and Hebbian learning rules 
to dynamically adjust semantic association weights and attention mechanisms.
"""

import logging
import math
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger("animetix.neuromorphic.plasticity")

class SynapticPlasticitySimulator:
    def __init__(self, num_concepts: int = 10, tau_plus: float = 20.0, tau_minus: float = 20.0):
        """
        Initialise le simulateur de plasticité synaptique.
        :param num_concepts: Nombre de concepts sémantiques ou nœuds d'attention simulés.
        :param tau_plus: Constante de temps pour la potentiation à long terme (LTP).
        :param tau_minus: Constante de temps pour la dépression à long terme (LTD).
        """
        self.num_concepts = num_concepts
        self.tau_plus = tau_plus
        self.tau_minus = tau_minus
        
        # Matrice de poids synaptiques W (symétrique/asymétrique selon la plasticité)
        self.W = np.random.uniform(0.1, 0.5, (num_concepts, num_concepts))
        np.fill_diagonal(self.W, 0.0) # Pas de boucle d'auto-excitation immédiate
        
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
        Met à jour la matrice de poids selon la règle classique de Hebb ("cells that fire together, wire together").
        dW_ij = learning_rate * a_i * a_j
        """
        act_arr = np.array(activations)[:self.num_concepts]
        if len(act_arr) < self.num_concepts:
            act_arr = np.pad(act_arr, (0, self.num_concepts - len(act_arr)))
            
        # Produit extérieur pour la co-activation
        dW = learning_rate * np.outer(act_arr, act_arr)
        
        self.W = np.clip(self.W + dW, 0.0, 1.0)
        np.fill_diagonal(self.W, 0.0)
        
        logger.info(f"🧠 Hebbian update completed. Synaptic weight mean: {np.mean(self.W):.4f}")
        return self.W

    def update_stdp(self, pre_idx: int, post_idx: int, learning_rate: float = 0.05) -> float:
        """
        Met à jour le poids synaptique spécifique entre un neurone pré-synaptique et post-synaptique
        en se basant sur la règle STDP (Spike-Timing-Dependent Plasticity).
        
        Si post_time > pre_time : Potentiation à long terme (LTP).
        Si post_time < pre_time : Dépression à long terme (LTD).
        """
        if not (0 <= pre_idx < self.num_concepts) or not (0 <= post_idx < self.num_concepts):
            return 0.0
            
        if pre_idx == post_idx:
            return 0.0

        t_pre = self.last_spike_times[pre_idx]
        t_post = self.last_spike_times[post_idx]
        
        delta_t = t_post - t_pre
        
        if delta_t > 0:
            # LTP : Potentiation (renforcement du poids)
            dW = learning_rate * math.exp(-delta_t / self.tau_plus)
        elif delta_t < 0:
            # LTD : Dépression (affaiblissement du poids)
            dW = -learning_rate * math.exp(delta_t / self.tau_minus) # delta_t est négatif, donc division cohérente
        else:
            # Coïncidence parfaite ou pas de spikes enregistrés
            dW = 0.0
            
        old_w = self.W[pre_idx, post_idx]
        self.W[pre_idx, post_idx] = np.clip(old_w + dW, 0.0, 1.0)
        
        logger.info(f"⚡ STDP: Connection [{pre_idx} -> {post_idx}] updated by {dW:+.4f} (old: {old_w:.4f}, new: {self.W[pre_idx, post_idx]:.4f})")
        return dW
