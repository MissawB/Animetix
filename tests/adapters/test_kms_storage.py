import pytest
from unittest.mock import MagicMock, patch
from django.core.files.base import ContentFile

@pytest.mark.django_db
def test_gcs_storage_kms_key_propagation(mocker):
    # Mock settings to have GS_DEFAULT_KMS_KEY_NAME and GS_OBJECT_PARAMETERS
    mock_kms_key = "projects/my-project/locations/europe-west1/keyRings/my-keyring/cryptoKeys/my-key"
    
    # We patch settings attributes directly
    mocker.patch("django.conf.settings.GS_DEFAULT_KMS_KEY_NAME", mock_kms_key, create=True)
    mocker.patch("django.conf.settings.GS_OBJECT_PARAMETERS", {"kms_key_name": mock_kms_key}, create=True)
    mocker.patch("django.conf.settings.GS_BUCKET_NAME", "my-test-bucket", create=True)

    # Mock google.cloud.storage.Client
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    
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
    
    # 1. Verify KMS key is loaded into GoogleCloudStorage instance options
    gcs_storage = GoogleCloudStorage(bucket_name="my-test-bucket")
    assert gcs_storage.object_parameters.get("kms_key_name") == mock_kms_key
    
    # 2. Save a dummy file and check that setattr(blob, 'kms_key_name', mock_kms_key) was executed
    file_name = "test_fusions/kms_test.txt"
    content = b"test-kms-content"
    
    mock_blob.name = file_name
    
    saved_path = gcs_storage.save(file_name, ContentFile(content))
    
    # Verify the path returned matches clean_name
    assert saved_path == file_name
    
    # Verify that kms_key_name attribute was set on the blob instance
    assert mock_blob.kms_key_name == mock_kms_key
    
    # Verify upload was called
    mock_blob.upload_from_file.assert_called_once()
