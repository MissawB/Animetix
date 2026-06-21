from core.domain.services.rag.hybrid_index import HybridSearchIndex


def _items():
    return [
        {
            "id": 1,
            "title": "Naruto",
            "description": "A young ninja named Naruto Uzumaki seeks recognition.",
            "genres": ["Action", "Adventure", "Shonen"],
        },
        {
            "id": 2,
            "title": "One Piece",
            "description": "Luffy the pirate captain searches for the legendary treasure.",
            "genres": ["Adventure", "Comedy"],
        },
        {
            "id": 3,
            "name": "Bleach",
            "clean_description": "Ichigo becomes a soul reaper to protect the living.",
        },
    ]


def test_not_initialized_returns_empty():
    idx = HybridSearchIndex()
    assert idx.is_initialized() is False
    assert idx.search("ninja") == []
    assert idx.search_with_scores("ninja") == []


def test_initialize_builds_matrix_and_chunks():
    idx = HybridSearchIndex()
    idx.initialize(_items(), media_type="anime")
    assert idx.is_initialized() is True
    assert len(idx.chunks) >= 3
    # every chunk maps back to a parent item
    assert all(c in idx.parent_child_map for c in idx.chunks)


def test_initialize_empty_items_stays_uninitialized():
    idx = HybridSearchIndex()
    idx.initialize([], media_type="anime")
    assert idx.is_initialized() is False


def test_search_finds_relevant_parent():
    idx = HybridSearchIndex()
    idx.initialize(_items(), media_type="anime")
    results = idx.search("Naruto Uzumaki ninja", limit=5)
    assert results
    assert results[0]["id"] == 1


def test_search_dedups_parents_by_id():
    # Two chunks from a long description of the same parent must yield one parent.
    long_desc = "Naruto trains hard. " * 20 + "He masters the rasengan technique. " * 20
    idx = HybridSearchIndex()
    idx.initialize(
        [{"id": 99, "title": "Naruto", "description": long_desc}],
        media_type="anime",
    )
    # ensure the description actually produced multiple chunks
    assert len(idx.chunks) > 1
    results = idx.search("rasengan technique naruto", limit=10)
    ids = [r["id"] for r in results]
    assert ids.count(99) == 1


def test_search_with_scores_returns_sorted_positive_scores():
    idx = HybridSearchIndex()
    idx.initialize(_items(), media_type="anime")
    scored = idx.search_with_scores("pirate treasure Luffy", limit=10)
    assert scored
    parent, score = scored[0]
    assert parent["id"] == 2
    assert score > 0
    # descending order
    score_values = [s for _, s in scored]
    assert score_values == sorted(score_values, reverse=True)


def test_search_irrelevant_query_returns_no_zero_score_hits():
    idx = HybridSearchIndex()
    idx.initialize(_items(), media_type="anime")
    # term absent from all docs -> all scores 0 -> filtered out
    results = idx.search("xyzzy quux nonexistentterm", limit=10)
    assert results == []


def test_context_header_includes_genres_and_is_cached():
    idx = HybridSearchIndex()
    item = {"title": "Naruto", "genres": ["Action", "Adventure", "Shonen"]}
    h1 = idx._generate_context_header(item, "anime")
    assert "Naruto" in h1
    assert "anime" in h1
    # only first 2 genres included
    assert "Action" in h1 and "Adventure" in h1
    assert "Shonen" not in h1
    # cached: same object returned on second call
    h2 = idx._generate_context_header(item, "anime")
    assert h1 == h2
    assert "anime:Naruto" in idx._context_headers


def test_chunk_text_splits_on_sentences_within_size():
    idx = HybridSearchIndex()
    text = "First sentence here. Second sentence here. Third sentence here."
    chunks = idx._chunk_text(text, size=25)
    assert len(chunks) > 1
    # reconstructed content preserved
    joined = " ".join(chunks)
    for word in ("First", "Second", "Third"):
        assert word in joined


def test_chunk_text_single_chunk_when_small():
    idx = HybridSearchIndex()
    chunks = idx._chunk_text("Short text.", size=300)
    assert chunks == ["Short text."]


# --- reciprocal_rank_fusion ---


def test_rrf_merges_and_ranks_by_combined_score():
    lexical = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    semantic = [{"id": "b"}, {"id": "a"}, {"id": "d"}]
    fused = HybridSearchIndex.reciprocal_rank_fusion(lexical, semantic, k=60)
    ids = [d["id"] for d in fused]
    # a (ranks 0 & 1) and b (ranks 1 & 0) appear in both -> outrank c/d (one list each)
    assert set(ids[:2]) == {"a", "b"}
    assert ids[0] == "a"  # a's combined score (0+1) slightly beats b's (1+0)
    assert set(ids) == {"a", "b", "c", "d"}


def test_rrf_uses_external_id_fallback_and_skips_missing_ids():
    lexical = [{"external_id": "x"}, {"title": "no-id"}]
    semantic = [{"id": "y"}]
    fused = HybridSearchIndex.reciprocal_rank_fusion(lexical, semantic)
    ids = [d.get("id") or d.get("external_id") for d in fused]
    assert "x" in ids
    assert "y" in ids
    # the doc with no id at all is dropped
    assert len(fused) == 2


def test_rrf_empty_inputs():
    assert HybridSearchIndex.reciprocal_rank_fusion([], []) == []
