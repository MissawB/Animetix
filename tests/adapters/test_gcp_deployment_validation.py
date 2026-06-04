import os
import sys
import importlib
import pytest
from unittest.mock import MagicMock, patch
from django.core.management import call_command, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile

import google.auth
from google.auth.exceptions import DefaultCredentialsError

from animetix.db.postgresql.base import DatabaseWrapper

# --- 1. CLOUD SQL (UNIX SOCKET & IAM) ---

def test_postgresql_iam_auth_success(mocker):
    # Mock credentials returned by Google Auth library
    mock_creds = MagicMock()
    mock_creds.token = "fake-oauth2-token"
    mock_auth_default = mocker.patch("google.auth.default", return_value=(mock_creds, "mock-project"))
    mock_auth_request = mocker.patch("google.auth.transport.requests.Request", return_value=MagicMock())
    
    # Mock settings to activate IAM database connection
    mock_settings = MagicMock()
    mock_settings.DJANGO_DB_USE_IAM = True
    mocker.patch("animetix.db.postgresql.base.settings", mock_settings)
    
    # Patch super class get_new_connection to avoid actual postgres connection
    mock_super_connect = mocker.patch("django.db.backends.postgresql.base.DatabaseWrapper.get_new_connection")
    mock_super_connect.return_value = "mock-connection"
    
    # Instantiate BaseDatabaseWrapper wrapper with empty settings dict
    wrapper = DatabaseWrapper(settings_dict={})
    conn_params = {"host": "localhost", "user": "test-user", "password": "old-password"}
    
    res = wrapper.get_new_connection(conn_params)
    
    assert res == "mock-connection"
    scopes = ["https://www.googleapis.com/auth/sqlservice.admin", "https://www.googleapis.com/auth/cloud-platform"]
    mock_auth_default.assert_called_once_with(scopes=scopes)
    mock_creds.refresh.assert_called_once()
    
    # Verify OAuth2 token was injected into postgres password parameter
    called_params = mock_super_connect.call_args[0][0]
    assert called_params["password"] == "fake-oauth2-token"

def test_postgresql_iam_auth_failover(mocker):
    # Mock google.auth.default to fail, simulating lack of ADC or service account credential
    mocker.patch("google.auth.default", side_effect=DefaultCredentialsError("No credentials found"))
    
    mock_settings = MagicMock()
    mock_settings.DJANGO_DB_USE_IAM = True
    mocker.patch("animetix.db.postgresql.base.settings", mock_settings)
    
    wrapper = DatabaseWrapper(settings_dict={})
    conn_params = {"host": "localhost", "user": "test-user", "password": "old-password"}
    
    # Verify the exception cascades correctly to block connection and raise descriptive error
    with pytest.raises(DefaultCredentialsError):
        wrapper.get_new_connection(conn_params)


# --- 2. GOOGLE CLOUD STORAGE (GCS) ---

def test_gcs_storage_lifecycle_and_restart(mocker):
    # Mock google.cloud.storage.Client to verify default_storage interactions
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    
    mock_client.bucket.return_value = mock_bucket
    mock_client.get_bucket.return_value = mock_bucket
    
    # Local simulation database for storage blobs
    in_memory_blobs = {}
    
    def mock_blob_factory(name):
        mb = MagicMock()
        mb.name = name
        mb.upload_from_file = lambda file_obj, **kwargs: in_memory_blobs.__setitem__(name, file_obj.read())
        mb.download_to_file = lambda file_obj, **kwargs: file_obj.write(in_memory_blobs[name])
        mb.delete = lambda **kwargs: in_memory_blobs.pop(name, None)
        return mb
        
    # Mock bucket methods
    mock_bucket.get_blob.side_effect = lambda name, **kwargs: mock_blob_factory(name) if name in in_memory_blobs else None
    mock_bucket.blob.side_effect = mock_blob_factory
    mock_bucket.delete_blob.side_effect = lambda name, **kwargs: in_memory_blobs.pop(name, None)
    
    # Mock Blob constructor in gcloud.py to return our mock blob
    mocker.patch("storages.backends.gcloud.Blob", side_effect=lambda name, bucket, **kwargs: mock_blob_factory(name))
    
    # Mock the client property of GoogleCloudStorage backend
    mocker.patch(
        "storages.backends.gcloud.GoogleCloudStorage.client",
        new_callable=mocker.PropertyMock,
        return_value=mock_client
    )
    
    from storages.backends.gcloud import GoogleCloudStorage
    
    # 1. Instantiate Storage 1
    gcs_storage_1 = GoogleCloudStorage(bucket_name="animetix-test-bucket")
    
    # Write scenario image/text file
    file_name = "test_fusions/scen_1.txt"
    content = b"Fusion Scenario: Naruto and Luffy crossover"
    saved_path = gcs_storage_1.save(file_name, ContentFile(content))
    
    assert gcs_storage_1.exists(saved_path)
    assert in_memory_blobs[file_name] == content
    
    # 2. Simulate container restart / redeployment (Instantiate Storage 2 pointing to the same virtual bucket)
    gcs_storage_2 = GoogleCloudStorage(bucket_name="animetix-test-bucket")
    
    # Validate post-redeployment persistence
    assert gcs_storage_2.exists(saved_path)
    with gcs_storage_2.open(saved_path) as f:
        read_content = f.read()
    assert read_content == content
    
    # Clean up
    gcs_storage_2.delete(saved_path)
    assert not gcs_storage_2.exists(saved_path)

def test_gcs_storage_failover_api_error(mocker):
    from google.api_core.exceptions import GoogleAPICallError
    
    # Mock transient GCS API failure (like 503 error) to verify exception management
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    
    class MockGoogleAPIErr(GoogleAPICallError):
        pass
        
    mock_blob.upload_from_file.side_effect = MockGoogleAPIErr("503 Service Unavailable")
    mock_client.bucket.return_value = mock_bucket
    mock_client.get_bucket.return_value = mock_bucket
    mock_bucket.get_blob.return_value = None
    mock_bucket.blob.return_value = mock_blob
    
    mocker.patch("storages.backends.gcloud.Blob", return_value=mock_blob)
    
    mocker.patch(
        "storages.backends.gcloud.GoogleCloudStorage.client",
        new_callable=mocker.PropertyMock,
        return_value=mock_client
    )
    
    from storages.backends.gcloud import GoogleCloudStorage
    gcs_storage = GoogleCloudStorage(bucket_name="animetix-test-bucket")
    
    with pytest.raises(GoogleAPICallError):
        gcs_storage.save("test.txt", ContentFile(b"test"))


# --- 3. SECRET MANAGER (INJECTION VALIDATION) ---

def test_settings_production_requires_secrets():
    # Verify that in production mode, settings.py triggers ImproperlyConfigured if secrets are not injected
    try:
        with patch.dict(os.environ, {"DJANGO_ENV": "production", "DJANGO_SECRET_KEY": ""}):
            with pytest.raises(ImproperlyConfigured) as exc_info:
                importlib.reload(sys.modules['animetix_project.settings'])
            assert "DJANGO_SECRET_KEY environment variable is required in production" in str(exc_info.value)
    finally:
        # Crucial clean-up: restore test settings to prevent polluting downstream tests
        importlib.reload(sys.modules['animetix_project.settings'])


# --- 4. CLOUD RUN JOBS (SCHEDULER / JOB FAILOVER) ---

def test_run_scheduled_task_failover_non_zero_exit_code(mocker):
    # Mock a task execution to fail due to a database exception
    from django.db import DatabaseError
    mocker.patch(
        "animetix.tasks.meta_tasks.scheduled_dpo_optimization",
        side_effect=DatabaseError("Cloud SQL connection timed out")
    )
    
    # Cloud Run Jobs use command return codes to mark executions as failed.
    # Verify that the Django management command raises CommandError (which yields a non-zero exit code) on failure.
    with pytest.raises(CommandError) as exc_info:
        call_command('run_scheduled_task', 'dpo-optimization-daily')
    assert "execution failed" in str(exc_info.value)


# --- 5. CLOUD CDN & GCS CUSTOM ENDPOINT ---

def test_gcs_storage_custom_endpoint(mocker):
    # Verify that the custom endpoint settings are correctly bound to GoogleCloudStorage
    from storages.backends.gcloud import GoogleCloudStorage
    
    # Mock the client property to prevent actual GCS credentials initialization
    mocker.patch(
        "storages.backends.gcloud.GoogleCloudStorage.client",
        new_callable=mocker.PropertyMock,
        return_value=MagicMock()
    )
    
    gcs_storage = GoogleCloudStorage(
        bucket_name="animetix-test-bucket", 
        custom_endpoint="https://cdn.animetix.com"
    )
    assert gcs_storage.custom_endpoint == "https://cdn.animetix.com"

