from abc import ABC, abstractmethod
from typing import Dict, Any

class EvalResultPort(ABC):
    @abstractmethod
    def save_result(self, query: str, context: str, answer: str, metrics: Dict[str, float]) -> None:
        pass

    @abstractmethod
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'évaluation globale."""
        pass
