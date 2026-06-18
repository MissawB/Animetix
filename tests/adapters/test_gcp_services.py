from unittest.mock import patch, MagicMock
from animetix.services import shutdown_brain_service, restore_brain_service


@patch("google.auth.default")
@patch("google.auth.transport.requests.AuthorizedSession.patch")
def test_shutdown_brain_service_success(mock_patch, mock_default):
    mock_default.return_value = (MagicMock(), "test-project")
    mock_patch.return_value = MagicMock(
        status_code=200, json=lambda: {"name": "animetix-brain"}
    )

    success, result = shutdown_brain_service()
    assert success is True
    assert result == {"name": "animetix-brain"}
    mock_patch.assert_called_once()


@patch("google.auth.default")
@patch("google.auth.transport.requests.AuthorizedSession.patch")
def test_restore_brain_service_success(mock_patch, mock_default):
    mock_default.return_value = (MagicMock(), "test-project")
    mock_patch.return_value = MagicMock(
        status_code=200, json=lambda: {"name": "animetix-brain"}
    )

    success, result = restore_brain_service(5)
    assert success is True
    assert (
        mock_patch.call_args[1]["json"]["template"]["scaling"]["maxInstanceCount"] == 5
    )
