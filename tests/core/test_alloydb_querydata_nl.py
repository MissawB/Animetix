from unittest.mock import MagicMock, patch

import pytest
from adapters.persistence.django_repository_adapter import (
    DjangoRepositoryAdapter,
    is_alloydb_nl_query_supported,
)
from adapters.persistence.pgvector_repository_adapter import PGVectorRepositoryAdapter
from adapters.persistence.unified_repository_adapter import UnifiedRepositoryAdapter
from core.utils.sql_guard import validate_sql_query
from django.conf import settings

# ==============================================================================
# 1. SQL GUARDRAIL SECURITY UTILITY TESTS
# ==============================================================================


def test_sql_guard_accepts_valid_queries():
    # Simple select
    assert validate_sql_query("SELECT * FROM animetix_mediaitem") is True
    # Select with WHERE clause
    assert (
        validate_sql_query(
            "SELECT title, release_year, rating FROM animetix_mediaitem WHERE rating > 8.5"
        )
        is True
    )
    # Case insensitivity and whitespace
    assert validate_sql_query("   select  title   from   animetix_mediaitem   ") is True
    # Allowing exactly one trailing semicolon
    assert validate_sql_query("SELECT * FROM animetix_mediaitem;") is True


def test_sql_guard_rejects_non_select():
    # No SQL or invalid types
    assert validate_sql_query("") is False
    assert validate_sql_query(None) is False
    # Mutating statements
    assert (
        validate_sql_query(
            "INSERT INTO animetix_mediaitem (title) VALUES ('Attack on Titan')"
        )
        is False
    )
    assert (
        validate_sql_query("UPDATE animetix_mediaitem SET rating = 9.0 WHERE id = 1")
        is False
    )
    assert validate_sql_query("DELETE FROM animetix_mediaitem WHERE id = 1") is False
    assert validate_sql_query("DROP TABLE animetix_mediaitem") is False
    assert validate_sql_query("TRUNCATE animetix_mediaitem") is False


def test_sql_guard_rejects_comments_and_chaining():
    # SQL Comments
    assert (
        validate_sql_query("SELECT * FROM animetix_mediaitem -- comment here") is False
    )
    assert (
        validate_sql_query("SELECT * FROM animetix_mediaitem /* block comment */")
        is False
    )
    # Multiple statements / Query chaining
    assert (
        validate_sql_query("SELECT * FROM animetix_mediaitem; SELECT * FROM auth_user")
        is False
    )
    assert (
        validate_sql_query(
            "SELECT * FROM animetix_mediaitem; DROP TABLE animetix_profile;"
        )
        is False
    )


def test_sql_guard_rejects_forbidden_tables():
    # Attempting to read other tables
    assert validate_sql_query("SELECT * FROM auth_user") is False
    assert validate_sql_query("SELECT * FROM animetix_profile") is False
    # Subquery referencing forbidden tables
    assert (
        validate_sql_query(
            "SELECT * FROM animetix_mediaitem JOIN auth_user ON animetix_mediaitem.id = auth_user.id"
        )
        is False
    )


def test_sql_guard_rejects_union_injection():
    # Union injection detection
    assert (
        validate_sql_query(
            "SELECT title FROM animetix_mediaitem UNION SELECT username FROM auth_user"
        )
        is False
    )


# ==============================================================================
# 2. ADAPTER TEXT-TO-SQL FLOW TESTS
# ==============================================================================


@patch("django.db.connection.vendor", "postgresql")
def test_is_alloydb_nl_query_supported_success():
    with patch("django.db.connection.cursor") as mock_cursor:
        # Cursor returns True for proname='get_sql' check
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (True,)

        import adapters.persistence.django_repository_adapter  # noqa: E402

        adapters.persistence.django_repository_adapter._alloydb_nl_supported = None

        assert is_alloydb_nl_query_supported() is True


@patch("django.db.connection.vendor", "sqlite")
def test_is_alloydb_nl_query_supported_sqlite_fails():
    import adapters.persistence.django_repository_adapter  # noqa: E402

    adapters.persistence.django_repository_adapter._alloydb_nl_supported = None
    assert is_alloydb_nl_query_supported() is False


@patch("django.db.connection.cursor")
@patch(
    "adapters.persistence.django_repository_adapter.is_alloydb_nl_query_supported",
    return_value=True,
)
@pytest.mark.django_db
def test_query_data_natural_language_native_flow(mock_supported, mock_cursor):
    # Set settings
    settings.ALLOYDB_NL_QUERY_ACTIVE = True

    mock_cursor_obj = mock_cursor.return_value.__enter__.return_value
    # First query (alloydb_ai_nl.get_sql) returns the generated SQL
    mock_cursor_obj.fetchone.return_value = (
        "SELECT title FROM animetix_mediaitem WHERE rating > 9.0;",
    )
    # Second query execution output mockup
    mock_cursor_obj.description = [("title",)]
    mock_cursor_obj.fetchall.return_value = [("Frieren",), ("Steins;Gate",)]

    adapter = DjangoRepositoryAdapter()
    results = adapter.query_data_natural_language("Show anime with rating above 9")

    assert len(results) == 2
    assert results[0]["title"] == "Frieren"
    assert results[1]["title"] == "Steins;Gate"

    # Assert native function was called with config and natural query
    calls = mock_cursor_obj.execute.call_args_list
    assert any("alloydb_ai_nl.get_sql" in call[0][0] for call in calls)


@patch("django.db.connection.cursor")
@patch(
    "adapters.persistence.django_repository_adapter.is_alloydb_nl_query_supported",
    return_value=False,
)
@pytest.mark.django_db
def test_query_data_natural_language_fallback_flow(mock_supported, mock_cursor):
    # Disable native query
    settings.ALLOYDB_NL_QUERY_ACTIVE = False

    # Mock LLMService
    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        "SELECT title, release_year FROM animetix_mediaitem WHERE release_year = 2024"
    )

    mock_cursor_obj = mock_cursor.return_value.__enter__.return_value
    mock_cursor_obj.description = [("title",), ("release_year",)]
    mock_cursor_obj.fetchall.return_value = [("Solo Leveling", 2024)]

    adapter = DjangoRepositoryAdapter()
    results = adapter.query_data_natural_language(
        "Show anime released in 2024", llm_service=mock_llm
    )

    assert len(results) == 1
    assert results[0]["title"] == "Solo Leveling"
    assert results[0]["release_year"] == 2024

    # Assert LLM was generated with specialized prompt
    mock_llm.generate.assert_called_once()
    prompt_arg = mock_llm.generate.call_args[0][0]
    assert "animetix_mediaitem" in prompt_arg

    # Assert executed SQL was the one generated by LLM
    mock_cursor_obj.execute.assert_called_with(
        "SELECT title, release_year FROM animetix_mediaitem WHERE release_year = 2024"
    )


@patch("django.db.connection.cursor")
@patch(
    "adapters.persistence.django_repository_adapter.is_alloydb_nl_query_supported",
    return_value=False,
)
@pytest.mark.django_db
def test_query_data_natural_language_blocked_by_guardrail(mock_supported, mock_cursor):
    settings.ALLOYDB_NL_QUERY_ACTIVE = False

    # Mock LLMService returning dangerous SQL injection attempt
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "SELECT * FROM auth_user;"

    adapter = DjangoRepositoryAdapter()
    results = adapter.query_data_natural_language(
        "Show all users", llm_service=mock_llm
    )

    # Should block execution and return empty list
    assert results == []

    # Cursor should not be executed with the malicious SQL
    mock_cursor_obj = mock_cursor.return_value.__enter__.return_value
    assert not any(
        "auth_user" in str(call) for call in mock_cursor_obj.execute.call_args_list
    )


def test_pgvector_adapter_query_data_nl_returns_empty():
    adapter = PGVectorRepositoryAdapter(project_root=".")
    assert adapter.query_data_natural_language("test query") == []


@patch(
    "adapters.persistence.django_repository_adapter.DjangoRepositoryAdapter.query_data_natural_language"
)
def test_unified_adapter_delegates_to_django(mock_query_nl):
    mock_query_nl.return_value = [{"title": "Frieren"}]

    adapter = UnifiedRepositoryAdapter(project_root=".")
    results = adapter.query_data_natural_language("test query", llm_service=MagicMock())

    assert results == [{"title": "Frieren"}]
    mock_query_nl.assert_called_once_with("test query", mock_query_nl.call_args[0][1])
