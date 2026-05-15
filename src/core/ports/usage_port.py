from abc import ABC, abstractmethod
from typing import Optional

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
