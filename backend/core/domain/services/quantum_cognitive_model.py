# -*- coding: utf-8 -*-
"""Stable public import path for the quantum-cognitive preference model.

The implementation lives in :mod:`core.domain.services.quantum_cognitive_service`
as :class:`QuantumCognitiveService`. This module exposes it under the historical
``QuantumCognitivePreferenceModel`` name for backward compatibility.
"""

from .quantum_cognitive_service import QuantumCognitiveService

QuantumCognitivePreferenceModel = QuantumCognitiveService

__all__ = ["QuantumCognitivePreferenceModel", "QuantumCognitiveService"]
