from abc import ABC, abstractmethod
from typing import Any, Optional

class StatePort(ABC):
    @abstractmethod
    async def get_state(self, key: str) -> Optional[Any]:
        """Récupère l'état à partir d'une clé."""
        pass

    @abstractmethod
    async def set_state(self, key: str, value: Any, timeout: Optional[int] = None):
        """Enregistre l'état pour une clé."""
        pass

    @abstractmethod
    async def delete_state(self, key: str):
        """Supprime l'état pour une clé."""
        pass
