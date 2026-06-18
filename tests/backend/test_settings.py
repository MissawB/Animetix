from django.conf import settings


def test_gcp_workflows_settings():
    assert hasattr(settings, "GCP_WORKFLOW_ID")
    assert settings.GCP_WORKFLOW_ID == "manga-voice-pipeline"
    assert hasattr(settings, "GCP_LOCATION")
    assert settings.GCP_LOCATION == "europe-west1"


def test_eventarc_settings():
    assert hasattr(settings, "EVENTARC_RECEIVER_URL")
    assert (
        settings.EVENTARC_RECEIVER_URL == "http://localhost:8000/api/events/gcs-upload/"
    )
