from unittest.mock import patch

import pytest
from animetix.models import ArchetypeDriftSnapshot, DuelRoom
from animetix.pubsub_service import PubSubPublisherService
from django.contrib.auth.models import User


def test_pubsub_service_local_mode_logs():
    service = PubSubPublisherService()
    service.is_prod = False

    with patch("animetix.pubsub_service.logger.info") as mock_log_info:
        res = service.publish_event(
            topic_name="animetix-events-topic",
            payload={"event_type": "test_event", "data": "hello"},
        )

    assert res is True
    mock_log_info.assert_called_once()
    log_msg = mock_log_info.call_args[0][0]
    assert "Simulating Pub/Sub Publish [animetix-events-topic]" in log_msg


@pytest.mark.django_db
def test_signals_trigger_pubsub_publish():
    user = User.objects.create_user(username="pubsub_tester", password="pwd")

    with patch(
        "animetix.pubsub_service.PubSubPublisherService.publish_event"
    ) as mock_publish:
        # Create drift snapshot
        ArchetypeDriftSnapshot.objects.create(
            user=user,
            archetype_id="Shonen",
            intensity=0.8,
            shonen_affinity=0.9,
            seinen_affinity=0.2,
            logic_consistency=0.75,
        )
        assert mock_publish.call_count == 1
        args, kwargs = mock_publish.call_args
        assert args[0] == "animetix-events-topic"
        assert args[1]["event_type"] == "archetype_drift_created"

    with patch(
        "animetix.pubsub_service.PubSubPublisherService.publish_event"
    ) as mock_publish:
        # Create finished DuelRoom
        DuelRoom.objects.create(
            room_code="WXYZ",
            player1=user,
            media_type="Anime",
            secret_title="Naruto",
            is_finished=True,
        )
        assert mock_publish.call_count == 1
        args, kwargs = mock_publish.call_args
        assert args[0] == "animetix-events-topic"
        assert args[1]["event_type"] == "duel_completed"
