import os
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_list_open_datasets(client):
    """Test that the open-data list endpoint returns available datasets."""
    url = reverse("open_dataset_list")
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "datasets" in data

    # Check that it returns datasets list (should have dpo_pairs and/or anonymized_logs if files exist)
    datasets = data["datasets"]
    for dataset in datasets:
        assert "id" in dataset
        assert "name" in dataset
        assert "description" in dataset
        assert "format" in dataset
        assert "size_bytes" in dataset
        assert "updated_at" in dataset


@pytest.mark.django_db
def test_download_dataset_success(client):
    """Test downloading a valid dataset."""
    url = reverse("open_dataset_download", kwargs={"dataset_id": "anonymized_logs"})
    response = client.get(url)

    # If the file exists, it should be 200 and return the file
    datasets_dir = os.path.join(settings.BASE_DIR, "data", "mlops", "datasets")
    file_path = os.path.join(datasets_dir, "gameplay_sessions.jsonl")

    if os.path.exists(file_path):
        assert response.status_code == 200
        assert response["Content-Type"] == "application/octet-stream"
        assert (
            'attachment; filename="gameplay_sessions.jsonl"'
            in response["Content-Disposition"]
        )
    else:
        assert response.status_code == 404


@pytest.mark.django_db
def test_download_dataset_not_found(client):
    """Test that requesting an invalid dataset ID returns 404."""
    url = reverse("open_dataset_download", kwargs={"dataset_id": "invalid_dataset_id"})
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
@patch("os.path.exists")
def test_download_dataset_missing_file_mocked(mock_exists, client):
    """Test that if the file is missing from disk, download view returns 404."""
    mock_exists.return_value = False

    url = reverse("open_dataset_download", kwargs={"dataset_id": "dpo_pairs"})
    response = client.get(url)
    assert response.status_code == 404
