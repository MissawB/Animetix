import uuid
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger("animetix.telemetry.bigquery")


class BigQueryTelemetryService:
    def __init__(self):
        self.is_prod = getattr(settings, "IS_PRODUCTION", False)
        self.dataset_id = getattr(settings, "GCP_BIGQUERY_DATASET", "telemetry")
        self.client = None

        if self.is_prod:
            try:
                from google.cloud import bigquery  # noqa: E402

                self.client = bigquery.Client()
            except Exception as e:
                logger.error(f"Failed to initialize BigQuery Client: {e}")

    def stream_interaction(
        self, user_id: int, media_item_id: int, interaction_type: str, weight: float
    ):
        """Streams a user-item interaction row to BigQuery telemetry.user_interactions."""
        row = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "media_item_id": media_item_id,
            "interaction_type": interaction_type,
            "weight": float(weight),
            "created_at": datetime.utcnow().isoformat(),
        }

        if self.client:
            try:
                table_id = f"{self.client.project}.{self.dataset_id}.user_interactions"
                errors = self.client.insert_rows_json(table_id, [row])
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                    return False
                return True
            except Exception as e:
                logger.error(f"BigQuery streaming insert failed: {e}")
                return False
        else:
            logger.info(f"Simulating BigQuery Stream [user_interactions]: {row}")
            return True

    def stream_drift(
        self,
        user_id: int,
        archetype_id: str,
        intensity: float,
        shonen: float,
        seinen: float,
        logic: float,
    ):
        """Streams an archetype drift snapshot row to BigQuery telemetry.archetype_drift."""
        row = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "archetype_id": archetype_id,
            "intensity": float(intensity),
            "shonen_affinity": float(shonen),
            "seinen_affinity": float(seinen),
            "logic_consistency": float(logic),
            "created_at": datetime.utcnow().isoformat(),
        }

        if self.client:
            try:
                table_id = f"{self.client.project}.{self.dataset_id}.archetype_drift"
                errors = self.client.insert_rows_json(table_id, [row])
                if errors:
                    logger.error(f"BigQuery insert errors: {errors}")
                    return False
                return True
            except Exception as e:
                logger.error(f"BigQuery streaming insert failed: {e}")
                return False
        else:
            logger.info(f"Simulating BigQuery Stream [archetype_drift]: {row}")
            return True
