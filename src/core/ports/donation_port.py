from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from core.domain.entities.donation import Donation

class DonationPort(ABC):
    @abstractmethod
    def save(self, donation: Donation) -> Donation:
        """Saves a donation."""
        pass

    @abstractmethod
    def get_user_donations(self, user_id: int) -> List[Donation]:
        """Returns all donations for a specific user."""
        pass

    @abstractmethod
    def get_total_donations(self, since: Optional[datetime] = None) -> float:
        """Returns the total amount of donations received (optionally since a date)."""
        pass

    @abstractmethod
    def get_recent_donations(self, limit: int = 10) -> List[Donation]:
        """Returns the most recent donations."""
        pass
