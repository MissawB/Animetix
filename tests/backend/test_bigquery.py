from unittest.mock import patch
from animetix.bigquery_service import BigQueryTelemetryService

def test_telemetry_service_local_mode_logs():
    # Enforce non-production
    service = BigQueryTelemetryService()
    service.is_prod = False
    service.client = None
    
    with patch("animetix.bigquery_service.logger.info") as mock_log_info:
        res = service.stream_interaction(
            user_id=42,
            media_item_id=101,
            interaction_type="duel_win",
            weight=2.0
        )
    
    assert res is True
    mock_log_info.assert_called_once()
    log_msg = mock_log_info.call_args[0][0]
    assert "Simulating BigQuery Stream [user_interactions]" in log_msg
    assert "media_item_id': 101" in log_msg

