import pytest
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def mock_django_media_item():
    item = MagicMock()
    item.title = "One Piece"
    item.external_id = "21"
    item.media_type = "Anime"
    item.metadata = {}
    return item

@patch('src.pipeline.expert_scrapers.gemini_client')
def test_scraper_g_streaming(mock_gemini):
    from pipeline.expert_scrapers import ScraperG_Streaming
    
    # Mocking Gemini response with valid JSON
    mock_model_response = MagicMock()
    mock_model_response.text = """
    [
        {"platform": "Netflix", "has_vf": true, "has_vostfr": true, "status": "Abonnement"}
    ]
    """
    mock_gemini.models.generate_content.return_value = mock_model_response
    
    data = ScraperG_Streaming.get_french_licence_and_streaming("One Piece", "Anime")
    
    assert len(data) == 1
    assert data[0]["platform"] == "Netflix"
    assert data[0]["has_vf"] is True

@patch('requests.get')
def test_scraper_h_recs(mock_get):
    from pipeline.expert_scrapers import ScraperH_Recs
    
    # Mocking Jikan recommendations API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "entry": {"title": "Fairy Tail", "mal_id": 6702},
                "content": "Both are long shonens with guild/crew adventure vibes."
            }
        ]
    }
    mock_get.return_value = mock_response
    
    recs = ScraperH_Recs.get_human_recs("21", "Anime")
    
    assert len(recs) == 1
    assert recs[0]["recommended_title"] == "Fairy Tail"
    assert recs[0]["mal_id"] == 6702
    assert "guild/crew" in recs[0]["reason"]

@patch('src.pipeline.expert_scrapers.gemini_client')
def test_scraper_i_pilgrimage(mock_gemini):
    from pipeline.expert_scrapers import ScraperI_Pilgrimage
    
    # Mocking Gemini response with valid JSON
    mock_model_response = MagicMock()
    mock_model_response.text = """
    [
        {"location_name": "Sado Island", "city": "Niigata", "scene_description": "Inspired the gold mines lore."}
    ]
    """
    mock_gemini.models.generate_content.return_value = mock_model_response
    
    locations = ScraperI_Pilgrimage.get_pilgrimage_locations("One Piece", "Anime")
    
    assert len(locations) == 1
    assert locations[0]["location_name"] == "Sado Island"
    assert locations[0]["city"] == "Niigata"

@patch('src.pipeline.expert_scrapers.MediaItem')
@patch('src.pipeline.expert_scrapers.ScraperG_Streaming.get_french_licence_and_streaming')
@patch('src.pipeline.expert_scrapers.ScraperH_Recs.get_human_recs')
@patch('src.pipeline.expert_scrapers.ScraperI_Pilgrimage.get_pilgrimage_locations')
@patch('src.pipeline.expert_scrapers.update_json_metadata_field')
def test_run_tripartite_enrichment_flow(mock_update_json, mock_get_pilgrimage, mock_get_recs, mock_get_streaming, mock_media_item, mock_django_media_item):
    from pipeline.expert_scrapers import run_tripartite_enrichment
    
    # Mocking Django QuerySet
    mock_media_item.objects.filter.return_value.order_by.return_value = [mock_django_media_item]
    
    # Mock return values
    mock_get_streaming.return_value = [{"platform": "Netflix", "has_vf": True}]
    mock_get_recs.return_value = [{"recommended_title": "Hunter X Hunter", "reason": "Adventure."}]
    mock_get_pilgrimage.return_value = [{"location_name": "Landmark", "city": "Tokyo"}]
    
    # Run tripartite flow
    run_tripartite_enrichment(limit=1, dry_run=False)
    
    # Assertions
    assert "streaming_platforms" in mock_django_media_item.metadata
    assert mock_django_media_item.metadata["streaming_platforms"][0]["platform"] == "Netflix"
    assert mock_django_media_item.metadata["human_recommendations"][0]["recommended_title"] == "Hunter X Hunter"
    assert mock_django_media_item.metadata["real_locations_pilgrimage"][0]["location_name"] == "Landmark"
    
    mock_django_media_item.save.assert_called_once()
    assert mock_update_json.call_count == 3
