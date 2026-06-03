import pytest
from unittest.mock import MagicMock, patch

@patch('google.auth.default')
def test_custom_wrapper_generates_token(mock_auth, settings):
    # Setup mock credentials
    mock_credentials = MagicMock()
    mock_credentials.token = "mock-oauth2-access-token-123"
    mock_auth.return_value = (mock_credentials, "mock-project")
    
    # Import the custom DatabaseWrapper
    from animetix.db.postgresql.base import DatabaseWrapper
    
    settings.DJANGO_DB_USE_IAM = True
    
    wrapper = DatabaseWrapper(settings.DATABASES['default'])
    
    # Mock psycopg2 connection call
    with patch('django.db.backends.postgresql.base.DatabaseWrapper.get_new_connection') as mock_super_conn:
        conn_params = {'user': 'my-sa@project.iam', 'password': 'old'}
        wrapper.get_new_connection(conn_params)
        
        # Verify password got replaced by the refreshed token
        mock_credentials.refresh.assert_called_once()
        called_args, _ = mock_super_conn.call_args
        assert called_args[0]['password'] == "mock-oauth2-access-token-123"
