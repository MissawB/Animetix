from abc import ABC, abstractmethod


class FeatureStorePort(ABC):
    """
    Port defining interface for low-latency Feature Store reads and writes.
    """

    @abstractmethod
    def get_user_preferences(self, user_id: str) -> dict:
        """
        Retrieves user preference feature vector.
        """
        pass

    @abstractmethod
    def save_user_preferences(self, user_id: str, preferences: dict):
        """
        Saves user preference feature vector.
        """
        pass
