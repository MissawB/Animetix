from unittest.mock import MagicMock

import pytest
from core.domain.exceptions import CatalogNotFoundError
from core.domain.services.catalog_service import CatalogService


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def mock_sql_repository():
    return MagicMock()


@pytest.fixture
def catalog_service(mock_repository, mock_sql_repository):
    return CatalogService(
        repository=mock_repository, sql_repository=mock_sql_repository
    )


def test_get_catalog_sql_success(catalog_service, mock_sql_repository):
    mock_sql_repository.get_catalog_by_type.return_value = [
        {"id": 1, "title": "Naruto"}
    ]
    catalog = catalog_service.get_catalog("Anime")

    assert catalog["titles"] == ["Naruto"]
    assert "title_to_full_data" in catalog
    assert "autocomplete_json" in catalog


def test_get_catalog_fallback_to_file(
    catalog_service, mock_sql_repository, mock_repository
):
    mock_sql_repository.get_catalog_by_type.return_value = []
    mock_repository.load_catalog.return_value = {
        "db": [{"id": 2, "title": "One Piece"}],
        "lookup": [{"id": 2, "title": "One Piece"}],
    }

    catalog = catalog_service.get_catalog("Anime")
    assert catalog["titles"] == ["One Piece"]


def test_get_catalog_not_found(catalog_service, mock_sql_repository, mock_repository):
    mock_sql_repository.get_catalog_by_type.return_value = []
    mock_repository.load_catalog.return_value = None

    with pytest.raises(CatalogNotFoundError):
        catalog_service.get_catalog("Anime")


def test_caching_logic(catalog_service, mock_sql_repository):
    mock_sql_repository.get_catalog_by_type.return_value = [
        {"id": 1, "title": "Naruto"}
    ]

    # Premier appel
    catalog_service.get_catalog("Anime")
    assert mock_sql_repository.get_catalog_by_type.call_count == 1

    # Deuxième appel (doit utiliser le cache RAM interne)
    catalog_service.get_catalog("Anime")
    assert mock_sql_repository.get_catalog_by_type.call_count == 1
