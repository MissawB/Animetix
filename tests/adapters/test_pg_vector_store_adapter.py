"""Behavior tests for ``PgVectorStoreAdapter``.

`get_collection_count` was added alongside the billing fix for image search
(CLIP): the availability guard calls it on every search request to decide
whether the target collection can possibly answer before Berrix is charged. We
replace the module-level ``vector_manager`` with a MagicMock so no real
pgvector/DB is touched, and clear the Django cache around each test (this
adapter caches the count for a short TTL -- see the module docstring in the
adapter itself).

`search_by_vector` is the READ path the visual-search endpoint now runs on. It
used to swallow every exception and return ``[]`` -- which the endpoint could
not tell apart from "the search ran and matched nothing". The user was charged,
saw "aucun résultat", and nothing anywhere said the query never ran. It must
raise instead: an empty list means "matched nothing", and only that.
"""

from unittest.mock import MagicMock, patch

import pytest
from adapters.persistence.pg_vector_store_adapter import PgVectorStoreAdapter
from core.domain.exceptions import InfrastructureError


@pytest.fixture(autouse=True)
def _clear_django_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def adapter():
    return PgVectorStoreAdapter()


def test_get_collection_count_returns_manager_count(adapter):
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.return_value = 12
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 12


def test_get_collection_count_zero_on_error(adapter):
    mock_manager = MagicMock()
    mock_manager.get_collection.side_effect = RuntimeError("boom")
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 0


def test_get_collection_count_is_cached(adapter):
    """Without a cache, `VisualIndexService.is_available()` (the per-target
    anti-charge guard) would add a COUNT(*) to every image-search request --
    this pins that it doesn't."""
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.return_value = 7
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 7
        assert adapter.get_collection_count("unified_clip_space") == 7
    mock_manager.get_collection.assert_called_once_with("unified_clip_space")


def test_get_collection_count_transient_failure_is_not_cached(adapter):
    """A `count() == 0` that actually means "the DB call blew up" must never
    be memoised as though it meant "the collection is empty" -- that would
    turn a transient pgvector hiccup into 60s of honest-sounding 503s. The
    very next call (still well within the TTL) must hit the database again."""
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.side_effect = [
        RuntimeError("transient pgvector hiccup"),
        5,
    ]
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.get_collection_count("unified_clip_space") == 0
        assert adapter.get_collection_count("unified_clip_space") == 5
    assert mock_manager.get_collection.return_value.count.call_count == 2


def test_get_collection_count_cache_read_failure_falls_back_to_live_count(adapter):
    """A Redis blip on `cache.get` must not 500 the caller -- it must degrade
    to a live COUNT, exactly as if the cache had simply missed."""
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.return_value = 11
    with (
        patch(
            "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
        ),
        patch("adapters.persistence.pg_vector_store_adapter.cache") as mock_cache,
    ):
        mock_cache.get.side_effect = RuntimeError("redis down")
        assert adapter.get_collection_count("unified_clip_space") == 11
    mock_manager.get_collection.assert_called_once_with("unified_clip_space")


def test_get_collection_count_cache_write_failure_still_returns_live_count(adapter):
    """A Redis blip on `cache.set` must not prevent the (correctly computed)
    live count from being returned to the caller."""
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.count.return_value = 9
    with (
        patch(
            "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
        ),
        patch("adapters.persistence.pg_vector_store_adapter.cache") as mock_cache,
    ):
        mock_cache.get.return_value = None
        mock_cache.set.side_effect = RuntimeError("redis down")
        assert adapter.get_collection_count("unified_clip_space") == 9


# --------------------------------------------------------------------------- #
# search_by_vector -- the read path. An empty list must mean "matched nothing".
# --------------------------------------------------------------------------- #
def _manager_returning(metadatas, ids):
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.query.return_value = {
        "metadatas": [metadatas],
        "ids": [ids],
    }
    return mock_manager


def test_search_by_vector_returns_metadata_with_the_id_attached(adapter):
    mock_manager = _manager_returning(
        [{"title": "Cowboy Bebop", "media_type": "Anime", "external_id": "1"}],
        ["Anime:1"],
    )
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        results = adapter.search_by_vector("unified_clip_space", [0.1, 0.2], limit=3)

    assert results == [
        {
            "title": "Cowboy Bebop",
            "media_type": "Anime",
            "external_id": "1",
            "id": "Anime:1",
        }
    ]


def test_search_by_vector_raises_instead_of_returning_an_empty_list_on_failure(adapter):
    """THE bug this test exists for: a transient pgvector failure used to be
    swallowed into `[]`. The endpoint turns `[]` into a 200 with no results --
    so the user paid Berrix, was told "nothing matched", and nothing anywhere
    recorded that the search never ran. A failed query must raise; the endpoint
    already turns an exception into a 500."""
    mock_manager = MagicMock()
    mock_manager.get_collection.return_value.query.side_effect = RuntimeError(
        "connexion pgvector perdue"
    )
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        with pytest.raises(InfrastructureError):
            adapter.search_by_vector("unified_clip_space", [0.1, 0.2])


def test_search_by_vector_raises_when_the_collection_itself_cannot_be_opened(adapter):
    """A missing/unreachable collection is likewise not the same fact as "the
    search ran and matched nothing"."""
    mock_manager = MagicMock()
    mock_manager.get_collection.side_effect = RuntimeError("collection introuvable")
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        with pytest.raises(InfrastructureError):
            adapter.search_by_vector("unified_clip_space", [0.1, 0.2])


def test_search_by_vector_still_returns_an_empty_list_when_nothing_matched(adapter):
    """The honest empty list survives: the query RAN, and matched nothing.
    That is the only thing `[]` is now allowed to mean."""
    mock_manager = _manager_returning([], [])
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager", mock_manager
    ):
        assert adapter.search_by_vector("unified_clip_space", [0.1, 0.2]) == []


# --------------------------------------------------------------------------- #
# The seam that actually broke: adapter <-> REAL vector_client wrapper.
#
# Every test above doubles `vector_manager`, so the adapter only ever saw a
# hand-written `query()` result -- always dict-shaped metadata. The real wrapper's
# raw-SQL branch handed back JSON *strings* (Django's postgres backend registers
# `loads=lambda x: x` for jsonb, so ANY raw cursor in this project gets a str),
# and `dict(meta)` in the adapter iterated the string's characters:
#     ValueError: dictionary update sequence element #0 has length 1; 2 is required
# Nothing in the suite crossed that seam, so nothing caught it. This does: the
# REAL PGVectorCollectionWrapper, with only the DB cursor faked -- in the shape
# the production database genuinely returns.
# --------------------------------------------------------------------------- #
def test_search_by_vector_over_the_real_wrapper_with_a_postgres_shaped_cursor(
    adapter, mocker
):
    import json

    import pipeline.vector_client as vc

    class _Cursor:
        def execute(self, sql, params=None):
            pass

        def fetchall(self):
            # Exactly what psycopg hands back for a jsonb column in this
            # project: a STRING, not a dict.
            return [
                (
                    "Anime:1",
                    json.dumps(
                        {
                            "title": "Cowboy Bebop",
                            "media_type": "Anime",
                            "external_id": "1",
                            "image": "http://img/anime",
                        }
                    ),
                    "",
                    0.02,
                )
            ]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    conn = MagicMock()
    conn.vendor = "postgresql"
    conn.cursor.return_value = _Cursor()
    mocker.patch.object(vc, "connection", conn)
    mocker.patch.object(vc, "is_alloydb_ai_supported", return_value=False)

    # The real manager/wrapper -- no double between the adapter and the SQL.
    mocker.patch.object(vc, "is_vertex_ai_supported", return_value=False)
    with patch(
        "adapters.persistence.pg_vector_store_adapter.vector_manager",
        vc.PGVectorManager(),
    ):
        results = adapter.search_by_vector("unified_clip_space", [0.1] * 512, limit=1)

    assert results == [
        {
            "title": "Cowboy Bebop",
            "media_type": "Anime",
            "external_id": "1",
            "image": "http://img/anime",
            "id": "Anime:1",
        }
    ]
