import json
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pipeline.games.build_emoji_sequences as build_emoji_sequences
import pipeline.games.filter_games as filter_games
import pipeline.games.ingest_games as ingest_games
import pipeline.games.vectorize_games as vectorize_games


def test_ingest_games_missing_env():
    with (
        patch.object(ingest_games, "CLIENT_ID", None),
        patch.object(ingest_games, "logger") as mock_logger,
    ):
        res = ingest_games.run_ingestion()
        assert res is False
        mock_logger.error.assert_called_with(
            "❌ Missing IGDB_CLIENT_ID or IGDB_CLIENT_SECRET in .env"
        )


def test_ingest_games_success():
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "twitch_token"}

    mock_igdb_resp = MagicMock()
    mock_igdb_resp.status_code = 200
    mock_igdb_resp.json.return_value = [
        {
            "id": 1,
            "name": "Game 1",
            "summary": "This is a summary description for game 1 that is long enough.",
            "genres": [{"name": "RPG"}],
            "themes": [{"name": "Fantasy"}],
            "platforms": [{"name": "PC"}],
            "total_rating": 85.0,
            "first_release_date": 1704067200,
            "cover": {"url": "//images.igdb.com/co/1.jpg"},
            "similar_games": [{"name": "Game 2"}],
        }
    ]

    with (
        patch.object(ingest_games, "CLIENT_ID", "id"),
        patch.object(ingest_games, "CLIENT_SECRET", "secret"),
        patch.object(
            ingest_games,
            "safe_http_request",
            side_effect=[mock_token_resp, mock_igdb_resp],
        ),
        patch("builtins.open", mock_open()) as mock_file,
        patch("os.path.exists", return_value=False),
        patch.object(ingest_games, "logger"),
    ):

        # Override sleep and run
        with patch("time.sleep"):
            res = ingest_games.run_ingestion()
            assert res is True
            mock_file.assert_called()


def test_filter_games():
    mock_raw_data = [
        {
            "id": 1,
            "title": "Game 1",
            "description": "This is a summary description for game 1 that is long enough.",
            "image": "http://img.jpg",
        },
        {
            "id": 2,
            "title": "Short desc",
            "description": "Too short",
            "image": "http://img.jpg",
        },
    ]

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_raw_data))),
        patch("json.dump") as mock_json_dump,
        patch.object(filter_games, "logger"),
    ):

        res = filter_games.run_filtering()
        assert res is True

        # Verify only 1 game remained
        written_data = mock_json_dump.call_args[0][0]
        assert len(written_data) == 1
        assert written_data[0]["id"] == 1


def test_vectorize_games():
    mock_clean_data = [
        {
            "id": 1,
            "title": "Game 1",
            "description": "This is a summary description for game 1 that is long enough.",
            "image": "http://img.jpg",
            "year": "2026",
        }
    ]

    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": []}

    mock_transformer = MagicMock()
    mock_transformer.encode.return_value = np.array([[0.1, 0.2]])

    def mock_exists(path):
        if path == vectorize_games.CLEAN_DB:
            return True
        return False

    with (
        patch("os.path.exists", mock_exists),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_clean_data))),
        patch("numpy.save"),
        patch("numpy.load", return_value=np.array([])),
        patch.object(vectorize_games, "vector_manager") as mock_vector_manager,
        patch.object(
            vectorize_games, "SentenceTransformer", return_value=mock_transformer
        ),
        patch.object(vectorize_games, "logger"),
    ):

        mock_vector_manager.get_collection.return_value = mock_collection

        res = vectorize_games.run_vectorization()
        assert res is True
        mock_vector_manager.add_to_collection.assert_called()


def test_build_emoji_sequences():
    mock_lexicon = {"sword": "⚔️", "dragon": "🐉"}

    mock_source_data = [
        {
            "id": 1,
            "title": "Dragon Sword Game",
            "description": "A game with dragon and sword combat.",
            "genres": ["Action"],
            "tags": ["fantasy"],
            "popularity": 100,
        }
    ]

    mock_transformer = MagicMock()
    # Dynamically size return value to match input items count to prevent IndexError
    mock_transformer.encode.side_effect = lambda inputs, *args, **kwargs: np.ones(
        (len(inputs), 2)
    )

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_lexicon))),
        patch("builtins.print"),
        patch.object(
            build_emoji_sequences, "SentenceTransformer", return_value=mock_transformer
        ),
    ):

        # Mock load from processed files
        def mock_read_text(self, *args, **kwargs):
            if "clean_root_animes.json" in str(self):
                return json.dumps(mock_source_data)
            elif "emoji_lexicon.json" in str(self):
                return json.dumps(mock_lexicon)
            return json.dumps([])

        with (
            patch("pathlib.Path.read_text", mock_read_text),
            patch("pathlib.Path.write_text") as mock_write,
        ):

            build_emoji_sequences.main()
            mock_write.assert_called()
