import pytest
from unittest.mock import patch


class MockResponse:
    def __init__(self, content):
        self.content = content


@pytest.mark.django_db
def test_beam_pipeline_execution():
    test_input = [
        {"url": "https://onepiece.fandom.com/wiki/Luffy", "franchise": "one piece"}
    ]

    mock_html = b"<html><body><div id='mw-content-text'>Monkey D. Luffy is the main protagonist of One Piece. He ate the Devil Fruit.</div></body></html>"

    with patch(
        "core.utils.security.safe_http_request", return_value=MockResponse(mock_html)
    ):
        from animetix.containers import get_container  # noqa: E402

        container = get_container()
        repo = container.persistence.repository()

        # Mock embedding_fn to avoid loading SentenceTransformer model during tests
        repo.chroma._embedding_fn = lambda texts: [[0.1] * 384 for _ in texts]

        with patch.object(repo.chroma, "upsert_items") as mock_upsert:
            from backend.pipeline.mlops.lore_ingestion_beam import (  # noqa: E402
                ScrapeAndCleanDoFn,
                ChunkTextDoFn,
                GenerateEmbeddingsDoFn,
                WriteToVectorDBDoFn,
            )

            # Step 1: Scrape
            scraper = ScrapeAndCleanDoFn()
            scraped = list(scraper.process(test_input[0]))
            assert len(scraped) == 1

            # Step 2: Chunk
            chunker = ChunkTextDoFn()
            chunked = list(chunker.process(scraped[0]))
            assert len(chunked) == 1

            # Step 3: Embed
            embedder = GenerateEmbeddingsDoFn()
            embedder.setup()
            embedded = list(embedder.process(chunked[0]))
            assert len(embedded) == 1

            # Step 4: Write
            writer = WriteToVectorDBDoFn()
            writer.setup()
            list(writer.process(embedded[0]))

            # Assert elements were scraped, chunked, embedded and upserted
            assert mock_upsert.call_count == 1
            args, kwargs = mock_upsert.call_args
            collection_name, ids, embeddings, metadatas = args

            assert collection_name == "anime_thematic"
            assert len(ids) > 0
            assert "beam_lore_one piece" in ids[0]
            assert "Monkey D. Luffy" in metadatas[0]["description"]
            assert metadatas[0]["franchise"] == "one piece"


def test_dofn_parameter_propagation():
    from backend.pipeline.mlops.lore_ingestion_beam import (
        GenerateEmbeddingsDoFn,
        WriteToVectorDBDoFn,
    )  # noqa: E402

    # Test GenerateEmbeddingsDoFn
    embedder = GenerateEmbeddingsDoFn(
        database_url="postgresql://test_url", django_env="test_env"
    )
    assert embedder.database_url == "postgresql://test_url"
    assert embedder.django_env == "test_env"

    # Test WriteToVectorDBDoFn
    writer = WriteToVectorDBDoFn(
        database_url="postgresql://test_url", django_env="test_env"
    )
    assert writer.database_url == "postgresql://test_url"
    assert writer.django_env == "test_env"
