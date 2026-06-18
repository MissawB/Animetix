import pytest
from unittest.mock import MagicMock
from core.domain.services.media_sync_service import MediaSyncService


@pytest.fixture
def mock_adapter():
    return MagicMock()


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def sync_service(mock_adapter, mock_repository):
    return MediaSyncService(sync_adapter=mock_adapter, repository=mock_repository)


def test_handle_media_update(sync_service, mock_adapter):
    item = {"id": "1", "title": "Naruto"}
    sync_service.handle_media_update("Anime", "1", item)
    mock_adapter.sync_to_graph_db.assert_called_with("Anime", "1", item)
    mock_adapter.sync_to_vector_db.assert_called_with("Anime", "1", item)
