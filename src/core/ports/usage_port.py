from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class UsagePort(ABC):
    @abstractmethod
    def log_usage(
        self, 
        engine: str, 
        input_tokens: int, 
        output_tokens: int, 
        user_id: Optional[int] = None
    ):
        """Logs LLM token usage."""
        pass

    @abstractmethod
    def get_total_cost(self, since: Optional[datetime] = None) -> float:
        """Returns the total estimated cost of LLM usage."""
        pass
