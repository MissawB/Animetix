from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class GoldDatasetPort(ABC):
    @abstractmethod
    def get_all_entries(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def sync_positive_feedback(self) -> int:
        """Synchronise les feedbacks positifs non traités vers le dataset gold."""
        pass

    @abstractmethod
    def validate_entry(self, entry_id: int) -> bool:
        pass

    @abstractmethod
    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        pass
