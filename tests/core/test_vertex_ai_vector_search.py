from unittest.mock import patch

import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_vertex_ai_detection_disabled():
    with override_settings(VERTEX_AI_VECTOR_SEARCH_ACTIVE=False):
        import pipeline.vector_client  # noqa: E402

        pipeline.vector_client._vertex_ai_supported = None
        from pipeline.vector_client import is_vertex_ai_supported  # noqa: E402

        assert is_vertex_ai_supported() is False


@pytest.mark.django_db
@patch("google.cloud.aiplatform.init")
def test_vertex_ai_detection_enabled_success(mock_init):
    with override_settings(
        VERTEX_AI_VECTOR_SEARCH_ACTIVE=True,
        VERTEX_AI_PROJECT_ID="test-project",
        VERTEX_AI_LOCATION="europe-west1",
    ):
        import pipeline.vector_client  # noqa: E402

        pipeline.vector_client._vertex_ai_supported = None
        from pipeline.vector_client import is_vertex_ai_supported  # noqa: E402

        assert is_vertex_ai_supported() is True
        mock_init.assert_called_once_with(
            project="test-project", location="europe-west1"
        )


@pytest.mark.django_db
def test_vertex_ai_fallback_to_pgvector():
    import pipeline.vector_client  # noqa: E402

    pipeline.vector_client._vertex_ai_supported = False
    from pipeline.vector_client import PGVectorManager  # noqa: E402

    manager = PGVectorManager()
    coll = manager.get_collection("test_fallback")
    assert coll.__class__.__name__ == "PGVectorCollectionWrapper"
