"""Behavior tests for PGVectorRepositoryAdapter.

The adapter delegates all vector work to ``self.manager`` (the module-level
``vector_manager``) and reads catalogs/latent-spaces from JSON files on disk.
We construct the adapter with a real (temp) ``project_root`` for the file paths
and replace ``adapter.manager`` with a MagicMock that returns crafted collection
results — so no real pgvector / pgvector / Django DB is touched.

Assertions target the REAL logic: the nearest-neighbor embedding round-trip,
the Matryoshka-sliced cosine similarity + cache write, catalog mapping /
caching, search query construction (alloydb vs local embedding path with
dimension padding/truncation), and every defensive ``except -> default`` branch.
"""

import json
import os
from unittest.mock import MagicMock

import numpy as np
import pytest
from adapters.persistence.pgvector_repository_adapter import (
    LocalSentenceTransformerEmbeddingFunction,
    PGVectorRepositoryAdapter,
)


@pytest.fixture
def adapter(tmp_path):
    a = PGVectorRepositoryAdapter(project_root=str(tmp_path))
    a.manager = MagicMock(name="vector_manager")
    return a


@pytest.fixture(autouse=True)
def _clear_django_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


# --- media-type -> collection-name resolution ---------------------------
#
# Bug: calculate_similarity/get_nearest_neighbors used to pass the media type
# ("Anime") straight through as the pgvector collection name instead of
# resolving it via ``coll_names`` (as load_catalog/search_media_items already
# do). The collection "Anime" never exists -> silent 0.0 similarity in prod
# for every guess. ``_resolve_collection`` centralizes the fix.


@pytest.mark.parametrize(
    "media_type, expected_collection",
    [
        ("Anime", "anime_thematic"),
        ("Manga", "manga_thematic"),
        ("Character", "character_vibe"),
        ("Movie", "movie_thematic"),
        ("Game", "game_thematic"),
        ("Actor", "actor_vibe"),
    ],
)
def test_resolve_collection_maps_every_media_type(
    adapter, media_type, expected_collection
):
    assert adapter._resolve_collection(media_type) == expected_collection


def test_resolve_collection_passes_through_unknown_names(adapter):
    # A caller that already passes a real collection name (or anything not a
    # known media-type key) must be left untouched.
    assert adapter._resolve_collection("anime_thematic") == "anime_thematic"
    assert adapter._resolve_collection("some_custom_collection") == (
        "some_custom_collection"
    )


def test_calculate_similarity_resolves_media_type_to_collection(adapter):
    vec = [1.0] * 300
    adapter.manager.get_collection.return_value.get.return_value = {
        "embeddings": [vec, vec]
    }

    score = adapter.calculate_similarity("Anime", "1", "2")

    assert score == pytest.approx(1.0)
    adapter.manager.get_collection.assert_called_once_with(name="anime_thematic")


def test_calculate_similarity_keeps_working_with_real_collection_name(adapter):
    vec = [1.0] * 300
    adapter.manager.get_collection.return_value.get.return_value = {
        "embeddings": [vec, vec]
    }

    score = adapter.calculate_similarity("anime_thematic", "1", "2")

    assert score == pytest.approx(1.0)
    adapter.manager.get_collection.assert_called_once_with(name="anime_thematic")


def test_get_nearest_neighbors_resolves_media_type_to_collection(adapter):
    coll = adapter.manager.get_collection.return_value
    coll.get.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
    coll.query.return_value = {"ids": [["7", "8"]]}

    out = adapter.get_nearest_neighbors("Anime", 5, n_results=3)

    adapter.manager.get_collection.assert_called_once_with(name="anime_thematic")
    assert out == {"ids": [["7", "8"]]}


def test_get_nearest_neighbors_keeps_working_with_real_collection_name(adapter):
    coll = adapter.manager.get_collection.return_value
    coll.get.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
    coll.query.return_value = {"ids": [["7", "8"]]}

    out = adapter.get_nearest_neighbors("anime_thematic", 5, n_results=3)

    adapter.manager.get_collection.assert_called_once_with(name="anime_thematic")
    assert out == {"ids": [["7", "8"]]}


# --- get_nearest_neighbors ----------------------------------------------


def test_get_nearest_neighbors_round_trips_embeddings(adapter):
    coll = adapter.manager.get_collection.return_value
    coll.get.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
    coll.query.return_value = {"ids": [["7", "8"]]}

    out = adapter.get_nearest_neighbors("anime_thematic", 5, n_results=3)

    # The fetched embedding is fed straight back into query with n_results.
    adapter.manager.get_collection.assert_called_once_with(name="anime_thematic")
    coll.get.assert_called_once_with(ids=["5"], include=["embeddings"])
    coll.query.assert_called_once_with(query_embeddings=[[0.1, 0.2, 0.3]], n_results=3)
    assert out == {"ids": [["7", "8"]]}


def test_get_nearest_neighbors_none_when_no_embeddings(adapter):
    adapter.manager.get_collection.return_value.get.return_value = {"embeddings": []}
    assert adapter.get_nearest_neighbors("c", "1") is None


def test_get_nearest_neighbors_swallows_exception(adapter):
    adapter.manager.get_collection.side_effect = RuntimeError("boom")
    assert adapter.get_nearest_neighbors("c", "1") is None


# --- calculate_similarity -----------------------------------------------


def test_calculate_similarity_matryoshka_slice_and_cache(adapter):
    from django.core.cache import cache

    # Two identical 300-dim vectors -> cosine similarity 1.0 (sliced to 256).
    vec = [1.0] * 300
    adapter.manager.get_collection.return_value.get.return_value = {
        "embeddings": [vec, vec]
    }

    score = adapter.calculate_similarity("character_vibe", "b", "a")

    assert score == pytest.approx(1.0)
    # Cache key is order-independent (min/max of the two ids).
    cache_key = "sim_character_vibe_a_b"
    assert cache.get(cache_key) == pytest.approx(1.0)


def test_calculate_similarity_uses_cached_value(adapter):
    from django.core.cache import cache

    cache.set("sim_coll_a_b", 0.42)
    score = adapter.calculate_similarity("coll", "a", "b")
    assert score == 0.42
    # A cache hit means the vector store is never consulted.
    adapter.manager.get_collection.assert_not_called()


def test_calculate_similarity_returns_zero_when_not_two_embeddings(adapter):
    adapter.manager.get_collection.return_value.get.return_value = {
        "embeddings": [[1.0]]
    }
    assert adapter.calculate_similarity("coll", "a", "b") == 0.0


def test_calculate_similarity_returns_zero_on_exception(adapter):
    adapter.manager.get_collection.side_effect = RuntimeError("down")
    assert adapter.calculate_similarity("coll", "a", "b") == 0.0


# --- load_catalog / get_media_item / get_catalog_by_type -----------------


def _write_catalog(tmp_path, rel, items):
    path = os.path.join(str(tmp_path), rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(json.dumps(items).encode("utf-8"))


def test_load_catalog_unknown_type_returns_none(adapter):
    assert adapter.load_catalog("Nope") is None


def test_load_catalog_builds_and_caches(adapter, tmp_path):
    _write_catalog(
        tmp_path,
        "data/processed/clean_root_animes.json",
        [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}],
    )
    adapter.manager.get_collection.return_value.get.return_value = {
        "metadatas": [{"id": 1}]
    }

    cat = adapter.load_catalog("Anime")

    assert cat["lookup"] == [{"id": 1}]
    assert cat["db"][0]["title"] == "A"
    assert set(cat["id_to_full_data"].keys()) == {"1", "2"}
    # Second call is served from the in-memory cache (no second file read /
    # collection call).
    adapter.manager.get_collection.reset_mock()
    cat2 = adapter.load_catalog("Anime")
    assert cat2 is cat
    adapter.manager.get_collection.assert_not_called()


def test_load_catalog_handles_collection_error(adapter, tmp_path):
    _write_catalog(tmp_path, "data/processed/clean_root_animes.json", [{"id": 9}])
    adapter.manager.get_collection.side_effect = RuntimeError("no coll")

    cat = adapter.load_catalog("Anime")
    # Falls back to empty lookup but still maps the db.
    assert cat["lookup"] == []
    assert "9" in cat["id_to_full_data"]


def test_load_catalog_returns_none_on_missing_file(adapter):
    # No file written -> open() raises -> caught -> None.
    assert adapter.load_catalog("Manga") is None


def test_get_media_item_and_catalog_by_type(adapter, tmp_path):
    _write_catalog(
        tmp_path,
        "data/processed/clean_root_games.json",
        [{"id": 10, "title": "G10"}, {"id": 11, "title": "G11"}],
    )
    adapter.manager.get_collection.return_value.get.return_value = {"metadatas": []}

    assert adapter.get_media_item("Game", 10)["title"] == "G10"
    assert adapter.get_media_item("Game", 999) is None
    assert len(adapter.get_catalog_by_type("Game", limit=1)) == 1


def test_get_media_item_none_when_catalog_missing(adapter):
    assert adapter.get_media_item("Anime", "1") is None
    assert adapter.get_catalog_by_type("Anime") == []


# --- upsert / delete / count / get_all_ids ------------------------------


def test_upsert_items_forwards_to_collection(adapter):
    coll = adapter.manager.get_collection.return_value
    adapter.upsert_items("col", ["1"], [[0.1]], [{"m": 1}], documents=["d"])
    coll.upsert.assert_called_once_with(
        ids=["1"], embeddings=[[0.1]], metadatas=[{"m": 1}], documents=["d"]
    )


def test_upsert_items_swallows_error(adapter):
    adapter.manager.get_collection.side_effect = RuntimeError("x")
    # Must not raise: the mass pipelines prefer to lose a batch over losing a run.
    adapter.upsert_items("col", ["1"], [[0.1]], [{}])


def test_upsert_items_raises_when_strict(adapter):
    """A caller that COUNTS what it wrote must be told when nothing landed.

    The upsert runs in a transaction: a failure rolled the whole batch back.
    Swallowing it there is how `build_visual_index` came to print "N vecteurs
    écrits" in green for vectors that do not exist.
    """
    adapter.manager.get_collection.side_effect = RuntimeError("dimension mismatch")

    with pytest.raises(RuntimeError):
        adapter.upsert_items("col", ["1"], [[0.1]], [{}], strict=True)


def test_delete_collection_forwards(adapter):
    adapter.delete_collection("col")
    adapter.manager.delete_collection.assert_called_once_with("col")


def test_delete_collection_swallows_error(adapter):
    adapter.manager.delete_collection.side_effect = RuntimeError("x")
    adapter.delete_collection("col")


def test_get_collection_count(adapter):
    adapter.manager.get_collection.return_value.count.return_value = 5
    assert adapter.get_collection_count("col") == 5


def test_get_collection_count_zero_on_error(adapter):
    adapter.manager.get_collection.side_effect = RuntimeError("x")
    assert adapter.get_collection_count("col") == 0


def test_get_collection_count_is_cached(adapter):
    """The billing-fix availability check (`VideoRAGService.is_available`)
    calls this on every search -- without a cache, that's a COUNT(*) per
    request. A second call within the TTL must not re-hit the manager."""
    adapter.manager.get_collection.return_value.count.return_value = 9
    assert adapter.get_collection_count("cached_col") == 9
    assert adapter.get_collection_count("cached_col") == 9
    adapter.manager.get_collection.assert_called_once_with("cached_col")


def test_get_collection_count_cache_is_per_collection(adapter):
    adapter.manager.get_collection.return_value.count.return_value = 3
    assert adapter.get_collection_count("col_a") == 3
    adapter.manager.get_collection.return_value.count.return_value = 0
    assert adapter.get_collection_count("col_b") == 0
    assert adapter.manager.get_collection.call_count == 2


def test_get_collection_count_transient_failure_is_not_cached(adapter):
    """A `count() == 0` that actually means "the DB call blew up" must never
    be memoised as though the collection were empty -- the very next call
    (still within the 60s TTL) must hit the database again."""
    adapter.manager.get_collection.return_value.count.side_effect = [
        RuntimeError("transient"),
        4,
    ]
    assert adapter.get_collection_count("col") == 0
    assert adapter.get_collection_count("col") == 4
    assert adapter.manager.get_collection.return_value.count.call_count == 2


def test_get_collection_count_cache_read_failure_falls_back_to_live_count(
    adapter, mocker
):
    """A Redis blip on `cache.get` must not 500 the caller -- it must degrade
    to a live COUNT."""
    adapter.manager.get_collection.return_value.count.return_value = 8
    mocker.patch(
        "adapters.persistence.pgvector_repository_adapter.cache.get",
        side_effect=RuntimeError("redis down"),
    )
    assert adapter.get_collection_count("col") == 8
    adapter.manager.get_collection.assert_called_once_with("col")


def test_get_collection_count_cache_write_failure_still_returns_live_count(
    adapter, mocker
):
    adapter.manager.get_collection.return_value.count.return_value = 6
    mocker.patch(
        "adapters.persistence.pgvector_repository_adapter.cache.get",
        return_value=None,
    )
    mocker.patch(
        "adapters.persistence.pgvector_repository_adapter.cache.set",
        side_effect=RuntimeError("redis down"),
    )
    assert adapter.get_collection_count("col") == 6


def test_upsert_items_invalidates_cached_count(adapter):
    """A fresh backfill must be immediately visible, not hidden behind a
    stale "empty" count for up to 60s."""
    from django.core.cache import cache

    cache.set("pgvra_collection_count_col", 0, timeout=60)
    adapter.upsert_items("col", ["1"], [[0.1]], [{"m": 1}])
    assert cache.get("pgvra_collection_count_col") is None

    adapter.manager.get_collection.return_value.count.return_value = 1
    assert adapter.get_collection_count("col") == 1


def test_upsert_items_invalidates_the_twin_read_side_cache_too(adapter):
    """MINOR: `PgVectorStoreAdapter`'s 503 "index not built" guard
    (`MediaSearchView.post`) reads `vsp_collection_count_*`, a DIFFERENT key
    from this adapter's own `pgvra_collection_count_*`. Before this fix, an
    upsert invalidated only its own key -- the guard could keep answering
    "index not built" for up to 60s after a build had already landed."""
    from django.core.cache import cache

    cache.set("vsp_collection_count_col", 0, timeout=60)
    adapter.upsert_items("col", ["1"], [[0.1]], [{"m": 1}])
    assert cache.get("vsp_collection_count_col") is None


def test_delete_collection_invalidates_cached_count(adapter):
    """An emptied collection must not stay billable (cached non-zero count)
    for up to 60s after the delete."""
    from django.core.cache import cache

    cache.set("pgvra_collection_count_col", 5, timeout=60)
    adapter.delete_collection("col")
    assert cache.get("pgvra_collection_count_col") is None


def test_delete_collection_invalidates_the_twin_read_side_cache_too(adapter):
    from django.core.cache import cache

    cache.set("vsp_collection_count_col", 5, timeout=60)
    adapter.delete_collection("col")
    assert cache.get("vsp_collection_count_col") is None


def test_get_all_ids(adapter):
    adapter.manager.get_all_ids.return_value = {"1", "2"}
    assert sorted(adapter.get_all_ids("col")) == ["1", "2"]


def test_get_all_ids_empty_on_error(adapter):
    adapter.manager.get_all_ids.side_effect = RuntimeError("x")
    assert adapter.get_all_ids("col") == []


def test_get_collection_delegates(adapter):
    sentinel = object()
    adapter.manager.get_collection.return_value = sentinel
    assert adapter.get_collection("col") is sentinel


# --- load_themes / load_covers / load_latent_space ----------------------


def test_load_themes_reads_file(adapter, tmp_path):
    _write_catalog(tmp_path, "data/processed/anime_themes.json", {"1": ["op"]})
    assert adapter.load_themes() == {"1": ["op"]}


def test_load_themes_empty_when_missing(adapter):
    assert adapter.load_themes() == {}


def test_load_covers_reads_file(adapter, tmp_path):
    _write_catalog(tmp_path, "data/processed/manga_covers.json", {"5": "url"})
    assert adapter.load_covers() == {"5": "url"}


def test_load_covers_empty_when_missing(adapter):
    assert adapter.load_covers() == {}


def test_load_latent_space_specific_file(adapter, tmp_path):
    path = os.path.join(
        str(tmp_path), "data", "artifacts", "latent_space_anime_visual_vibe.json"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"points": [1, 2]}, f)

    assert adapter.load_latent_space("Anime", "visual") == {"points": [1, 2]}


def test_load_latent_space_falls_back_to_generic(adapter, tmp_path):
    path = os.path.join(str(tmp_path), "data", "artifacts", "latent_space_3d.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"fallback": True}, f)
    # Unknown vibe -> resolved filename missing -> generic fallback file used.
    assert adapter.load_latent_space("character", "unknownvibe") == {"fallback": True}


def test_load_latent_space_none_when_nothing_on_disk(adapter):
    assert adapter.load_latent_space("manga", "scenario") is None


# --- manga covers: DB failure must be logged, not swallowed --------------
#
# Bug (audit dette 2026-07-19): the three MangaCover readers wrapped the DB
# path in `except Exception: pass` — a real DB outage silently degraded to
# the (possibly stale) manga_covers.json file with zero trace in the logs.
# A plain "not found" miss, however, is a normal state and must NOT warn.


def _write_covers_file(tmp_path):
    _write_catalog(
        tmp_path,
        "data/processed/manga_covers.json",
        {
            "5": {
                "title": "Berserk",
                "mangadex_id": "mdx-5",
                "covers": {"ja": "u"},
                "synonyms": [],
            }
        },
    )


def _broken_manga_cover(mocker, error=RuntimeError("db down")):
    fake = MagicMock(name="MangaCover")
    fake.objects.all.side_effect = error
    fake.objects.filter.side_effect = error
    mocker.patch("animetix.models.MangaCover", fake)
    return fake


def _spy_warning(mocker):
    # The "animetix" logger does not propagate to root (Django LOGGING), so
    # caplog never sees its records — spy the module logger instead.
    import adapters.persistence.pgvector_repository_adapter as pgvra

    return mocker.spy(pgvra.logger, "warning")


def test_get_manga_covers_metadata_logs_db_failure_then_falls_back(
    adapter, tmp_path, mocker
):
    _write_covers_file(tmp_path)
    _broken_manga_cover(mocker)
    warn = _spy_warning(mocker)

    out = adapter.get_manga_covers_metadata()

    assert [m["title"] for m in out] == ["Berserk"]  # file fallback still works
    assert warn.call_count == 1
    assert "MangaCover" in warn.call_args[0][0]


def test_get_manga_cover_by_id_logs_db_failure_then_falls_back(
    adapter, tmp_path, mocker
):
    _write_covers_file(tmp_path)
    _broken_manga_cover(mocker)
    warn = _spy_warning(mocker)

    out = adapter.get_manga_cover_by_id("5")

    assert out["mangadex_id"] == "mdx-5"
    assert warn.call_count == 1
    assert "MangaCover" in warn.call_args[0][0]


def test_get_manga_cover_by_id_plain_miss_does_not_warn(adapter, tmp_path, mocker):
    _write_covers_file(tmp_path)
    fake = MagicMock(name="MangaCover")
    fake.objects.filter.return_value.first.return_value = None  # DB up, row absent
    mocker.patch("animetix.models.MangaCover", fake)
    warn = _spy_warning(mocker)

    out = adapter.get_manga_cover_by_id("5")

    assert out["title"] == "Berserk"  # falls back to the file
    warn.assert_not_called()  # a miss is a normal state, not an incident


def test_get_manga_cover_by_title_logs_db_failure_then_falls_back(
    adapter, tmp_path, mocker
):
    _write_covers_file(tmp_path)
    _broken_manga_cover(mocker)
    warn = _spy_warning(mocker)

    out = adapter.get_manga_cover_by_title("Berserk")

    assert out["mangadex_id"] == "mdx-5"
    assert warn.call_count == 1
    assert "MangaCover" in warn.call_args[0][0]


# --- search_media_items -------------------------------------------------


def test_search_media_items_alloydb_path(adapter, mocker):
    mocker.patch("pipeline.vector_client.is_alloydb_ai_supported", return_value=True)
    coll = adapter.manager.get_collection.return_value
    coll.query.return_value = {
        "metadatas": [[{"title": "X"}]],
        "ids": [["42"]],
    }

    res = adapter.search_media_items("ninja", media_type="Anime", limit=3, offset=2)

    # AlloyDB path forwards query_texts directly (no manual embedding).
    coll.query.assert_called_once_with(query_texts=["ninja"], n_results=3, offset=2)
    assert res == [{"title": "X", "id": "42"}]


def test_search_media_items_local_embedding_truncates_dim(adapter, mocker):
    mocker.patch("pipeline.vector_client.is_alloydb_ai_supported", return_value=False)
    coll = adapter.manager.get_collection.return_value
    # Existing record has a 2-dim embedding -> expected_dim becomes 2.
    coll.get.return_value = {"embeddings": [[0.0, 0.0]]}
    coll.query.return_value = {"metadatas": [[{"t": 1}]], "ids": [["1"]]}
    # The embedding fn returns 4 dims -> must be truncated to 2.
    adapter._embedding_fn = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])

    res = adapter.search_media_items("q", media_type="Manga")

    sent = coll.query.call_args.kwargs["query_embeddings"][0]
    assert sent == [0.1, 0.2]  # truncated to expected_dim
    assert res == [{"t": 1, "id": "1"}]


def test_search_media_items_local_embedding_pads_dim(adapter, mocker):
    mocker.patch("pipeline.vector_client.is_alloydb_ai_supported", return_value=False)
    coll = adapter.manager.get_collection.return_value
    coll.get.return_value = {"embeddings": [[0.0, 0.0, 0.0, 0.0]]}  # dim 4
    coll.query.return_value = {"metadatas": [[]], "ids": [[]]}
    adapter._embedding_fn = MagicMock(return_value=[[0.5, 0.6]])  # dim 2 -> padded

    adapter.search_media_items("q", media_type="Anime")

    sent = coll.query.call_args.kwargs["query_embeddings"][0]
    assert sent == [0.5, 0.6, 0.0, 0.0]


def test_search_media_items_defaults_media_type_to_anime(adapter, mocker):
    mocker.patch("pipeline.vector_client.is_alloydb_ai_supported", return_value=True)
    coll = adapter.manager.get_collection.return_value
    coll.query.return_value = {"metadatas": [[]], "ids": [[]]}

    adapter.search_media_items("q")  # no media_type
    # Resolves to the "anime_thematic" collection.
    adapter.manager.get_collection.assert_called_with(name="anime_thematic")


def test_search_media_items_empty_on_error(adapter, mocker):
    mocker.patch("pipeline.vector_client.is_alloydb_ai_supported", return_value=True)
    adapter.manager.get_collection.side_effect = RuntimeError("down")
    assert adapter.search_media_items("q", media_type="Anime") == []


# --- pass-through / stub methods ----------------------------------------


def test_sync_latent_space_returns_count(adapter):
    assert adapter.sync_latent_space("Anime", "thematic", [{"a": 1}, {"b": 2}]) == 2


def test_stub_methods_return_defaults(adapter):
    assert adapter.get_creative_fusion(1) is None
    assert adapter.get_user_gameplay_history(1) == []
    assert adapter.get_user_creative_history(1) == []


# --- LocalSentenceTransformerEmbeddingFunction --------------------------


def test_embedding_function_tolist_path(mocker):
    fake_st = MagicMock()
    arr = np.array([[1.0, 2.0]])
    fake_st.return_value.encode.return_value = arr
    mocker.patch.dict(
        "sys.modules",
        {"sentence_transformers": MagicMock(SentenceTransformer=fake_st)},
    )
    fn = LocalSentenceTransformerEmbeddingFunction("m")
    assert fn(["hello"]) == [[1.0, 2.0]]


def test_embedding_function_list_fallback(mocker):
    fake_st = MagicMock()
    # encode returns a plain list of tuples (no .tolist()).
    fake_st.return_value.encode.return_value = [(1.0, 2.0), (3.0, 4.0)]
    mocker.patch.dict(
        "sys.modules",
        {"sentence_transformers": MagicMock(SentenceTransformer=fake_st)},
    )
    fn = LocalSentenceTransformerEmbeddingFunction("m")
    assert fn(["a", "b"]) == [[1.0, 2.0], [3.0, 4.0]]


def test_embedding_fn_property_is_lazy(tmp_path, mocker):
    fake_st = MagicMock()
    mocker.patch.dict(
        "sys.modules",
        {"sentence_transformers": MagicMock(SentenceTransformer=fake_st)},
    )
    a = PGVectorRepositoryAdapter(project_root=str(tmp_path))
    assert a._embedding_fn is None
    fn1 = a.embedding_fn
    fn2 = a.embedding_fn
    assert fn1 is fn2  # cached
