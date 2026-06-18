from unittest.mock import ANY, patch

import pytest
from animetix.bigquery_service import BigQueryTelemetryService


def test_telemetry_service_local_mode_logs():
    # Enforce non-production
    service = BigQueryTelemetryService()
    service.is_prod = False
    service.client = None

    with patch("animetix.bigquery_service.logger.info") as mock_log_info:
        res = service.stream_interaction(
            user_id=42, media_item_id=101, interaction_type="duel_win", weight=2.0
        )

    assert res is True
    mock_log_info.assert_called_once()
    log_msg = mock_log_info.call_args[0][0]
    assert "Simulating BigQuery Stream [user_interactions]" in log_msg
    assert "media_item_id': 101" in log_msg


@pytest.mark.django_db
def test_signals_trigger_tasks():
    from animetix.models import ArchetypeDriftSnapshot, DuelRoom  # noqa: E402
    from django.contrib.auth.models import User  # noqa: E402

    user = User.objects.create_user(username="sig_tester", password="pwd")

    with patch("animetix.tasks_client.enqueue_task") as mock_enqueue:
        # Create drift snapshot
        ArchetypeDriftSnapshot.objects.create(
            user=user,
            archetype_id="Shonen",
            intensity=0.8,
            shonen_affinity=0.9,
            seinen_affinity=0.2,
            logic_consistency=0.75,
        )

        mock_enqueue.assert_any_call("ingest_drift_telemetry", ANY)

    with patch("animetix.tasks_client.enqueue_task") as mock_enqueue:
        # Create unfinished DuelRoom (should not trigger telemetry task)
        room = DuelRoom.objects.create(
            room_code="ABCD", player1=user, media_type="Anime", secret_title="Naruto"
        )
        assert mock_enqueue.call_count == 0

        # Mark finished
        room.is_finished = True
        room.save()
        mock_enqueue.assert_called_once_with("ingest_duel_telemetry", room.id)


@pytest.mark.django_db
def test_sync_recommendations_command():
    from animetix.models import MediaItem, UserRecommendation  # noqa: E402
    from django.contrib.auth.models import User  # noqa: E402
    from django.core.management import call_command  # noqa: E402

    user = User.objects.create_user(username="command_tester", password="pwd")
    media = MediaItem.objects.create(
        external_id="456", media_type="Anime", title="Naruto"
    )

    # Assert table starts empty
    assert UserRecommendation.objects.count() == 0

    # Call the Django management command
    call_command("sync_bigquery_recommendations")

    # Assert recommendations are generated and synced (fallback mock recommendations)
    assert UserRecommendation.objects.filter(user=user).exists()
    rec = UserRecommendation.objects.get(user=user, media_item=media)
    assert rec.rank == 1
    assert rec.score == 4.5
