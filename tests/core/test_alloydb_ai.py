from unittest.mock import patch

from pipeline.chroma_client import PGVectorCollectionWrapper, is_alloydb_ai_supported


@patch("django.db.connection.vendor", "postgresql")
def test_alloydb_ai_detection_success():
    with patch("django.db.connection.cursor") as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
            [0.1, 0.2],
        )

        import pipeline.chroma_client  # noqa: E402

        pipeline.chroma_client._alloydb_ai_supported = None

        assert is_alloydb_ai_supported() is True


@patch("django.db.connection.vendor", "postgresql")
def test_alloydb_ai_detection_failure():
    with patch("django.db.connection.cursor") as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.execute.side_effect = Exception(
            "No function"
        )

        import pipeline.chroma_client  # noqa: E402

        pipeline.chroma_client._alloydb_ai_supported = None

        assert is_alloydb_ai_supported() is False


@patch("django.db.connection.vendor", "postgresql")
@patch("pipeline.chroma_client.is_alloydb_ai_supported", return_value=True)
def test_alloydb_ai_query_structure(mock_detect):
    wrapper = PGVectorCollectionWrapper("test_coll")
    with patch("django.db.connection.cursor") as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.fetchall.return_value = []

        wrapper.query(query_texts=["hello"], n_results=5)

        calls = mock_cursor.return_value.__enter__.return_value.execute.call_args_list
        assert any("embedding(" in call[0][0] for call in calls)
