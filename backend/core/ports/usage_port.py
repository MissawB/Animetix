from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

class UsagePort(ABC):
    @abstractmethod
    def log_usage(
        self, 
        engine: str, 
        input_tokens: int = 0, 
        output_tokens: int = 0, 
        units: int = 0,
        user_id: Optional[int] = None
    ):
        """Logs AI usage (tokens or units)."""
        pass

    @abstractmethod
    def get_total_cost(self, since: Optional[datetime] = None) -> float:
        """Returns the total estimated cost of LLM usage."""
        pass

    @abstractmethod
    def check_quota(self, user_id: int, tier: str) -> bool:
        """Returns True if user is within their quota."""
        pass
