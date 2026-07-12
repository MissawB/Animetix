# tests/pipeline/test_kitsu_episodes.py
"""Kitsu is the substitute for plot data no other source structures. The two pure
transforms below are what the network layer feeds; they must never invent an
episode and never keep an empty one."""

import importlib

kitsu = importlib.import_module("pipeline.anime.fetch_kitsu_episodes")

MAPPING = {
    "data": [{"id": "9", "type": "mappings"}],
    "included": [
        {"id": "7442", "type": "anime", "attributes": {"canonicalTitle": "Kimetsu"}}
    ],
}

EPISODES = {
    "data": [
        {
            "attributes": {
                "number": 2,
                "canonicalTitle": "Trainer Sakonji",
                "synopsis": "Tanjiro meets.",
            }
        },
        {
            "attributes": {
                "number": 1,
                "canonicalTitle": "Cruelty",
                "synopsis": "The family dies.",
            }
        },
        {"attributes": {"number": 3, "canonicalTitle": None, "synopsis": None}},
    ]
}


def test_reads_the_kitsu_id_from_the_mapping():
    assert kitsu.kitsu_id_from_mapping(MAPPING) == "7442"


def test_returns_none_when_the_work_is_not_mapped():
    assert kitsu.kitsu_id_from_mapping({"data": [], "included": []}) is None


def test_episodes_are_ordered_and_empty_ones_dropped():
    episodes = kitsu.episodes_from_payload(EPISODES)

    assert [e["number"] for e in episodes] == [
        1,
        2,
    ]  # sorted, ep3 dropped (no title, no plot)
    assert episodes[0]["title"] == "Cruelty"
    assert episodes[0]["synopsis"] == "The family dies."


def test_an_episode_with_a_title_but_no_plot_is_kept():
    episodes = kitsu.episodes_from_payload(
        {
            "data": [
                {
                    "attributes": {
                        "number": 1,
                        "canonicalTitle": "Cruelty",
                        "synopsis": None,
                    }
                }
            ]
        }
    )
    assert episodes == [{"number": 1, "title": "Cruelty", "synopsis": ""}]
