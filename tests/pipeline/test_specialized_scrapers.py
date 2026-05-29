import pytest
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def mock_django_media_item():
    item = MagicMock()
    item.title = "Bleach"
    item.external_id = "269"
    item.media_type = "Anime"
    item.metadata = {}
    item.alternative_titles = []
    return item

@patch('src.pipeline.specialized_scrapers.gemini_client')
@patch('requests.get')
def test_scraper_a_casting(mock_get, mock_gemini):
    from backend.pipeline.specialized_scrapers import ScraperA_Casting
    
    # Mocking Jikan characters API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "character": {"name": "Ichigo Kurosaki"},
                "role": "Main",
                "voice_actors": [
                    {"language": "Japanese", "person": {"name": "Masakazu Morita"}},
                    {"language": "French", "person": {"name": "Vincent de Bouard"}}
                ]
            }
        ]
    }
    mock_get.return_value = mock_response
    
    cast = ScraperA_Casting.scrape_casting("269", "Anime")
    
    assert len(cast) == 1
    assert cast[0]["character"] == "Ichigo Kurosaki"
    assert cast[0]["seiyuu_vo"] == "Masakazu Morita"
    assert cast[0]["doubleur_vf"] == "Vincent de Bouard"

@patch('requests.get')
def test_scraper_b_music(mock_get):
    from backend.pipeline.specialized_scrapers import ScraperB_Music
    
    # Mocking Jikan full details theme response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "theme": {
                "openings": ["*Asterisk by Orange Range"],
                "endings": ["Life is Like a Boat by Rie fu"]
            }
        }
    }
    mock_get.return_value = mock_response
    
    # Mock Open file to simulate no cached file
    with patch('os.path.exists', return_value=False):
        themes = ScraperB_Music.get_music_themes("269", "bleach_id")
        
        assert len(themes) == 2
        assert themes[0]["type"] == "Opening"
        assert themes[0]["song_title"] == "*Asterisk by Orange Range"
        assert themes[1]["type"] == "Ending"
        assert themes[1]["song_title"] == "Life is Like a Boat by Rie fu"

@patch('src.pipeline.specialized_scrapers.gemini_client')
def test_scraper_c_reviews(mock_gemini):
    from backend.pipeline.specialized_scrapers import ScraperC_Reviews
    
    # Mocking Gemini response with valid JSON
    mock_model_response = MagicMock()
    mock_model_response.text = """
    {
        "score_global_fr": "8.8/10",
        "consensus_fr": "Bleach est adoré en France pour sa bande son et ses combats cultes.",
        "reviews_sources": [
            {"site": "SensCritique", "note": "8.5/10", "critique": "Un shonen légendaire de la grande époque."}
        ]
    }
    """
    mock_gemini.models.generate_content.return_value = mock_model_response
    
    reviews = ScraperC_Reviews.synthesize_french_reviews("Bleach", "Anime")
    
    assert reviews.get("score_global_fr") == "8.8/10"
    assert "SensCritique" in reviews.get("reviews_sources")[0]["site"]

@patch('src.pipeline.specialized_scrapers.MediaItem')
@patch('src.pipeline.specialized_scrapers.ScraperA_Casting.scrape_casting')
@patch('src.pipeline.specialized_scrapers.ScraperB_Music.get_music_themes')
@patch('src.pipeline.specialized_scrapers.ScraperC_Reviews.synthesize_french_reviews')
@patch('src.pipeline.specialized_scrapers.update_json_metadata_field')
def test_run_tripartite_enrichment_flow(mock_update_json, mock_synthesize, mock_get_music, mock_scrape_casting, mock_media_item, mock_django_media_item):
    from backend.pipeline.specialized_scrapers import run_tripartite_enrichment
    
    # Mocking Django QuerySet
    mock_media_item.objects.filter.return_value.order_by.return_value = [mock_django_media_item]
    
    # Mock return values for scrapers
    mock_scrape_casting.return_value = [{"character": "Ichigo", "role": "Main", "seiyuu_vo": "Morita", "doubleur_vf": "de Bouard"}]
    mock_get_music.return_value = [{"type": "Opening", "song_title": "Asterisk"}]
    mock_synthesize.return_value = {"score_global_fr": "9.0/10"}
    
    # Run in production mode
    run_tripartite_enrichment(limit=1, dry_run=False)
    
    # Assertions
    assert "cast" in mock_django_media_item.metadata
    assert mock_django_media_item.metadata["cast"][0]["character"] == "Ichigo"
    assert mock_django_media_item.metadata["themes_musicaux"][0]["song_title"] == "Asterisk"
    assert mock_django_media_item.metadata["critiques_fr"]["score_global_fr"] == "9.0/10"
    
    mock_django_media_item.save.assert_called_once()
    assert mock_update_json.call_count == 3
