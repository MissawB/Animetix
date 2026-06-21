import os
from abc import ABC, abstractmethod
from typing import Any


class ConfigPort(ABC):
    """Port d'accès à la configuration applicative.

    Abstrait `django.conf.settings` afin que le `core` reste indépendant du
    framework. Les adapters concrets vivent dans `adapters/infrastructure`.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration, ou `default` si absente."""
        ...


class EnvConfig(ConfigPort):
    """Implémentation de repli lisant les variables d'environnement.

    Utilisée par défaut quand aucun adapter n'est injecté (tests, scripts,
    exécution du `core` hors Django). Aucune dépendance framework.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return os.environ.get(key, default)
