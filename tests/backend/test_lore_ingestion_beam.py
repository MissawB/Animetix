import pytest
from unittest.mock import patch, MagicMock
from backend.pipeline.mlops.lore_ingestion_beam import run_pipeline

class MockResponse:
    def __init__(self, content):
        self.content = content

@pytest.mark.django_db
def test_beam_pipeline_execution():
    test_input = [
        {"url": "https://onepiece.fandom.com/wiki/Luffy", "franchise": "one piece"}
    ]
    
    mock_html = b"<html><body><div id='mw-content-text'>Monkey D. Luffy is the main protagonist of One Piece. He ate the Devil Fruit.</div></body></html>"
    
    with patch("core.utils.security.safe_http_request", return_value=MockResponse(mock_html)):
        from animetix.containers import get_container
        container = get_container()
        repo = container.persistence.repository()
        
        with patch.object(repo.chroma, 'upsert_items') as mock_upsert:
            # Run in-memory using DirectRunner
            run_pipeline(
                argv=["--runner=DirectRunner"],
                test_input=test_input
            )
            
            # Assert elements were scraped, chunked, embedded and upserted
            assert mock_upsert.call_count == 1
            args, kwargs = mock_upsert.call_args
            collection_name, ids, embeddings, metadatas = args
            
            assert collection_name == "anime_thematic"
            assert len(ids) > 0
            assert "beam_lore_one piece" in ids[0]
            assert "Monkey D. Luffy" in metadatas[0]["description"]
            assert metadatas[0]["franchise"] == "one piece"
