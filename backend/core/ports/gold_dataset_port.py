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

    @abstractmethod
    def save_star_trace(self, instruction: str, input_text: str, output_text: str) -> None:
        """Sauvegarde une trace STaR en attente de validation humaine."""
        pass

    @abstractmethod
    def get_unprocessed_validated_entries(self) -> List[Dict[str, Any]]:
        """Récupère les entrées validées qui n'ont pas encore été exportées pour le Fine-Tuning."""
        pass
        
    @abstractmethod
    def mark_entries_as_processed(self, entry_ids: List[int]) -> None:
        """Marque un lot d'entrées comme traitées/exportées."""
        pass
