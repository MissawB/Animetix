# -*- coding: utf-8 -*-
"""
Quantum-Cognitive Preference Model for Animetix.
Models user decisions and context shifts using non-commutative Quantum Probability Theory.
"""

import logging
import numpy as np
from typing import Dict, Any, Tuple

logger = logging.getLogger("animetix.quantum.cognition")

class QuantumCognitivePreferenceModel:
    def __init__(self, dimension: int = 4):
        self.dimension = dimension
        # Initialisation de l'état d'esprit de l'utilisateur comme un vecteur d'état complexe normalisé |psi>
        # Dans un espace de Hilbert de dimension 4
        self.state = np.zeros(dimension, dtype=complex)
        self.state[0] = 1.0 / np.sqrt(2)
        self.state[1] = 1.0j / np.sqrt(2)
        
        # Projecteurs orthogonaux correspondant à des thèmes (Shonen, Seinen, Ghibli, Comedy)
        self.projectors = self._generate_thematic_projectors()

    def _generate_thematic_projectors(self) -> Dict[str, np.ndarray]:
        """
        Génère des matrices de projection orthogonale complexes.
        """
        projectors = {}
        
        # 1. Projecteur Shonen
        v_shonen = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        projectors["shonen"] = np.outer(v_shonen, np.conj(v_shonen))
        
        # 2. Projecteur Seinen (un état de superposition complexe)
        v_seinen = np.array([0.0, 1.0, 0.0, 0.0], dtype=complex)
        projectors["seinen"] = np.outer(v_seinen, np.conj(v_seinen))
        
        # 3. Projecteur Ghibli
        v_ghibli = np.array([1.0/np.sqrt(2), 0.0, 1.0/np.sqrt(2), 0.0], dtype=complex)
        projectors["ghibli"] = np.outer(v_ghibli, np.conj(v_ghibli))
        
        # 4. Projecteur Comedy
        v_comedy = np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
        projectors["comedy"] = np.outer(v_comedy, np.conj(v_comedy))
        
        return projectors

    def measure_preference(self, theme: str) -> Tuple[float, bool]:
        """
        Calcule la probabilité de réponse "Oui" à un thème en appliquant la règle de Born.
        Effondre ensuite l'état cognitif |psi> en fonction du résultat de la mesure.
        """
        self.state /= np.linalg.norm(self.state) # Rigueur: normalisation continuelle
        P = self.projectors.get(theme.lower())
        
        if P is None:
            # Fallback en cas de thème inconnu
            return 0.5, False

        # Règle de Born : p = <psi| P |psi>
        prob = float(np.real(np.dot(np.conj(self.state), np.dot(P, self.state))))
        
        # Simulation de la mesure projective
        outcome = np.random.rand() < prob
        
        # Effondrement de l'état (Projection et Renormalisation)
        if outcome:
            collapsed = np.dot(P, self.state)
        else:
            # Projection sur le complément orthogonal (I - P)
            I = np.eye(self.dimension, dtype=complex)
            collapsed = np.dot(I - P, self.state)
            
        norm = np.linalg.norm(collapsed)
        if norm > 0.0:
            self.state = collapsed / norm
        else:
            # Si effondrement complet (impossible mathématiquement sauf prob=0), réinitialiser
            self.state[0] = 1.0
            
        logger.info(f"🌌 Quantum Born's Rule: Measured '{theme}' -> Prob: {prob:.2f} -> Outcome: {outcome}")
        return prob, outcome

    def order_effects_demonstration(self, theme_a: str, theme_b: str) -> Tuple[float, float]:
        """
        Démontre le caractère non-commutatif de la cognition humaine (Effets d'ordre) :
        Mesurer A puis B donne un état différent de mesurer B puis A.
        """
        # Sauvegarde de l'état d'origine
        saved_state = np.copy(self.state)
        
        # Trajet 1 : A puis B
        p_a1, _ = self.measure_preference(theme_a)
        p_b1, _ = self.measure_preference(theme_b)
        
        # Restauration
        self.state = np.copy(saved_state)
        
        # Trajet 2 : B puis A
        p_b2, _ = self.measure_preference(theme_b)
        p_a2, _ = self.measure_preference(theme_a)
        
        logger.info(f"🌌 Non-Commutativity Order Effect: P({theme_a} then {theme_b})={p_b1:.3f} | P({theme_b} then {theme_a})={p_a2:.3f}")
        return p_b1, p_a2
