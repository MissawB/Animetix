import pytest
from django.core.management import call_command
from unittest.mock import patch

@patch('animetix.management.commands.restore_brain_service.restore_brain_service')
def test_restore_command_success(mock_restore):
    mock_restore.return_value = (True, "restored-json")
    
    # Run command
    call_command('restore_brain_service', '--max-instances=5')
    
    mock_restore.assert_called_once_with(5)
