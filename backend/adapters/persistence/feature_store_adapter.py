from adapters.infrastructure.vertex_feature_store_client import VertexFeatureStoreClient
from core.ports.feature_store_port import FeatureStorePort
from django.core.cache import cache


class FeatureStoreAdapter(FeatureStorePort):
    """
    Adapter implementing FeatureStorePort using VertexFeatureStoreClient
    and Django cache for L1/L2 latency optimization.
    """

    def __init__(self):
        self.client = VertexFeatureStoreClient()

    def get_user_preferences(self, user_id: str) -> dict:
        """
        Retrieves user preference feature vector using L1 Cache and L2 Feature Store.
        """
        cache_key = f"user_features_{user_id}"
        cached_features = cache.get(cache_key)

        if cached_features is not None:
            return cached_features

        # L2: Read from Feature Store Client
        features = self.client.get_online_features(user_id)

        # Cache for 15 minutes
        if features:
            cache.set(cache_key, features, 900)

        return features

    def save_user_preferences(self, user_id: str, preferences: dict):
        """
        Saves updated user preference feature vector to Feature Store and updates L1 cache.
        """
        # Save to Feature Store (L2)
        self.client.write_online_features(user_id, preferences)

        # Update L1 Cache
        cache_key = f"user_features_{user_id}"
        cache.set(cache_key, preferences, 900)
