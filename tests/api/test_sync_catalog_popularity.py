"""MediaItem.popularity was never written, so `order_by("-popularity")` — which the
World Boss pool, Akinetix and Quiz Who all rely on — ordered rows arbitrarily."""

import json

import pytest
from animetix.models import MediaItem
from django.core.management import call_command


@pytest.mark.django_db
def test_sync_writes_the_popularity_column(tmp_path, monkeypatch):
    from animetix.management.commands import sync_catalog

    # Inserted in reverse-popularity order on purpose: pre-fix, popularity stays
    # 0.0 for every row and SQLite ties break by insertion (rowid) order, so a
    # naive test with "Popular" inserted first would pass by accident even
    # without the fix. Insert "Niche" first so only a real popularity write
    # produces ["Popular", "Niche"].
    data = [
        {"idMal": 2, "title": "Niche", "popularity": 1200},
        {"idMal": 1, "title": "Popular", "popularity": 900000},
    ]
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    (processed / "clean_root_animes.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    monkeypatch.setattr(
        sync_catalog.os.path, "abspath", lambda _p: str(tmp_path), raising=False
    )

    call_command("sync_catalog")

    titles = list(
        MediaItem.objects.filter(media_type="Anime")
        .order_by("-popularity")
        .values_list("title", flat=True)
    )
    assert titles == ["Popular", "Niche"]


def test_popularity_of_handles_the_character_shape():
    from animetix.management.commands.sync_catalog import popularity_of

    assert popularity_of({"popularity": 928335}) == 928335.0
    assert popularity_of({"popularity": {"favourites": 40830, "rank": 5}}) == 40830.0
    assert popularity_of({}) == 0.0
