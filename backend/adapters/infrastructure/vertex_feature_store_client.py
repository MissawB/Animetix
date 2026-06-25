import json
import logging
import os
import tempfile
from datetime import datetime, timezone

from django.conf import settings

logger = logging.getLogger("animetix.mlops.feature_store")

try:
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import aiplatform

    HAS_PLATFORM = True
except ImportError:
    HAS_PLATFORM = False


class VertexFeatureStoreClient:
    """
    Client wrapper for Vertex AI Feature Store to store/serve user preferences.
    """

    def __init__(self):
        self.project_id = getattr(settings, "GCP_PROJECT_ID", "animetix")
        self.region = getattr(
            settings, "VERTEX_AI_FEATURE_STORE_REGION", "europe-west1"
        )
        self.featurestore_id = getattr(
            settings, "VERTEX_AI_FEATURE_STORE_ID", "animetix_features"
        )

        self.simulation_mode = (
            os.getenv("VERTEX_AI_FEATURE_STORE_SIMULATION", "false").lower() == "true"
        )

        if not HAS_PLATFORM:
            self.simulation_mode = True
            logger.info(
                "Vertex AI Platform SDK not installed. Running Feature Store in simulation mode."
            )
        else:
            try:
                aiplatform.init(project=self.project_id, location=self.region)
                logger.info("Initialized Vertex AI client for Feature Store.")
            except (DefaultCredentialsError, Exception) as e:
                self.simulation_mode = True
                logger.warning(
                    f"Failed to initialize Vertex AI Feature Store client ({e}). Falling back to simulation mode."
                )

        # Local mock features storage path
        self.mock_store_path = os.path.join(
            getattr(settings, "DATA_DIR", tempfile.gettempdir()),
            "vertex_feature_store_mock.json",
        )

    def get_online_features(self, entity_id: str) -> dict:
        """
        Retrieves the online feature values (user preferences vector) for the given user entity_id.
        """
        if self.simulation_mode:
            logger.info(f"[SIMULATION] Reading features for user: {entity_id}")
            store = self._load_mock_store()
            return store.get(str(entity_id), {})

        try:
            # Note: Vertex AI Feature Store serving uses Featurestore or FeatureOnlineStoreServiceClient.
            # In a standard client wrapper:
            fs = aiplatform.Featurestore(self.featurestore_id)
            entity_type = fs.get_entity_type("user")

            # Read feature values
            response = entity_type.read_manual_features(
                entity_ids=[str(entity_id)],
                feature_ids=[
                    "shonen_hero",
                    "seinen_rebel",
                    "ghibli_dreamer",
                    "comedy_relief",
                    "last_calculated",
                ],
            )

            # Parse the response values
            # The returned response has a structure depending on the Vertex SDK.
            # We convert it to a standard dictionary.
            result = {}
            if response and len(response) > 0:
                row = response[0]
                for f_id in [
                    "shonen_hero",
                    "seinen_rebel",
                    "ghibli_dreamer",
                    "comedy_relief",
                    "last_calculated",
                ]:
                    val = getattr(row, f_id, None)
                    if val is not None:
                        result[f_id] = val
            return result
        except Exception as e:
            logger.error(
                f"Failed to retrieve online features for entity {entity_id}: {e}"
            )
            # Return empty dict so service layer can gracefully fallback
            return {}

    def write_online_features(self, entity_id: str, feature_values: dict):
        """
        Writes/updates the online feature values for the given user entity_id.
        """
        # Ensure timestamp is string for serialization
        feature_values = feature_values.copy()
        if "last_calculated" not in feature_values:
            # Use UTC time string format
            feature_values["last_calculated"] = datetime.now(timezone.utc).isoformat()
        else:
            if isinstance(feature_values["last_calculated"], datetime):
                feature_values["last_calculated"] = feature_values[
                    "last_calculated"
                ].isoformat()

        if self.simulation_mode:
            logger.info(
                f"[SIMULATION] Writing features for user {entity_id}: {feature_values}"
            )
            store = self._load_mock_store()

            # Merge if existing, or overwrite
            store[str(entity_id)] = feature_values
            self._save_mock_store(store)
            return

        try:
            # Writing features is typically done by importing feature values into the entity type
            # or streaming them via Featurestore API.
            fs = aiplatform.Featurestore(self.featurestore_id)
            entity_type = fs.get_entity_type("user")

            # In a production streaming system, we use write_feature_values (available in newer SDKs)
            # or ingest them from GCS/BigQuery.
            # For immediate low-latency writing we mimic the stream client:
            entity_type.write_feature_values(
                instances=[
                    {"entity_id": str(entity_id), "feature_values": feature_values}
                ]
            )
            logger.info(
                f"Successfully wrote features for user {entity_id} to Vertex AI Feature Store."
            )
        except Exception as e:
            logger.error(
                f"Failed to write features to Feature Store for entity {entity_id}: {e}"
            )
            raise e

    def _load_mock_store(self) -> dict:
        if not os.path.exists(self.mock_store_path):
            return {}
        try:
            with open(self.mock_store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_mock_store(self, store: dict):
        os.makedirs(os.path.dirname(self.mock_store_path), exist_ok=True)
        try:
            with open(self.mock_store_path, "w", encoding="utf-8") as f:
                json.dump(store, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write mock features store JSON file: {e}")
