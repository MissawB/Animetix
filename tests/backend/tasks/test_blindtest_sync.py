import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from animetix.tasks.club_events import trigger_club_event

@pytest.mark.django_db
def test_trigger_club_event_sends_websocket_message():
    # Setup
    club_id = 1
    event_id = 10
    
    # Mock channel layer with AsyncMock for group_send
    mock_channel_layer = MagicMock()
    mock_channel_layer.group_send = AsyncMock()
    
    with patch('animetix.tasks.club_events.get_channel_layer', return_value=mock_channel_layer):
        # Execute
        trigger_club_event(club_id, event_id)
        
        # Verify
        mock_channel_layer.group_send.assert_called_once()
        args, _ = mock_channel_layer.group_send.call_args
        assert args[0] == f'club_{club_id}'
        assert args[1]['type'] == 'event_start'
        assert args[1]['event_id'] == event_id
