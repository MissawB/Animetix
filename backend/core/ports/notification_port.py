from abc import ABC, abstractmethod
from typing import Any, Optional


class NotificationPort(ABC):
    """
    Port for sending user notifications across different channels.
    """

    @abstractmethod
    def send(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        link: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Sends a notification to a specific user."""
        pass
