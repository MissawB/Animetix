import pytest
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def mock_django_media_item():
    item = MagicMock()
    item.title = "Naruto"
    item.external_id = "20"
    item.media_type = "Anime"
    item.metadata = {}
    return item

@patch('src.pipeline.advanced_scrapers.gemini_client')
@patch('pipeline.advanced_scrapers.httpx.get')
def test_scraper_d_arcs(mock_get, mock_gemini):
    from pipeline.advanced_scrapers import ScraperD_Arcs
    
    # Mocking Jikan episodes list
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"mal_id": 1, "title": "Enter: Naruto Uzumaki!"},
            {"mal_id": 2, "title": "My Name is Konohamaru!"}
        ]
    }
    mock_get.return_value = mock_response
    
    # Mocking Gemini response with valid JSON
    mock_model_response = MagicMock()
    mock_model_response.text = """
    {
        "arcs": [{"arc_name": "Introduction Arc", "episode_range": "1-2"}],
        "fillers": []
    }
    """
    mock_gemini.models.generate_content.return_value = mock_model_response
    
    data = ScraperD_Arcs.get_arcs_and_fillers("20", "Naruto")
    
    assert "arcs" in data
    assert data["arcs"][0]["arc_name"] == "Introduction Arc"
    assert len(data["fillers"]) == 0

@patch('pipeline.advanced_scrapers.httpx.post')
def test_scraper_e_igdb(mock_post):
    from pipeline.advanced_scrapers import ScraperE_IGDB
    
    # 1. Mock OAuth token request
    mock_oauth_res = MagicMock()
    mock_oauth_res.status_code = 200
    mock_oauth_res.json.return_value = {"access_token": "mock_access_token_123"}
    
    # 2. Mock IGDB search games request
    mock_search_res = MagicMock()
    mock_search_res.status_code = 200
    mock_search_res.json.return_value = [
        {
            "name": "Naruto Shippuden: Ultimate Ninja Storm 4",
            "platforms": [{"name": "PlayStation 4"}, {"name": "PC"}],
            "total_rating": 89.456,
            "first_release_date": 1454544000 # 2016-02-04
        }
    ]
    
    # Set mock post behavior based on URL
    def side_effect(url, *args, **kwargs):
        if "oauth2" in url:
            return mock_oauth_res
        elif "games" in url:
            return mock_search_res
        return MagicMock()
        
    mock_post.side_effect = side_effect
    
    # Set env vars to ensure we don't hit simulation fallback
    with patch.dict('os.environ', {'IGDB_CLIENT_ID': 'id_123', 'IGDB_CLIENT_SECRET': 'sec_123'}):
        games = ScraperE_IGDB.search_games("Naruto")
        
        assert len(games) == 1
        assert games[0]["name"] == "Naruto Shippuden: Ultimate Ninja Storm 4"
        assert "PlayStation 4" in games[0]["platforms"]
        assert games[0]["rating"] == 89.5
        assert games[0]["release_date"] == "2016-02-04"

@patch('src.pipeline.advanced_scrapers.gemini_client')
def test_scraper_f_tropes(mock_gemini):
    from pipeline.advanced_scrapers import ScraperF_Tropes
    
    # Mocking Gemini response with valid JSON
    mock_model_response = MagicMock()
    mock_model_response.text = """
    [
        {"trope": "The Chosen One", "description": "Naruto est destiné à apporter la paix."}
    ]
    """
    mock_gemini.models.generate_content.return_value = mock_model_response
    
    tropes = ScraperF_Tropes.get_narrative_tropes("Naruto", "Anime")
    
    assert len(tropes) == 1
    assert tropes[0]["trope"] == "The Chosen One"
    assert "destiné" in tropes[0]["description"]

@patch('src.pipeline.advanced_scrapers.MediaItem')
@patch('src.pipeline.advanced_scrapers.ScraperD_Arcs.get_arcs_and_fillers')
@patch('src.pipeline.advanced_scrapers.ScraperE_IGDB.search_games')
@patch('src.pipeline.advanced_scrapers.ScraperF_Tropes.get_narrative_tropes')
@patch('src.pipeline.advanced_scrapers.update_json_metadata_field')
def test_run_tripartite_enrichment_flow(mock_update_json, mock_get_tropes, mock_search_games, mock_get_arcs, mock_media_item, mock_django_media_item):
    from pipeline.advanced_scrapers import run_tripartite_enrichment
    
    # Mocking Django QuerySet
    mock_media_item.objects.filter.return_value.order_by.return_value = [mock_django_media_item]
    
    # Mock return values
    mock_get_arcs.return_value = {"arcs": [{"arc_name": "Test Arc"}], "fillers": []}
    mock_search_games.return_value = [{"name": "Naruto Game", "platforms": ["PC"]}]
    mock_get_tropes.return_value = [{"trope": "Test Trope", "description": "Trope description."}]
    
    # Run tripartite flow
    run_tripartite_enrichment(limit=1, dry_run=False)
    
    # Assertions
    assert "narrative_arcs" in mock_django_media_item.metadata
    assert mock_django_media_item.metadata["narrative_arcs"]["arcs"][0]["arc_name"] == "Test Arc"
    assert mock_django_media_item.metadata["video_games"][0]["name"] == "Naruto Game"
    assert mock_django_media_item.metadata["narrative_tropes"][0]["trope"] == "Test Trope"
    
    mock_django_media_item.save.assert_called_once()
    assert mock_update_json.call_count == 3
