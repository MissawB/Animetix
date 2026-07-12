"""The cleaned entry is the quiz's only source of truth for studio, source and
filiation questions — so those fields must survive the filter step."""

import importlib

filter_anime = importlib.import_module("pipeline.anime.filter_anime")

RAW = {
    "id": 101922,
    "idMal": 38000,
    "title": {
        "romaji": "Kimetsu no Yaiba",
        "english": "Demon Slayer",
        "native": "鬼滅の刃",
    },
    "description": "Tanjiro sets out. (Source: MAL)",
    "genres": ["Action", "Adventure"],
    "tags": [{"name": "Demons", "rank": 90}, {"name": "Noise", "rank": 20}],
    "popularity": 928335,
    "startDate": {"year": 2019},
    "coverImage": {"large": "https://img/kny.jpg"},
    "source": "MANGA",
    "episodes": 26,
    "studios": {
        "edges": [
            {"node": {"name": "ufotable", "isAnimationStudio": True}},
            {"node": {"name": "Aniplex", "isAnimationStudio": False}},
        ]
    },
    "relations": {
        "edges": [
            {
                "relationType": "SEQUEL",
                "node": {"id": 2, "title": {"romaji": "Mugen Train"}},
            },
            {
                "relationType": "ADAPTATION",
                "node": {"id": 3, "title": {"romaji": "KnY Manga"}},
            },
        ]
    },
    "recommendations": {
        "nodes": [
            {
                "rating": 300,
                "mediaRecommendation": {"title": {"romaji": "Jujutsu Kaisen"}},
            }
        ]
    },
}


def test_keeps_the_animation_studio_only():
    entry = filter_anime.build_clean_entry(RAW, micro_tags=[])
    assert entry["studios"] == ["ufotable"]


def test_keeps_source_and_episode_count():
    entry = filter_anime.build_clean_entry(RAW, micro_tags=[])
    assert entry["source"] == "MANGA"
    assert entry["episode_count"] == 26


def test_groups_relations_by_type():
    entry = filter_anime.build_clean_entry(RAW, micro_tags=[])
    assert entry["relations"]["SEQUEL"] == ["Mugen Train"]
    assert entry["relations"]["ADAPTATION"] == ["KnY Manga"]


def test_still_produces_the_fields_the_catalogue_already_relies_on():
    entry = filter_anime.build_clean_entry(RAW, micro_tags=["swordsmanship"])
    assert entry["title"] == "Kimetsu no Yaiba"
    assert entry["year"] == 2019
    assert entry["popularity"] == 928335
    assert "Demons" in entry["tags"]  # rank >= 70 kept
    assert "Noise" not in entry["tags"]  # rank < 70 dropped
    assert "swordsmanship" in entry["tags"]  # micro tags merged in
    assert entry["recommendations"] == {"Jujutsu Kaisen": 300}
    assert "(Source:" not in entry["description"]
