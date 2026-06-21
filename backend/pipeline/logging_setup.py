"""Configuration de logging centralisée pour les scripts pipeline / MLOps.

Évite de répéter ``logging.basicConfig(...)`` (et des formats divergents) dans
chaque script. ``basicConfig`` est idempotent — no-op si le root logger possède
déjà des handlers — donc appeler ``setup_logging()`` reste sûr même quand l'app
hôte (Django) a déjà configuré le logging.

Idéalement appelé depuis le garde ``if __name__ == "__main__":`` d'un script pour
ne pas reconfigurer le logging global au simple import du module.
"""

import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure le logging root (format + niveau) pour un script standalone."""
    logging.basicConfig(level=level, format=LOG_FORMAT)
