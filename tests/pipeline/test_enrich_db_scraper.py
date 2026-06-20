from unittest.mock import MagicMock, patch

import pytest


# Configuration pour le test
@pytest.fixture
def mock_django_media_item():
    item = MagicMock()
    item.title = "Mock Anime"
    item.external_id = "12345"
    item.media_type = "Anime"
    item.synopsis_en = "An epic story of mock objects."
    item.synopsis_fr = ""
    item.metadata = {}
    item.alternative_titles = []
    return item


@patch("src.pipeline.enrich_db_scraper.gemini_client")
@patch("pipeline.enrich_db_scraper.safe_http_request")
def test_jikan_fetching_and_translation(mock_get, mock_gemini, mock_django_media_item):
    from pipeline.enrich_db_scraper import (
        fetch_jikan_details,  # noqa: E402
        translate_synopsis_via_gemini,
    )

    # 1. Test Jikan fetching
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"synopsis": "Jikan Synopsis"}}
    mock_get.return_value = mock_response

    data = fetch_jikan_details("12345", "Anime")
    assert data.get("synopsis") == "Jikan Synopsis"

    # 2. Test Gemini translation
    mock_model_response = MagicMock()
    mock_model_response.text = "Synopsis traduit"
    mock_gemini.models.generate_content.return_value = mock_model_response

    translation = translate_synopsis_via_gemini("Mock Anime", "English synopsis")
    assert translation == "Synopsis traduit"


@patch("src.pipeline.enrich_db_scraper.MediaItem")
@patch("src.pipeline.enrich_db_scraper.translate_synopsis_via_gemini")
@patch("src.pipeline.enrich_db_scraper.fetch_jikan_details")
@patch("src.pipeline.enrich_db_scraper.update_json_file")
def test_run_enrichment_flow(
    mock_update_json,
    mock_fetch_jikan,
    mock_translate,
    mock_media_item,
    mock_django_media_item,
):
    from pipeline.enrich_db_scraper import run_enrichment  # noqa: E402

    # Mocking Django querysets
    mock_qs = MagicMock()
    mock_qs.exclude.return_value.order_by.return_value.__getitem__.return_value = [
        mock_django_media_item
    ]
    mock_qs.count.return_value = 1
    mock_media_item.objects.filter.return_value.__or__.return_value = mock_qs

    # Mock return values for functions
    mock_translate.return_value = "Un récit épique d'objets simulés."
    mock_fetch_jikan.return_value = {
        "themes": [{"name": "Action"}],
        "background": "Background test",
        "titles": [{"title": "Alternative title"}],
        "recommendations": [],
    }

    # Run the enrichment flow
    run_enrichment(limit=1, dry_run=False)

    # Assertions
    assert mock_django_media_item.synopsis_fr == "Un récit épique d'objets simulés."
    assert mock_django_media_item.synopsis_en == "An epic story of mock objects."
    mock_django_media_item.save.assert_called_once()
    mock_update_json.assert_called_once()
