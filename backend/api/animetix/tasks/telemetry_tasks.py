from animetix_project.logging_config import get_logger
from animetix.tasks_registry import register_task
from animetix.bigquery_service import BigQueryTelemetryService
from animetix.models import DuelRoom, ArchetypeDriftSnapshot, MediaItem

logger = get_logger('animetix.' + __name__)

@register_task("ingest_duel_telemetry")
def ingest_duel_telemetry(room_id):
    try:
        room = DuelRoom.objects.get(id=room_id)
        if not room.is_finished:
            logger.info(f"Skipping telemetry for unfinished room: {room_id}")
            return {"status": "skipped", "reason": "room not finished"}
        
        # Look up MediaItem matching secret title
        media_item = MediaItem.objects.filter(title=room.secret_title, media_type=room.media_type).first()
        media_item_id = media_item.id if media_item else 0
        
        service = BigQueryTelemetryService()
        
        # Ingest for both players if they exist
        if room.player1:
            weight = 2.0 if room.winner == room.player1 else 1.0
            service.stream_interaction(
                user_id=room.player1.id,
                media_item_id=media_item_id,
                interaction_type="duel_win" if room.winner == room.player1 else "duel_play",
                weight=weight
            )
            
        if room.player2:
            weight = 2.0 if room.winner == room.player2 else 1.0
            service.stream_interaction(
                user_id=room.player2.id,
                media_item_id=media_item_id,
                interaction_type="duel_win" if room.winner == room.player2 else "duel_play",
                weight=weight
            )
            
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in ingest_duel_telemetry: {e}")
        return {"status": "error", "error": str(e)}

@register_task("ingest_drift_telemetry")
def ingest_drift_telemetry(snapshot_id):
    try:
        snapshot = ArchetypeDriftSnapshot.objects.get(id=snapshot_id)
        service = BigQueryTelemetryService()
        service.stream_drift(
            user_id=snapshot.user.id,
            archetype_id=snapshot.archetype_id,
            intensity=snapshot.intensity,
            shonen=snapshot.shonen_affinity,
            seinen=snapshot.seinen_affinity,
            logic=snapshot.logic_consistency
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in ingest_drift_telemetry: {e}")
        return {"status": "error", "error": str(e)}
