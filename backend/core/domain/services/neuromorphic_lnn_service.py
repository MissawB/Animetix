# -*- coding: utf-8 -*-
"""
Neuromorphic Liquid Neural Network (LNN) Service for Animetix.
Handles continuous time-continuous signals and ODE-based state transitions.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger("animetix.neuromorphic.lnn")

class LiquidNeuralNetworkService:
    def __init__(self, state_dimension: int = 4, input_dimension: int = 2, inference_engine: Optional[Any] = None):
        self.state_dimension = state_dimension
        self.input_dimension = input_dimension
        self.inference_engine = inference_engine
        
        # État courant du système
        self.state = np.zeros(state_dimension)
        
        # Initialisation des poids synaptiques (W) et constantes de temps liquides (tau)
        self.W = np.random.randn(state_dimension, state_dimension) * 0.1
        self.I_W = np.random.randn(state_dimension, input_dimension) * 0.1
        self.tau = np.random.uniform(0.1, 1.0, state_dimension)

    def process(self, input_data: List[float]):
        if self.inference_engine:
            self.inference_engine.run(input_data)
        return self.process_continuous_signal([input_data])

    def ode_system(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """
        Définition du système d'équations différentielles liquides (LNN) :
        dx/dt = -x/tau + f(W*x + I_W*u) * (A - x)
        Où f est une fonction d'activation non-linéaire (tanh).
        """
        synaptic_input = np.dot(self.W, x) + np.dot(self.I_W, u)
        f_activation = np.tanh(synaptic_input)
        
        # A représente la borne supérieure de l'état (saturation)
        A = 1.0
        
        # dx/dt
        dxdt = -x / self.tau + f_activation * (A - x)
        return dxdt

    def integrate_rk4(self, x_init: np.ndarray, u: np.ndarray, dt: float = 0.05) -> np.ndarray:
        """
        Intégration numérique d'un pas temporel dt par la méthode de Runge-Kutta d'ordre 4 (RK4).
        """
        k1 = self.ode_system(x_init, u)
        k2 = self.ode_system(x_init + 0.5 * dt * k1, u)
        k3 = self.ode_system(x_init + 0.5 * dt * k2, u)
        k4 = self.ode_system(x_init + dt * k3, u)
        
        x_next = x_init + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        return x_next

    def process_continuous_signal(self, input_signal: List[List[float]], dt: float = 0.05) -> List[List[float]]:
        """
        Traite un signal d'entrée multimodal continu et met à jour l'état interne.
        """
        # Validation de stabilité : dt trop grand peut faire diverger RK4
        if dt > 0.5:
            logger.warning(f"⚠️ LNN: Time step dt={dt} is too large for stable RK4 integration. Clipping to 0.5.")
            dt = 0.5

        if not input_signal:
            logger.warning("⚠️ LNN: Empty input signal received.")
            return []

        if len(input_signal) > 1000:
            logger.warning(f"⚠️ LNN: Signal length {len(input_signal)} exceeds safety limit (1000). Truncating.")
            input_signal = input_signal[:1000]

        logger.info(f"🧠 LNN: Processing continuous signal of length {len(input_signal)} steps...")
        
        current_state = np.copy(self.state)
        state_history = []
        
        for u_step in input_signal:
            u_arr = np.array(u_step)[:self.input_dimension]
            if len(u_arr) < self.input_dimension:
                u_arr = np.pad(u_arr, (0, self.input_dimension - len(u_arr)))
                
            current_state = self.integrate_rk4(current_state, u_arr, dt)
            
            # Anti-Explosion check : saturation forcée si divergence
            if np.any(np.isnan(current_state)) or np.any(np.isinf(current_state)):
                logger.error("🔥 LNN: State divergence detected! Emergency reset.")
                current_state = np.zeros(self.state_dimension)
                
            state_history.append(current_state.tolist())
            
        self.state = current_state
        logger.info(f"✅ LNN processing completed. Final state variance: {np.var(current_state):.4f}")
        return state_history

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'état pour persistance."""
        return {
            "state": self.state.tolist(),
            "W": self.W.tolist(),
            "I_W": self.I_W.tolist(),
            "tau": self.tau.tolist(),
            "state_dimension": self.state_dimension,
            "input_dimension": self.input_dimension
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiquidNeuralNetworkService':
        """Restaure un service à partir de données sérialisées."""
        instance = cls(
            state_dimension=data["state_dimension"],
            input_dimension=data["input_dimension"]
        )
        instance.state = np.array(data["state"])
        instance.W = np.array(data["W"])
        instance.I_W = np.array(data["I_W"])
        instance.tau = np.array(data["tau"])
        return instance
