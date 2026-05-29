from abc import ABC, abstractmethod
from typing import List, Dict, Any

class FeedbackRepositoryPort(ABC):
    @abstractmethod
    def save_feedback(self, input_context: str, output_text: str, is_positive: bool, user_id: Any = None, feedback_type: str = "general") -> None:
        pass

    @abstractmethod
    def get_recent_feedback(self, limit: int = 100, feedback_type: str = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_feedback_stats(self) -> Dict[str, Any]:
        pass
