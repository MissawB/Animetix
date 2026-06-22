from unittest.mock import patch

from django.core.management import call_command


@patch("animetix.management.commands.restore_brain_service.restore_brain_service")
def test_restore_command_success(mock_restore):
    mock_restore.return_value = (True, "restored-json")

    # Run command
    call_command("restore_brain_service", "--max-instances=5")

    mock_restore.assert_called_once_with(5)


@patch("animetix.management.commands.restore_brain_service.restore_brain_service")
def test_restore_command_defaults_to_three(mock_restore):
    mock_restore.return_value = (True, "restored-json")

    call_command("restore_brain_service")  # no --max-instances
    mock_restore.assert_called_once_with(3)
