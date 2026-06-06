from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class SafetyPort(ABC):
    @abstractmethod
    def log_safety_event(self, 
                        event_type: str,
                        action_taken: str,
                        detected_categories: List[str] = None,
                        input_text: str = "",
                        output_text: str = "",
                        reasoning: str = "",
                        user_id: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def get_safety_stats(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        pass
