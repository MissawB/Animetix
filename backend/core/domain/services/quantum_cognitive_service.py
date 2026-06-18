# -*- coding: utf-8 -*-
"""
Quantum-Cognitive Preference Service for Animetix.
Models user decisions using non-commutative Quantum Probability Theory and Born's rule.
"""

import logging  # noqa: E402
import numpy as np  # noqa: E402
from typing import Dict, Any, Tuple  # noqa: E402

logger = logging.getLogger("animetix.quantum.cognition")


class QuantumCognitiveService:
    def __init__(self, dimension: int = 4):
        self.dimension = dimension
        # Initialisation de l'état d'esprit de l'utilisateur comme un vecteur d'état complexe normalisé |psi>
        self.state = np.zeros(dimension, dtype=complex)
        self.state[0] = 1.0 / np.sqrt(2)
        self.state[1] = 1.0j / np.sqrt(2)

        # Projecteurs orthogonaux correspondant à des thèmes
        self.projectors = self._generate_thematic_projectors()

    def _generate_thematic_projectors(self) -> Dict[str, np.ndarray]:
        """
        Génère des matrices de projection orthogonale complexes.
        """
        projectors = {}

        # 1. Projecteur Shonen
        v_shonen = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        projectors["shonen"] = np.outer(v_shonen, np.conj(v_shonen))

        # 2. Projecteur Seinen
        v_seinen = np.array([0.0, 1.0, 0.0, 0.0], dtype=complex)
        projectors["seinen"] = np.outer(v_seinen, np.conj(v_seinen))

        # 3. Projecteur Ghibli
        v_ghibli = np.array(
            [1.0 / np.sqrt(2), 0.0, 1.0 / np.sqrt(2), 0.0], dtype=complex
        )
        projectors["ghibli"] = np.outer(v_ghibli, np.conj(v_ghibli))

        # 4. Projecteur Comedy
        v_comedy = np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
        projectors["comedy"] = np.outer(v_comedy, np.conj(v_comedy))

        return projectors

    def measure_preference(self, theme: str) -> Tuple[float, bool]:
        """
        Calcule la probabilité de réponse "Oui" à un thème et effondre l'état |psi>.
        """
        self.state /= np.linalg.norm(self.state)
        P = self.projectors.get(theme.lower())

        if P is None:
            return 0.5, False

        prob = float(np.real(np.dot(np.conj(self.state), np.dot(P, self.state))))
        outcome = np.random.rand() < prob

        if outcome:
            collapsed = np.dot(P, self.state)
        else:
            identity_matrix = np.eye(self.dimension, dtype=complex)
            collapsed = np.dot(identity_matrix - P, self.state)

        norm = np.linalg.norm(collapsed)
        if norm > 0.0:
            self.state = collapsed / norm
        else:
            self.state[0] = 1.0

        logger.info(
            f"🌌 Quantum Born's Rule: Measured '{theme}' -> Prob: {prob:.2f} -> Outcome: {outcome}"
        )
        return prob, outcome

    def order_effects_demonstration(
        self, theme_a: str, theme_b: str
    ) -> Tuple[float, float]:
        """
        Démontre le caractère non-commutatif de la cognition humaine.
        """
        saved_state = np.copy(self.state)
        p_a1, _ = self.measure_preference(theme_a)
        p_b1, _ = self.measure_preference(theme_b)
        self.state = np.copy(saved_state)
        p_b2, _ = self.measure_preference(theme_b)
        p_a2, _ = self.measure_preference(theme_a)

        logger.info(
            f"🌌 Non-Commutativity Order Effect: P({theme_a} then {theme_b})={p_b1:.3f} | P({theme_b} then {theme_a})={p_a2:.3f}"
        )
        return p_b1, p_a2

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'état complexe pour persistance JSON."""
        return {
            "state_real": self.state.real.tolist(),
            "state_imag": self.state.imag.tolist(),
            "dimension": self.dimension,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuantumCognitiveService":
        """Restaure un service à partir de données sérialisées."""
        instance = cls(dimension=data["dimension"])
        real = np.array(data["state_real"])
        imag = np.array(data["state_imag"])
        instance.state = real + 1j * imag
        return instance
