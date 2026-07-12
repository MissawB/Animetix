"""The AniList ingestion must ASK for the facts the quiz needs, and a refetch must
enrich the works already on disk (the loop used to skip every known id, so new
query fields would never have reached the 2155 existing entries)."""

import importlib

ingest = importlib.import_module("pipeline.anime.ingest_anime")


def test_query_requests_the_facts_the_quiz_needs():
    for field in ("studios", "isAnimationStudio", "source", "episodes"):
        assert field in ingest.query, f"{field} missing from the AniList query"


def test_refetch_enriches_a_work_already_on_disk():
    known = {"id": 1, "title": {"romaji": "Cowboy Bebop"}, "popularity": 10}
    all_animes = [known]
    by_id = {1: known}

    added = ingest.merge_page(
        all_animes,
        by_id,
        [
            {
                "id": 1,
                "title": {"romaji": "Cowboy Bebop"},
                "popularity": 12,
                "source": "ORIGINAL",
            }
        ],
    )

    assert added == 0
    assert len(all_animes) == 1
    assert all_animes[0]["source"] == "ORIGINAL"  # the new field landed
    assert all_animes[0]["popularity"] == 12  # and the old one refreshed


def test_a_new_work_is_appended():
    all_animes, by_id = [], {}
    added = ingest.merge_page(
        all_animes, by_id, [{"id": 7, "title": {"romaji": "Monster"}}]
    )
    assert added == 1
    assert by_id[7]["title"]["romaji"] == "Monster"
