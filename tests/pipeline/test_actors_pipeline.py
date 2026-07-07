import json
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pipeline.actors.cross_media_mapping as cross_media_mapping
import pipeline.actors.filter_actors as filter_actors
import pipeline.actors.ingest_actors as ingest_actors
import pipeline.actors.vectorize_actors as vectorize_actors


def test_ingest_actors_missing_key():
    with patch.object(ingest_actors, "TMDB_API_KEY", None):
        res = ingest_actors.run_ingestion()
        assert res is False


def test_ingest_actors_success():
    mock_popular_resp = MagicMock()
    mock_popular_resp.status_code = 200
    mock_popular_resp.json.return_value = {
        "results": [
            {
                "id": 1,
                "name": "Actor A",
                "known_for_department": "Acting",
                "known_for": [{"title": "Movie X"}],
            }
        ]
    }

    mock_detail_resp = MagicMock()
    mock_detail_resp.status_code = 200
    mock_detail_resp.json.return_value = {
        "id": 1,
        "name": "Actor A",
        "popularity": 10.0,
        "biography": "This is a detailed biography of Actor A.",
        "profile_path": "/profile.jpg",
        "gender": 2,
    }

    with (
        patch.object(ingest_actors, "TMDB_API_KEY", "dummy_key"),
        patch.object(
            ingest_actors,
            "safe_http_request",
            side_effect=[mock_popular_resp, mock_detail_resp],
        ),
        patch("builtins.open", mock_open()) as mock_file,
        patch("os.path.exists", return_value=False),
        patch.object(ingest_actors, "logger"),
    ):

        with patch("time.sleep"):
            # Mock loop limit to 1 page for quick test execution
            def mock_fetch_tmdb_page(endpoint, page=1, params={}):
                if endpoint == "person/popular":
                    if page == 1:
                        return mock_popular_resp.json()
                    return None
                return mock_detail_resp.json()

            with patch.object(ingest_actors, "fetch_tmdb_page", mock_fetch_tmdb_page):
                res = ingest_actors.run_ingestion()
                assert res is True
                mock_file.assert_called()


def test_filter_actors():
    mock_raw_data = [
        {
            "id": 1,
            "name": "Actor A",
            "biography": "This is a biography that is longer than twenty characters.",
        },
        {"id": 2, "name": "Short Bio Actor", "biography": "Too short."},
    ]

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_raw_data))),
        patch("json.dump") as mock_json_dump,
        patch.object(filter_actors, "logger"),
    ):

        res = filter_actors.run_filtering()
        assert res is True

        # Verify writing filtered data (only 1 item should remain)
        written_data = mock_json_dump.call_args[0][0]
        assert len(written_data) == 1
        assert written_data[0]["id"] == 1


def test_vectorize_actors():
    mock_clean_data = [
        {
            "id": 1,
            "name": "Actor A",
            "biography": "This is a biography that is longer than twenty characters.",
            "popularity": 10.0,
            "image": "http://img.jpg",
        }
    ]

    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": []}

    mock_transformer = MagicMock()
    mock_transformer.encode.return_value = np.array([[0.1, 0.2]])

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_clean_data))),
        patch.object(vectorize_actors, "vector_manager") as mock_vector_manager,
        patch.object(
            vectorize_actors, "SentenceTransformer", return_value=mock_transformer
        ),
    ):

        mock_vector_manager.get_collection.return_value = mock_collection

        res = vectorize_actors.run_vectorization()
        assert res is True
        mock_vector_manager.add_to_collection.assert_called()


def test_cross_media_mapping_actors():
    mock_source_coll = MagicMock()
    mock_source_coll.get.return_value = {
        "ids": ["pers_1"],
        "embeddings": [[0.1, 0.2]],
        "metadatas": [{"title": "Character A"}],
    }

    mock_target_coll = MagicMock()
    mock_target_coll.query.return_value = {
        "metadatas": [[{"title": "Actor A", "image": "actor.jpg"}]],
        "distances": [[0.15]],
    }

    with (
        patch.object(cross_media_mapping, "vector_manager") as mock_vector_manager,
        patch("builtins.open", mock_open()) as mock_file,
        patch.object(cross_media_mapping, "logger"),
    ):

        mock_vector_manager.get_collection.side_effect = [
            mock_source_coll,
            mock_target_coll,
        ]

        res = cross_media_mapping.run_mapping()
        assert res is True
        mock_file.assert_called()
