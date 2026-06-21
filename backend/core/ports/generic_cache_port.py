from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CachePort(ABC):
    """Port générique de cache clé/valeur.

    Abstrait le cache du framework (Django/Redis) afin que le `core` reste
    indépendant de l'infrastructure. Les adapters concrets vivent dans
    `adapters/infrastructure`.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur, ou `default` si absente."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Stocke une valeur avec un TTL optionnel (en secondes)."""
        ...

    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Récupère plusieurs clés d'un coup (seules les clés présentes sont retournées)."""
        ...

    @abstractmethod
    def set_many(self, mapping: Dict[str, Any], timeout: Optional[int] = None) -> None:
        """Stocke plusieurs paires clé/valeur d'un coup."""
        ...


class InMemoryCache(CachePort):
    """Implémentation de repli en mémoire (pur Python, sans dépendance framework).

    Utilisée par défaut quand aucun adapter n'est injecté : tests, scripts ou
    exécution du `core` hors du contexte Django. N'applique pas l'expiration
    (`timeout` est accepté mais ignoré) — usage best-effort.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        self._store[key] = value

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        return {k: self._store[k] for k in keys if k in self._store}

    def set_many(self, mapping: Dict[str, Any], timeout: Optional[int] = None) -> None:
        self._store.update(mapping)
