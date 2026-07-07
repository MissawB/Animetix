import importlib
import json
from unittest.mock import MagicMock, mock_open, patch

# Dynamic imports using importlib since the filenames start with numbers
ingest_movies_mod = importlib.import_module("pipeline.movies.1_ingest_movies")
filter_movies_mod = importlib.import_module("pipeline.movies.3_filter_movies")
vectorize_movies_mod = importlib.import_module("pipeline.movies.5_vectorize_movies")
cross_media_mapping_mod = importlib.import_module(
    "pipeline.movies.6_cross_media_mapping"
)


def test_ingest_movies_missing_key():
    # Test when TMDB_API_KEY is not set
    with (
        patch.object(ingest_movies_mod, "TMDB_API_KEY", None),
        patch.object(ingest_movies_mod, "logger") as mock_logger,
    ):
        ingest_movies_mod.ingest_movies()
        mock_logger.error.assert_called_once_with(
            "❌ TMDB_API_KEY not found in .env file."
        )


def test_ingest_movies_success():
    # Test successful ingestion of movies
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": 101,
                "title": "Movie 1",
                "original_title": "Original Movie 1",
                "overview": "This is a very cool test movie description that is long enough.",
                "poster_path": "/path1.jpg",
                "release_date": "2026-01-01",
                "popularity": 8.5,
                "genre_ids": [28, 12],
            }
        ]
    }

    mock_details_response = MagicMock()
    mock_details_response.status_code = 200
    mock_details_response.json.return_value = {
        "genres": [{"name": "Action"}, {"name": "Adventure"}],
        "keywords": {"keywords": [{"name": "superhero"}]},
        "recommendations": {"results": [{"title": "Similar Movie"}]},
        "credits": {"cast": [{"name": "Actor One"}]},
    }

    with (
        patch.object(ingest_movies_mod, "TMDB_API_KEY", "dummy_key"),
        patch.object(
            ingest_movies_mod,
            "safe_http_request",
            side_effect=[mock_response, mock_details_response],
        ),
        patch("os.path.exists", return_value=False),
        patch("builtins.open", mock_open()) as mock_file,
        patch.object(ingest_movies_mod, "logger"),
    ):

        # Override fetch_tmdb_page for quick execution
        with patch.object(
            ingest_movies_mod, "fetch_tmdb_page", return_value=mock_response.json()
        ):
            ingest_movies_mod.ingest_movies()

            # Verify file was written
            mock_file.assert_called()


def test_filter_movies():
    # Input mock data
    mock_raw_data = [
        {
            "id": 101,
            "title": "Movie 1",
            "title_english": "Movie 1",
            "title_native": "Movie 1",
            "image": "/path1.jpg",
            "year": "2026",
            "media_type": "Movie",
            "popularity": 8.5,
            "description": "This description is long enough to pass the quality gate filter.",
        },
        {
            "id": 102,
            "title": "Short Description Movie",
            "title_english": "Short",
            "title_native": "Short",
            "image": "/path2.jpg",
            "year": "2026",
            "media_type": "Movie",
            "popularity": 5.0,
            "description": "Too short.",  # Should be filtered out (< 30 chars)
        },
    ]

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_raw_data))),
        patch("json.dump") as mock_json_dump,
        patch.object(filter_movies_mod, "logger"),
    ):

        filter_movies_mod.filter_movies()

        # Verify writing filtered data (only 1 item should remain)
        mock_json_dump.assert_called()
        written_data = mock_json_dump.call_args[0][0]
        assert len(written_data) == 1
        assert written_data[0]["id"] == 101


def test_vectorize_movies():
    mock_clean_data = [
        {
            "id": 101,
            "title": "Movie 1",
            "image": "/path1.jpg",
            "year": "2026",
            "media_type": "Movie",
            "popularity": 8.5,
            "description": "Test description of movie 1",
            "genres": ["Action"],
            "tags": ["sci-fi"],
            "recommendations": {"Sim": 90},
            "cast": ["Actor A"],
        }
    ]

    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": []}

    mock_transformer = MagicMock()
    mock_transformer.encode.return_value = [[0.1, 0.2]]

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_clean_data))),
        patch.object(vectorize_movies_mod, "vector_manager") as mock_vector_manager,
        patch.object(
            vectorize_movies_mod, "SentenceTransformer", return_value=mock_transformer
        ),
        patch.object(vectorize_movies_mod, "logger"),
    ):

        mock_vector_manager.get_collection.return_value = mock_collection

        vectorize_movies_mod.main()

        # Verify collection was queried and new items were added
        mock_vector_manager.get_collection.assert_called_with("movie_thematic")
        mock_vector_manager.add_to_collection.assert_called()


def test_cross_media_mapping():
    mock_source_coll = MagicMock()
    mock_source_coll.get.return_value = {
        "ids": ["1"],
        "embeddings": [[0.1, 0.2]],
        "metadatas": [{"title": "Anime 1"}],
    }

    mock_target_coll = MagicMock()
    mock_target_coll.query.return_value = {
        "metadatas": [[{"title": "Movie 1", "image": "path.jpg", "type": "Movie"}]],
        "distances": [[0.1]],
    }

    with (
        patch.object(cross_media_mapping_mod, "vector_manager") as mock_vector_manager,
        patch("builtins.open", mock_open()) as mock_file,
        patch.object(cross_media_mapping_mod, "logger") as mock_logger,
    ):

        mock_vector_manager.get_collection.side_effect = [
            mock_source_coll,
            mock_target_coll,
        ]

        cross_media_mapping_mod.create_mapping_v2(
            "anime_thematic", "movie_thematic", "artifacts/dummy_output.json"
        )

        print("LOGGER CALLS:", mock_logger.error.call_args_list)
        # Verify writing results
        mock_file.assert_called()
