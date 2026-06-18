import json
import uuid
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger("animetix.pubsub")


class PubSubPublisherService:
    def __init__(self):
        self.is_prod = getattr(settings, "IS_PRODUCTION", False)
        self.project_id = getattr(settings, "GCP_PROJECT_ID", "animetix-project")
        self.client = None
        if self.is_prod:
            try:
                from google.cloud import pubsub_v1  # noqa: E402

                self.client = pubsub_v1.PublisherClient()
            except Exception as e:
                logger.error(f"Failed to initialize Pub/Sub Publisher Client: {e}")

    def publish_event(self, topic_name: str, payload: dict) -> bool:
        """Publishes an event payload to a Pub/Sub topic."""
        payload_with_meta = {
            "event_id": payload.get("event_id", str(uuid.uuid4())),
            "timestamp": payload.get("timestamp", datetime.utcnow().isoformat()),
            **payload,
        }
        data = json.dumps(payload_with_meta).encode("utf-8")

        if self.client:
            try:
                topic_path = self.client.topic_path(self.project_id, topic_name)
                future = self.client.publish(topic_path, data)
                future.result(timeout=10)  # resolve future to detect exceptions
                logger.info(
                    f"Published event {payload_with_meta['event_id']} to topic {topic_name}"
                )
                return True
            except Exception as e:
                logger.error(f"Pub/Sub publish failed for topic {topic_name}: {e}")
                return False
        else:
            logger.info(
                f"Simulating Pub/Sub Publish [{topic_name}]: {payload_with_meta}"
            )
            return True
