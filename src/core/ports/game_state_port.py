from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class GameStatePort(ABC):
    """
    Interface for persistent state management (sync).
    Decouples domain services from specific infrastructure (Sessions, Cache, DB).
    """
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from the state store."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        """Sets a value in the state store."""
        pass

    @abstractmethod
    def update(self, data: Dict[str, Any]):
        """Updates multiple keys in the state store."""
        pass

    @abstractmethod
    def delete(self, key: str):
        """Deletes a key from the state store."""
        pass
